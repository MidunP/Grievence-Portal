"""
Phase 3: Multilingual Complaint Classifier — Enhanced Ensemble v2.
Implements a stacked ensemble (TF-IDF word + char n-gram features → Logistic Regression,
LinearSVC, SGDClassifier soft-voting) with language-aware feature engineering.
Falls back to Pure-Python Multinomial Naive Bayes when scikit-learn is unavailable.
"""

import json
import pickle
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict, Counter

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression, SGDClassifier
    from sklearn.svm import LinearSVC
    from sklearn.pipeline import Pipeline, FeatureUnion
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.ensemble import VotingClassifier
    from sklearn.metrics import classification_report, f1_score
    from sklearn.preprocessing import LabelEncoder
    from scipy.sparse import hstack
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from config import CATEGORIES, MODELS_DIR, DATA_DIR


# ─────────────────────────────────────────────────────────────────────────────
# Pure-Python fallback (no scikit-learn)
# ─────────────────────────────────────────────────────────────────────────────
class PurePythonNaiveBayes:
    """Lightweight Multinomial Naïve Bayes Classifier with Laplace smoothing."""

    def __init__(self):
        self.category_word_counts: Dict[str, Counter] = defaultdict(Counter)
        self.category_counts: Counter = Counter()
        self.vocab: set = set()
        self.categories = CATEGORIES
        self.is_trained = False

    def _tokenize(self, text: str) -> List[str]:
        # Word unigrams + character 3-grams for multilingual robustness
        words = re.findall(r'\w+', text.lower())
        chars = [text[i:i+3] for i in range(len(text) - 2)]
        return words + chars

    def fit(self, X: List[str], y: List[str]):
        for text, label in zip(X, y):
            tokens = self._tokenize(text)
            self.category_counts[label] += 1
            for token in tokens:
                self.category_word_counts[label][token] += 1
                self.vocab.add(token)
        self.is_trained = True

    def predict_one(self, text: str) -> Tuple[str, Dict[str, float]]:
        tokens = self._tokenize(text)
        total_docs = sum(self.category_counts.values())
        scores: Dict[str, float] = {}

        for cat in self.categories:
            cat_doc_count = self.category_counts[cat]
            if cat_doc_count == 0:
                scores[cat] = -999.0
                continue
            prior = math.log(cat_doc_count / total_docs)
            word_total = sum(self.category_word_counts[cat].values()) + len(self.vocab) + 1
            log_prob = prior
            for token in tokens:
                count = self.category_word_counts[cat][token]
                log_prob += math.log((count + 1) / word_total)
            scores[cat] = log_prob

        max_s = max(scores.values())
        exp_scores = {k: math.exp(v - max_s) for k, v in scores.items()}
        s = sum(exp_scores.values())
        probs = {k: round(v / s, 4) for k, v in exp_scores.items()}
        pred_cat = max(probs, key=probs.get)
        return pred_cat, probs


# ─────────────────────────────────────────────────────────────────────────────
# sklearn-based Ensemble Classifier
# ─────────────────────────────────────────────────────────────────────────────
def _build_feature_extractor():
    """
    Dual TF-IDF feature matrix:
      • word (1,3)-grams  : captures phrase semantics
      • char (2,5)-grams  : captures morphology, handles Hindi/Tamil subwords
    """
    word_tfidf = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 3),
        max_features=15_000,
        sublinear_tf=True,
        min_df=1,
        strip_accents=None,
    )
    char_tfidf = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        max_features=20_000,
        sublinear_tf=True,
        min_df=1,
    )
    return word_tfidf, char_tfidf


