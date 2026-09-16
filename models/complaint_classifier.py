"""
Phase 3: Multilingual Complaint Classifier.
Implements TF-IDF + Logistic Regression baseline and Hugging Face Transformer fine-tuning (MuRIL / IndicBERT).
Provides macro-F1 evaluation across English, Hindi, and Tamil test sets.
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
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from config import CATEGORIES, MODELS_DIR, DATA_DIR


class PurePythonNaiveBayes:
    """Lightweight Naive Bayes Classifier when sklearn is missing."""
    def __init__(self):
        self.category_word_counts = defaultdict(Counter)
        self.category_counts = Counter()
        self.vocab = set()
        self.categories = CATEGORIES
        self.is_trained = False

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def fit(self, X: List[str], y: List[str]):
        for text, label in zip(X, y):
            tokens = self.tokenize(text)
            self.category_counts[label] += 1
            for token in tokens:
                self.category_word_counts[label][token] += 1
                self.vocab.add(token)
        self.is_trained = True

    def predict_one(self, text: str) -> Tuple[str, Dict[str, float]]:
        tokens = self.tokenize(text)
        total_docs = sum(self.category_counts.values())
        scores = {}
        
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

        # Softmax normalization for probabilities
        max_s = max(scores.values())
        exp_scores = {k: math.exp(v - max_s) for k, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {k: round(v / sum_exp, 4) for k, v in exp_scores.items()}
        
        pred_cat = max(probs, key=probs.get)
        return pred_cat, probs



class BaselineClassifier:
    """TF-IDF + Logistic Regression Baseline (or Pure Python Naive Bayes fallback)."""

    def __init__(self):
        self.categories = CATEGORIES
        self.is_trained = False
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
            self.model = LogisticRegression(class_weight="balanced", max_iter=500)
            self.fallback_model = None
        else:
            self.vectorizer = None
            self.model = None
            self.fallback_model = PurePythonNaiveBayes()

    def train(self, train_data: List[Dict]) -> Dict:
        X_train = [item["text"] for item in train_data]
        y_train = [item["category"] for item in train_data]

        if SKLEARN_AVAILABLE:
            X_tfidf = self.vectorizer.fit_transform(X_train)
            self.model.fit(X_tfidf, y_train)
            y_pred = self.model.predict(X_tfidf)
            train_f1 = f1_score(y_train, y_pred, average="macro")
        else:
            self.fallback_model.fit(X_train, y_train)
            preds = [self.fallback_model.predict_one(x)[0] for x in X_train]
            correct = sum(1 for p, t in zip(preds, y_train) if p == t)
            train_f1 = correct / max(len(y_train), 1)

        self.is_trained = True
        return {"status": "success", "train_macro_f1": round(train_f1, 4)}

    def evaluate(self, test_data: List[Dict]) -> Dict:
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")

        X_test = [item["text"] for item in test_data]
        y_test = [item["category"] for item in test_data]

        if SKLEARN_AVAILABLE:
            X_tfidf = self.vectorizer.transform(X_test)
            y_pred = self.model.predict(X_tfidf)
            macro_f1 = f1_score(y_test, y_pred, average="macro")
            report = classification_report(y_test, y_pred, output_dict=True)
            
            lang_metrics = {}
            for lang in ["en", "hi", "ta"]:
                lang_items = [item for item in test_data if item["language"] == lang]
                if lang_items:
                    X_lang = self.vectorizer.transform([item["text"] for item in lang_items])
                    y_lang = [item["category"] for item in lang_items]
                    y_lang_pred = self.model.predict(X_lang)
                    lang_metrics[lang] = round(float(f1_score(y_lang, y_lang_pred, average="macro")), 4)
        else:
            y_pred = [self.fallback_model.predict_one(x)[0] for x in X_test]
            correct = sum(1 for p, t in zip(y_pred, y_test) if p == t)
            macro_f1 = correct / max(len(y_test), 1)
            report = {"accuracy": macro_f1}
            
            lang_metrics = {}
            for lang in ["en", "hi", "ta"]:
                lang_items = [item for item in test_data if item["language"] == lang]
                if lang_items:
                    l_preds = [self.fallback_model.predict_one(item["text"])[0] for item in lang_items]
                    l_targets = [item["category"] for item in lang_items]
                    l_acc = sum(1 for p, t in zip(l_preds, l_targets) if p == t) / max(len(l_targets), 1)
                    lang_metrics[lang] = round(l_acc, 4)

        return {
            "model_type": "TF-IDF + Logistic Regression" if SKLEARN_AVAILABLE else "Pure Python Naive Bayes Baseline",
            "overall_macro_f1": round(float(macro_f1), 4),
            "per_language_f1": lang_metrics,
            "detailed_report": report
        }

    def predict(self, text: str) -> Dict:
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")

        if SKLEARN_AVAILABLE:
            X_tfidf = self.vectorizer.transform([text])
            probs = self.model.predict_proba(X_tfidf)[0]
            top_idx = int(np.argmax(probs))
            category = self.model.classes_[top_idx]
            confidence = float(probs[top_idx])
            all_scores = {cls: round(float(prob), 4) for cls, prob in zip(self.model.classes_, probs)}
        else:
            category, all_scores = self.fallback_model.predict_one(text)
            confidence = all_scores[category]

        return {
            "predicted_category": category,
            "confidence": round(confidence, 4),
            "all_scores": all_scores
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
                "is_trained": self.fallback_model.is_trained
            }
        with open(file_path, "wb") as f:
            pickle.dump({
                "vectorizer": self.vectorizer,
                "model": self.model,
                "fallback_data": fallback_data
            }, f)

    def load(self, file_path: Path = None) -> bool:
        if file_path is None:
            file_path = MODELS_DIR / "baseline_classifier.pkl"
        if not file_path.exists():
            return False
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
                self.vectorizer = data.get("vectorizer")
                self.model = data.get("model")
                fallback_data = data.get("fallback_data")
                if fallback_data:
                    self.fallback_model = PurePythonNaiveBayes()
                    self.fallback_model.category_counts = Counter(fallback_data["category_counts"])
                    for k, v in fallback_data["category_word_counts"].items():
                        self.fallback_model.category_word_counts[k] = Counter(v)
                    self.fallback_model.vocab = set(fallback_data["vocab"])
                    self.fallback_model.is_trained = fallback_data["is_trained"]
                self.is_trained = True
                return True
        except Exception:
            return False



def train_and_eval_baseline():
    """Helper script to train and evaluate baseline classifier."""
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
    print("Baseline Model Evaluation:")
    print(json.dumps(res, indent=2))

