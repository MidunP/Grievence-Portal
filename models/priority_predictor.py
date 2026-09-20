"""
Phase 5: Priority Prediction Module — ML-backed v2.
Trains a TF-IDF + Logistic Regression model on labelled dataset priority fields.
Combines the trained ML score with a rule-based safety-net for critical emergencies.
Includes language fairness evaluation across English, Hindi, and Tamil.
"""

import json
import pickle
from typing import Dict, List, Optional
from pathlib import Path

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, f1_score
    from sklearn.preprocessing import LabelEncoder
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.svm import LinearSVC
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from config import PRIORITY_LEVELS, URGENCY_KEYWORDS, DATA_DIR, MODELS_DIR


# ─────────────────────────────────────────────────────────────────────────────
# Hard-coded safety keywords (rule-based safety net — runs BEFORE ML)
# ─────────────────────────────────────────────────────────────────────────────
_CRITICAL_TRIGGERS = [
    "burst", "explode", "fire", "injury", "dead animal", "toxic", "bleeding",
    "shock", "electrocution", "collapsed", "flood", "fumes", "gas leak",
    "फट गया", "शॉर्ट सर्किट", "आग", "चोट", "मृत", "डूबना", "गैस रिसाव",
    "வெடித்து", "தீ", "காயம்", "சாய்ந்து", "உடைந்து", "மூழ்கி", "கசிவு"
]

_HIGH_TRIGGERS = [
    "no water", "12 hours", "8 hours", "overflowing", "choked", "low voltage",
    "no power", "stench", "toxic smell", "sewage",
    "पानी नहीं", "12 घंटे", "8 घंटे", "बिजली कट", "गंदगी", "नाला ओवरफ्लो",
    "நீர் விநியோகம்", "12 மணி நேரமாக", "மின்வெட்டு", "சாக்கடை"
]


