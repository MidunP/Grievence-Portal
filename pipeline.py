"""
Integrated Master AI Pipeline Orchestrator for Grievance Portal.
Chains Phase 2 (Language Detection) -> Phase 3 (Classification) -> Phase 4 (Duplicate Check)
       -> Phase 5 (Priority Prediction) -> Phase 6 (Routing) -> Phase 7 (Explainability).
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

from config import DATA_DIR, MODELS_DIR
from models.language_detector import detect_language
from models.complaint_classifier import BaselineClassifier
from models.duplicate_detector import DuplicateDetector
from models.priority_predictor import PriorityPredictor
from models.department_router import DepartmentRouter
from models.explainer import GrievanceExplainer


class GrievanceAIPipeline:
    """Master AI Pipeline Orchestrator."""

    def __init__(self):
        self.classifier = BaselineClassifier()
        self.duplicate_detector = DuplicateDetector()
        self.priority_predictor = PriorityPredictor()
        self.router = DepartmentRouter()
        self.explainer = GrievanceExplainer()
        self.is_initialized = False

    def initialize(self, force_retrain: bool = False):
        """
        Loads data, trains/loads all ML models, and builds the vector index.
        Set force_retrain=True to clear saved models and retrain from scratch.
        """
        train_path = DATA_DIR / "train.json"
        if not train_path.exists():
            from data_generator import save_dataset
            save_dataset(80)  # Use 80 samples/cat/lang for richer training

        with open(train_path, "r", encoding="utf-8") as f:
            train_data = json.load(f)

        print(f"[Pipeline] Initializing on {len(train_data)} training samples...")

        # ── Complaint Classifier (Ensemble) ──────────────────────────────
        clf_path = MODELS_DIR / "baseline_classifier.pkl"
        if force_retrain and clf_path.exists():
            clf_path.unlink()
        if not self.classifier.load():
            print("[Pipeline] Training classifier ensemble...")
            self.classifier.train(train_data)
            self.classifier.save()
        else:
            print("[Pipeline] Loaded saved classifier.")

        # ── Priority Predictor (ML) ───────────────────────────────────────
        prio_path = MODELS_DIR / "priority_predictor.pkl"
        if force_retrain and prio_path.exists():
            prio_path.unlink()
        if not self.priority_predictor.load():
            print("[Pipeline] Training priority predictor...")
            self.priority_predictor.train(train_data)
            self.priority_predictor.save()
        else:
            print("[Pipeline] Loaded saved priority predictor.")

        # ── Duplicate Detection Index ─────────────────────────────────────
        print("[Pipeline] Building duplicate detection index...")
        self.duplicate_detector.populate_database(train_data)

        self.is_initialized = True
        print("[Pipeline] Initialization complete.\n")
        return True

    def process_grievance(self, text: str, area: str = "Unknown", days_open: int = 0) -> Dict:
        """
        Executes end-to-end AI pipeline on a new grievance submission.
        """
        if not self.is_initialized:
            self.initialize()

        # Phase 2: Language Detection
        lang_res = detect_language(text)
        language = lang_res["language"]

        # Phase 3: Category Classification
        cat_res = self.classifier.predict(text)

        # Phase 4: Duplicate Detection
        dup_res = self.duplicate_detector.check_duplicate(text, category=cat_res["predicted_category"])

        # Phase 5: Priority Prediction
        prio_res = self.priority_predictor.predict_priority(
            text=text,
            language=language,
            category=cat_res["predicted_category"],
            days_open=days_open
        )

        # Phase 6: Department Routing
        route_res = self.router.route_complaint(
            category=cat_res["predicted_category"],
            text=text
        )

        # Phase 7: Explainability Summary
        explanation = self.explainer.format_explanation(
            text=text,
            language=language,
            category_res=cat_res,
            priority_res=prio_res,
            routing_res=route_res
        )

        return {
            "input_text": text,
            "area": area,
            "language_detection": lang_res,
            "classification": cat_res,
            "duplicate_check": dup_res,
            "priority": prio_res,
            "routing": route_res,
            "explanation": explanation
        }


# Global singleton instance
pipeline_instance = GrievanceAIPipeline()


if __name__ == "__main__":
    pipeline = GrievanceAIPipeline()
    pipeline.initialize()

    test_samples = [
        "Main water pipeline burst near Station Road. Heavy flooding.",
        "वार्ड नंबर 10 में कचरा नहीं उठाया गया है। दुर्गंध आ रही है।",
        "வார்டு 5 பகுதியில் சாக்கடை நீர் பொங்கி வழிகிறது."
    ]

    for sample in test_samples:
        print("\n==========================================")
        res = pipeline.process_grievance(sample)
        print(f"Input: {res['input_text']}")
        print(f"Detected Lang: {res['language_detection']['language']}")
        print(f"Category: {res['classification']['predicted_category']} (Conf: {res['classification']['confidence']})")
        print(f"Duplicate?: {res['duplicate_check']['is_duplicate']} (Score: {res['duplicate_check']['similarity_score']})")
        print(f"Priority: {res['priority']['priority']}")
        print(f"Routed To: {res['routing']['target_department']}")
        print(f"Explanation: {res['explanation']['summary']}")
