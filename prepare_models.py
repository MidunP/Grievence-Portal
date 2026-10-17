"""
Model preparation & verification script for Docker build and deployment.
Verifies pre-trained models and synthetic dataset; trains models if missing.
"""
import sys
import subprocess
from pathlib import Path

from config import MODELS_DIR, DATA_DIR


def prepare():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    clf_exists = (MODELS_DIR / "baseline_classifier.pkl").exists()
    prio_exists = (MODELS_DIR / "priority_predictor.pkl").exists()
    data_exists = (DATA_DIR / "train.json").exists()

    if not data_exists:
        print("[Build] Generating dataset (data/train.json)...")
        subprocess.run([sys.executable, "data_generator.py"], check=True)
    else:
        print("[Build] Dataset verified.")

    if not clf_exists or not prio_exists:
        print("[Build] Training ML models...")
        subprocess.run([sys.executable, "train_models.py"], check=True)
    else:
        print("[Build] Pre-trained models verified.")


if __name__ == "__main__":
    prepare()
