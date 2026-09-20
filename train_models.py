"""
train_models.py — Master Training & Evaluation Script
======================================================
Regenerates the dataset (80 samples/cat/lang), trains all ML models from scratch,
evaluates them on the held-out test set, and prints a comprehensive report.

Run with:
    python train_models.py
    python train_models.py --regen   # also regenerate dataset
"""

import sys
import io
# Ensure UTF-8 output in PowerShell / Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
import time
from pathlib import Path

from config import DATA_DIR, MODELS_DIR


def separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main(regen_data: bool = False):
    t_start = time.time()

    # ── 0. Dataset ────────────────────────────────────────────────────────
    separator("STEP 0: Dataset Generation")

    train_path = DATA_DIR / "train.json"
    if regen_data or not train_path.exists():
        from data_generator import save_dataset
        full, train_data, val_data, test_data = save_dataset(80)
        print(f"Dataset created: train={len(train_data)} | val={len(val_data)} | test={len(test_data)}")
    else:
        with open(DATA_DIR / "train.json", "r", encoding="utf-8") as f:
            train_data = json.load(f)
        with open(DATA_DIR / "val.json", "r", encoding="utf-8") as f:
            val_data = json.load(f)
        with open(DATA_DIR / "test.json", "r", encoding="utf-8") as f:
            test_data = json.load(f)
        print(f"Loaded existing dataset: train={len(train_data)} | val={len(val_data)} | test={len(test_data)}")

    # ── 1. Complaint Classifier ───────────────────────────────────────────
    separator("STEP 1: Training Complaint Classifier (Ensemble)")
    from models.complaint_classifier import BaselineClassifier

    # Delete stale saved model so we always retrain fresh here
    stale_clf = MODELS_DIR / "baseline_classifier.pkl"
    if stale_clf.exists():
        stale_clf.unlink()
        print("  Deleted stale classifier model.")

    clf = BaselineClassifier()
    t0 = time.time()
    train_res = clf.train(train_data)
    print(f"  Training done in {time.time()-t0:.1f}s — Train macro-F1: {train_res['train_macro_f1']}")

    # Val evaluation
    val_res = clf.evaluate(val_data)
    print(f"  Val   macro-F1: {val_res['overall_macro_f1']}")
    print(f"  Per-language val F1: {val_res['per_language_f1']}")

    # Test evaluation
    test_res = clf.evaluate(test_data)
    print(f"\n  ★ Test  macro-F1: {test_res['overall_macro_f1']}")
    print(f"  ★ Per-language test F1: {test_res['per_language_f1']}")

    clf.save()

    # ── 2. Priority Predictor ─────────────────────────────────────────────
    separator("STEP 2: Training Priority Predictor (ML Hybrid)")
    from models.priority_predictor import PriorityPredictor

    stale_prio = MODELS_DIR / "priority_predictor.pkl"
    if stale_prio.exists():
        stale_prio.unlink()
        print("  Deleted stale priority model.")

    prio = PriorityPredictor()
    t0 = time.time()
    prio_train_res = prio.train(train_data)
    print(f"  Training done in {time.time()-t0:.1f}s — {prio_train_res}")

    prio_test_res = prio.evaluate(test_data)
    print(f"  ★ Priority Test macro-F1: {prio_test_res.get('overall_macro_f1', 'N/A')}")

    fairness = prio.audit_fairness(test_data)
    print(f"  Language Fairness: max_disparity={fairness['max_disparity_score']:.3f}  "
          f"{'✓ FAIR' if fairness['is_fair'] else '✗ REQUIRES CALIBRATION'}")
    prio.save()

    # ── 3. Duplicate Detector ─────────────────────────────────────────────
    separator("STEP 3: Building Duplicate Detection Index")
    from models.duplicate_detector import DuplicateDetector

    t0 = time.time()
    detector = DuplicateDetector()
    detector.populate_database(train_data)
    print(f"  Index built in {time.time()-t0:.1f}s using backend='{detector.backend}'")

    # Self-test: known sample should be flagged as duplicate
    sample = train_data[0]
    dup_res = detector.check_duplicate(sample["text"], category=sample["category"])
    print(f"  Self-check (known sample): sim={dup_res['similarity_score']:.4f}  "
          f"is_duplicate={dup_res['is_duplicate']}")

    # Test: dissimilar text
    dis_res = detector.check_duplicate("Completely unrelated text about something else.")
    print(f"  Non-dup check:             sim={dis_res['similarity_score']:.4f}  "
          f"is_duplicate={dis_res['is_duplicate']}")

    # ── 4. End-to-end Pipeline ────────────────────────────────────────────
    separator("STEP 4: End-to-End Pipeline Evaluation")
    from pipeline import GrievanceAIPipeline

    pipeline = GrievanceAIPipeline()
    # Inject already-trained models to avoid re-training
    pipeline.classifier = clf
    pipeline.priority_predictor = prio
    pipeline.duplicate_detector = detector
    pipeline.duplicate_detector.populate_database(train_data)
    pipeline.is_initialized = True

    metrics = {
        "en": {"total": 0, "correct_cat": 0, "correct_route": 0},
        "hi": {"total": 0, "correct_cat": 0, "correct_route": 0},
        "ta": {"total": 0, "correct_cat": 0, "correct_route": 0},
    }

    for item in test_data:
        lang = item["language"]
        if lang not in metrics:
            continue
        res = pipeline.process_grievance(item["text"])
        pred_cat = res["classification"]["predicted_category"]
        pred_dept = res["routing"]["target_department"]
        metrics[lang]["total"] += 1
        if pred_cat == item["category"]:
            metrics[lang]["correct_cat"] += 1
        expected_dept = pipeline.router.mapping.get(item["category"])
        if pred_dept == expected_dept:
            metrics[lang]["correct_route"] += 1

    print(f"\n  {'Language':<12} | {'Samples':<8} | {'Cat Acc':<10} | {'Route Acc':<12}")
    print(f"  {'-'*50}")
    for lang, m in metrics.items():
        if m["total"] == 0:
            continue
        acc = m["correct_cat"] / m["total"] * 100
        racc = m["correct_route"] / m["total"] * 100
        lang_name = {"en": "English", "hi": "Hindi", "ta": "Tamil"}[lang]
        print(f"  {lang_name:<12} | {m['total']:<8} | {acc:<9.1f}% | {racc:<11.1f}%")

    # ── 5. Summary ────────────────────────────────────────────────────────
    separator("TRAINING COMPLETE — SUMMARY")
    print(f"  Classifier   macro-F1  : {test_res['overall_macro_f1']:.4f}")
    print(f"  Priority     macro-F1  : {prio_test_res.get('overall_macro_f1', 'N/A')}")
    print(f"  Fairness disparity    : {fairness['max_disparity_score']:.4f}")
    print(f"  Total elapsed         : {time.time()-t_start:.1f}s")
    print()

    return {
        "classifier": test_res,
        "priority": prio_test_res,
        "fairness": fairness,
        "pipeline_metrics": metrics,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train all Grievance Portal ML models")
    parser.add_argument("--regen", action="store_true", help="Regenerate synthetic dataset")
    args = parser.parse_args()
    main(regen_data=args.regen)