class PriorityPredictor:
    """
    Hybrid Priority Predictor:
      1. Rule-based safety net  → forced Critical/High if triggers found
      2. ML model (TF-IDF + LR) → predicts Critical/High/Medium/Low from text
      3. Category default        → fallback for ambiguous cases
    """

    def __init__(self):
        self.priority_levels = PRIORITY_LEVELS
        self.is_trained = False

        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 4),
                max_features=10_000,
                sublinear_tf=True,
                min_df=1,
            )
            self.model = CalibratedClassifierCV(
                LinearSVC(class_weight="balanced", max_iter=2000, C=0.8),
                cv=3,
                method="isotonic",
            )
        else:
            self.vectorizer = None
            self.model = None

    # ── Training ──────────────────────────────────────────────────────────
    def train(self, train_data: List[Dict]) -> Dict:
        """Train ML priority model from dataset labels."""
        if not SKLEARN_AVAILABLE:
            self.is_trained = False
            return {"status": "sklearn_unavailable", "trained": False}

        X = [item["text"] for item in train_data]
        y = [item["priority"] for item in train_data]

        # Only keep samples that have explicit priority labels
        valid = [(xi, yi) for xi, yi in zip(X, y) if yi in PRIORITY_LEVELS]
        if len(valid) < 10:
            self.is_trained = False
            return {"status": "insufficient_data", "trained": False}

        X_v, y_v = zip(*valid)
        X_feat = self.vectorizer.fit_transform(X_v)
        self.model.fit(X_feat, y_v)
        y_pred = self.model.predict(X_feat)
        train_f1 = f1_score(y_v, y_pred, average="macro", zero_division=0)
        self.is_trained = True
        print(f"  [Priority]   Train macro-F1: {train_f1:.4f}  (n={len(X_v)})")
        return {"status": "success", "train_macro_f1": round(float(train_f1), 4), "trained": True}

    def evaluate(self, test_data: List[Dict]) -> Dict:
        """Evaluate ML model on test set."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return {"status": "not_trained"}
        X = [item["text"] for item in test_data]
        y = [item["priority"] for item in test_data]
        valid = [(xi, yi) for xi, yi in zip(X, y) if yi in PRIORITY_LEVELS]
        if not valid:
            return {"status": "no_valid_samples"}
        X_v, y_v = zip(*valid)
        X_feat = self.vectorizer.transform(X_v)
        y_pred = self.model.predict(X_feat)
        return {
            "overall_macro_f1": round(float(f1_score(y_v, y_pred, average="macro", zero_division=0)), 4),
            "report": classification_report(y_v, y_pred, output_dict=True, zero_division=0),
        }

    def save(self, file_path: Path = None):
        if file_path is None:
            file_path = MODELS_DIR / "priority_predictor.pkl"
        with open(file_path, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "model": self.model}, f, protocol=4)
        print(f"  [Priority]   Saved → {file_path}")

    def load(self, file_path: Path = None) -> bool:
        if file_path is None:
            file_path = MODELS_DIR / "priority_predictor.pkl"
        if not file_path.exists():
            return False
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.model = data["model"]
            self.is_trained = True
            return True
        except Exception as e:
            print(f"  [Priority]   Load failed: {e}")
            return False

    # ── Inference ─────────────────────────────────────────────────────────
    def extract_urgency_score(self, text: str, language: str) -> float:
        text_lower = text.lower()
        keywords = (
            URGENCY_KEYWORDS.get(language, [])
            + URGENCY_KEYWORDS["en"]
            + URGENCY_KEYWORDS["hi"]
            + URGENCY_KEYWORDS["ta"]
        )
        return float(sum(1 for kw in set(keywords) if kw in text_lower))

    def _rule_based_priority(self, text: str, language: str, category: str, days_open: int) -> Optional[str]:
        """Returns a forced priority string if a critical/high trigger fires, else None."""
        text_lower = text.lower()
        urgency_hits = self.extract_urgency_score(text, language)

        if any(t in text_lower for t in _CRITICAL_TRIGGERS) or urgency_hits >= 2:
            return "Critical"
        if any(t in text_lower for t in _HIGH_TRIGGERS) or urgency_hits >= 1 or days_open > 5:
            return "High"
        return None

    def predict_priority(self, text: str, language: str, category: str, days_open: int = 0) -> Dict:
        """
        Predict priority using:
          1. Rule-based safety net (overrides everything for Critical/High triggers)
          2. ML model prediction (if trained)
          3. Category-based default (final fallback)
        """
        # Step 1: safety-net rules
        forced = self._rule_based_priority(text, language, category, days_open)

        if forced is not None:
            reason = "Triggered emergency keyword or high urgency count (rule-based safety net)"
            priority = forced
            confidence = 0.95 if forced == "Critical" else 0.88

            return {
                "priority": priority,
                "confidence": confidence,
                "reason": reason,
                "urgency_matches": int(self.extract_urgency_score(text, language)),
                "days_open": days_open,
                "method": "rule",
            }

        # Step 2: ML model
        if self.is_trained and SKLEARN_AVAILABLE:
            X_feat = self.vectorizer.transform([text])
            probs = self.model.predict_proba(X_feat)[0]
            top_idx = int(np.argmax(probs))
            priority = self.model.classes_[top_idx]
            confidence = float(probs[top_idx])
            return {
                "priority": priority,
                "confidence": round(confidence, 4),
                "reason": f"ML model prediction (confidence {confidence:.2%})",
                "urgency_matches": int(self.extract_urgency_score(text, language)),
                "days_open": days_open,
                "method": "ml",
            }

        # Step 3: category default
        if category in ["Water Supply & Quality", "Electricity & Power Cut"]:
            priority, confidence = "Medium", 0.75
        else:
            priority, confidence = "Low", 0.70

        return {
            "priority": priority,
            "confidence": confidence,
            "reason": "Category-based default priority (no ML model available)",
            "urgency_matches": int(self.extract_urgency_score(text, language)),
            "days_open": days_open,
            "method": "default",
        }

    # ── Fairness ──────────────────────────────────────────────────────────
    def audit_fairness(self, test_data: List[Dict]) -> Dict:
        """Evaluate priority distribution across languages for bias detection."""
        bias_report: Dict[str, Dict] = {}
        for lang in ["en", "hi", "ta"]:
            samples = [item for item in test_data if item["language"] == lang]
            if not samples:
                continue
            dist = {p: 0 for p in PRIORITY_LEVELS}
            for item in samples:
                res = self.predict_priority(
                    item["text"], item["language"], item["category"], item.get("days_open", 0)
                )
                dist[res["priority"]] += 1
            total = len(samples)
            dist_pct = {k: round(v / total, 4) for k, v in dist.items()}
            high_ratio = round((dist["Critical"] + dist["High"]) / total, 4)
            bias_report[lang] = {
                "total_samples": total,
                "priority_distribution_pct": dist_pct,
                "high_priority_ratio": high_ratio,
            }

        ratios = [v["high_priority_ratio"] for v in bias_report.values()]
        max_disparity = round(max(ratios) - min(ratios), 4) if len(ratios) >= 2 else 0.0

        return {
            "language_fairness_report": bias_report,
            "max_disparity_score": max_disparity,
            "is_fair": max_disparity < 0.15,
        }


if __name__ == "__main__":
    import json
    predictor = PriorityPredictor()

    with open(DATA_DIR / "train.json", "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(DATA_DIR / "test.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)

    predictor.train(train_data)
    predictor.save()
    eval_res = predictor.evaluate(test_data)
    print("Priority Model Evaluation:")
    print(json.dumps(eval_res, indent=2))
    fairness = predictor.audit_fairness(test_data)
    print("\nFairness Audit:")
    print(json.dumps(fairness, indent=2))