def _build_soft_voter():
    """
    Soft-voting ensemble of three diverse linear models:
      • Logistic Regression  (multinomial, L2)  → calibrated probability
      • Linear SVC           (fast, high-margin) → calibrated via Platt
      • SGD with log-loss    (online-style)      → soft proba natively
    """
    lr = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        C=2.0,
    )
    svc = CalibratedClassifierCV(
        LinearSVC(class_weight="balanced", max_iter=3000, C=1.0),
        cv=3,
        method="isotonic",
    )
    sgd = SGDClassifier(
        loss="modified_huber",
        penalty="l2",
        alpha=1e-4,
        class_weight="balanced",
        max_iter=200,
        random_state=42,
        n_jobs=-1,
    )
    voter = VotingClassifier(
        estimators=[("lr", lr), ("svc", svc), ("sgd", sgd)],
        voting="soft",
        n_jobs=-1,
    )
    return voter


# ─────────────────────────────────────────────────────────────────────────────
# Main Classifier Class
# ─────────────────────────────────────────────────────────────────────────────
class BaselineClassifier:
    """
    Enhanced Ensemble Classifier.
    sklearn path  : Dual-TF-IDF features → Soft-Voting (LR + LinearSVC + SGD).
    fallback path : Pure-Python Multinomial Naïve Bayes with char n-grams.
    """

    def __init__(self):
        self.categories = CATEGORIES
        self.is_trained = False

        if SKLEARN_AVAILABLE:
            self.word_tfidf, self.char_tfidf = _build_feature_extractor()
            self.model = _build_soft_voter()
            self.fallback_model = None
        else:
            self.word_tfidf = None
            self.char_tfidf = None
            self.model = None
            self.fallback_model = PurePythonNaiveBayes()

    def _get_features(self, texts: List[str], fit: bool = False):
        if fit:
            X_word = self.word_tfidf.fit_transform(texts)
            X_char = self.char_tfidf.fit_transform(texts)
        else:
            X_word = self.word_tfidf.transform(texts)
            X_char = self.char_tfidf.transform(texts)
        return hstack([X_word, X_char], format="csr")

    def train(self, train_data: List[Dict]) -> Dict:
        X_train = [item["text"] for item in train_data]
        y_train = [item["category"] for item in train_data]

        if SKLEARN_AVAILABLE:
            X_feat = self._get_features(X_train, fit=True)
            self.model.fit(X_feat, y_train)
            y_pred = self.model.predict(X_feat)
            train_f1 = f1_score(y_train, y_pred, average="macro")
        else:
            self.fallback_model.fit(X_train, y_train)
            preds = [self.fallback_model.predict_one(x)[0] for x in X_train]
            train_f1 = sum(p == t for p, t in zip(preds, y_train)) / max(len(y_train), 1)

        self.is_trained = True
        print(f"  [Classifier] Train macro-F1: {train_f1:.4f}")
        return {"status": "success", "train_macro_f1": round(float(train_f1), 4)}

    def evaluate(self, test_data: List[Dict]) -> Dict:
        if not self.is_trained:
            raise ValueError("Model not trained yet.")

        X_test = [item["text"] for item in test_data]
        y_test = [item["category"] for item in test_data]

        if SKLEARN_AVAILABLE:
            X_feat = self._get_features(X_test)
            y_pred = self.model.predict(X_feat)
            macro_f1 = f1_score(y_test, y_pred, average="macro")
            report = classification_report(y_test, y_pred, output_dict=True)

            lang_metrics: Dict[str, float] = {}
            for lang in ["en", "hi", "ta"]:
                items = [it for it in test_data if it["language"] == lang]
                if items:
                    Xl = self._get_features([it["text"] for it in items])
                    yl = [it["category"] for it in items]
                    yl_pred = self.model.predict(Xl)
                    lang_metrics[lang] = round(float(f1_score(yl, yl_pred, average="macro")), 4)
        else:
            y_pred = [self.fallback_model.predict_one(x)[0] for x in X_test]
            macro_f1 = sum(p == t for p, t in zip(y_pred, y_test)) / max(len(y_test), 1)
            report = {"accuracy": macro_f1}
            lang_metrics = {}
            for lang in ["en", "hi", "ta"]:
                items = [it for it in test_data if it["language"] == lang]
                if items:
                    lp = [self.fallback_model.predict_one(it["text"])[0] for it in items]
                    la = sum(p == t for p, t in zip(lp, [it["category"] for it in items])) / max(len(items), 1)
                    lang_metrics[lang] = round(la, 4)

        return {
            "model_type": "Ensemble (LR+LinearSVC+SGD) / Dual TF-IDF" if SKLEARN_AVAILABLE else "Pure Python NB",
            "overall_macro_f1": round(float(macro_f1), 4),
            "per_language_f1": lang_metrics,
            "detailed_report": report,
        }

    def predict(self, text: str) -> Dict:
        if not self.is_trained:
            raise ValueError("Model not trained yet.")

        if SKLEARN_AVAILABLE:
            X_feat = self._get_features([text])
            probs = self.model.predict_proba(X_feat)[0]
            top_idx = int(np.argmax(probs))
            category = self.model.classes_[top_idx]
            confidence = float(probs[top_idx])
            all_scores = {cls: round(float(p), 4) for cls, p in zip(self.model.classes_, probs)}
        else:
            category, all_scores = self.fallback_model.predict_one(text)
            confidence = all_scores[category]

        return {
            "predicted_category": category,
            "confidence": round(confidence, 4),
            "all_scores": all_scores,
        }

    def save(self, file_path: Path = None):
        if file_path is None:
            file_path = MODELS_DIR / "baseline_classifier.pkl"
        fallback_data = None
        if self.fallback_model is not None:
            fallback_data = {
                "category_word_counts": {k: dict(v) for k, v in self.fallback_model.category_word_counts.items()},
                "category_counts": dict(self.fallback_model.category_counts),
                "vocab": list(self.fallback_model.vocab),
                "is_trained": self.fallback_model.is_trained,
            }
        with open(file_path, "wb") as f:
            pickle.dump({
                "word_tfidf": self.word_tfidf,
                "char_tfidf": self.char_tfidf,
                "model": self.model,
                "fallback_data": fallback_data,
            }, f, protocol=4)
        print(f"  [Classifier] Saved → {file_path}")

    def load(self, file_path: Path = None) -> bool:
        if file_path is None:
            file_path = MODELS_DIR / "baseline_classifier.pkl"
        if not file_path.exists():
            return False
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            self.word_tfidf = data.get("word_tfidf")
            self.char_tfidf = data.get("char_tfidf")
            # backwards compat: old pkl only had "vectorizer"
            if self.word_tfidf is None:
                self.word_tfidf = data.get("vectorizer")
                self.char_tfidf = None
            self.model = data.get("model")
            fd = data.get("fallback_data")
            if fd:
                self.fallback_model = PurePythonNaiveBayes()
                self.fallback_model.category_counts = Counter(fd["category_counts"])
                for k, v in fd["category_word_counts"].items():
                    self.fallback_model.category_word_counts[k] = Counter(v)
                self.fallback_model.vocab = set(fd["vocab"])
                self.fallback_model.is_trained = fd["is_trained"]
            self.is_trained = True
            return True
        except Exception as e:
            print(f"  [Classifier] Load failed: {e}")
            return False

    def _get_features(self, texts: List[str], fit: bool = False):
        """Override to handle missing char_tfidf gracefully (backwards compat)."""
        if not SKLEARN_AVAILABLE:
            return None
        if fit:
            X_word = self.word_tfidf.fit_transform(texts)
            if self.char_tfidf is not None:
                X_char = self.char_tfidf.fit_transform(texts)
                return hstack([X_word, X_char], format="csr")
            return X_word
        else:
            X_word = self.word_tfidf.transform(texts)
            if self.char_tfidf is not None:
                X_char = self.char_tfidf.transform(texts)
                return hstack([X_word, X_char], format="csr")
            return X_word


def train_and_eval_baseline():
    """Helper script: train + evaluate + save the baseline ensemble."""
    with open(DATA_DIR / "train.json", "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(DATA_DIR / "test.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)

    clf = BaselineClassifier()
    clf.train(train_data)
    results = clf.evaluate(test_data)
    clf.save()
    return results


if __name__ == "__main__":
    res = train_and_eval_baseline()
    print("Baseline Ensemble Evaluation:")
    print(json.dumps(res, indent=2))
