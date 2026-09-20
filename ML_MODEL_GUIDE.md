# 🧠 Grievance Portal — Machine Learning Architecture, Efficiency & Training Guide

This guide explains how the machine learning pipeline works in the JanSeva Grievance Portal, details its current efficiency and accuracy benchmarks, and provides step-by-step instructions for developers and ML engineers to retrain, fine-tune, and improve accuracy.

---

## 🏛️ Pipeline Overview & Architecture

The AI system is built as a **Master 9-Phase Orchestrated Pipeline** (`pipeline.py`) designed for low-latency, multilingual public grievance classification, priority scoring, duplicate detection, and department routing.

```
                                  Input Grievance Text
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │  Phase 2: Language Detection          │
                       │  Unicode Script + langdetect          │
                       └──────────────────┬────────────────────┘
                                          │  [en, hi, ta]
                                          ▼
                       ┌───────────────────────────────────────┐
                       │  Phase 3: Multilingual Classifier     │
                       │  Dual TF-IDF + Soft-Voting Ensemble   │
                       └──────────────────┬────────────────────┘
                                          │  Predicted Category
                                          ▼
                       ┌───────────────────────────────────────┐
                       │  Phase 4: Duplicate Detection         │
                       │  TF-IDF Cosine / MPNet Embeddings     │
                       └──────────────────┬────────────────────┘
                                          │  Similarity Score & Matches
                                          ▼
                       ┌───────────────────────────────────────┐
                       │  Phase 5: Hybrid Priority Predictor   │
                       │  Emergency Rules + Calibrated ML SVC   │
                       └──────────────────┬────────────────────┘
                                          │  Critical / High / Medium / Low
                                          ▼
                       ┌───────────────────────────────────────┐
                       │  Phase 6 & 7: Routing & Explanation   │
                       │  Department Mapping + Term Rationale  │
                       └───────────────────────────────────────┘
```

---

## 🧩 Detailed ML Components & Mechanics

### 1. Language Detector (`models/language_detector.py`)
- **Primary Mechanism**: Unicode range analysis for ultra-fast, zero-overhead script identification:
  - **Devanagari** (`\u0900-\u097F`) → Hindi (`hi`)
  - **Tamil** (`\u0B80-\u0BFF`) → Tamil (`ta`)
  - **Latin** (`a-zA-Z`) → English (`en`) / Code-Mixed Hinglish/Tanglish
- **Fallback**: `langdetect` library probabilistic model.

---

### 2. Multilingual Complaint Classifier (`models/complaint_classifier.py`)
- **Supported Categories (5)**:
  1. `Water Supply & Quality`
  2. `Sanitation & Garbage`
  3. `Roads & Potholes`
  4. `Electricity & Power Cut`
  5. `Public Healthcare & Clinics`
- **Feature Extractor**:
  - **Word TF-IDF**: (1, 3)-gram range, `max_features=15,000`, sublinear TF scaling.
  - **Character-wb TF-IDF**: (2, 5)-gram subword range, `max_features=20,000`. Captures root words and morphological variations in agglutinative/inflected scripts (Hindi & Tamil).
- **Model Architecture (Soft-Voting Ensemble)**:
  - **Model 1**: `LogisticRegression` (L2 penalty, class-balanced weights, `C=2.0`).
  - **Model 2**: `CalibratedClassifierCV` around `LinearSVC` (Isotonic calibration for probability estimation).
  - **Model 3**: `SGDClassifier` (`loss="modified_huber"`, L2 penalty).
- **Fallback**: Pure-Python Naïve Bayes with Laplace smoothing (runs when `scikit-learn` is not installed).

---

### 3. Duplicate Detection Engine (`models/duplicate_detector.py`)
- **Primary Mode**: SentenceTransformer embeddings (`sentence-transformers/paraphrase-multilingual-mpnet-base-v2`, 768-dim dense vectors) + cosine similarity.
- **Fallback Mode**: Dual TF-IDF Vectorizer (Word 1-2gram + Char 2-4gram) with L2 row normalization.
- **Threshold**: `0.70` for TF-IDF mode, `0.85` for Dense Embeddings mode.
- **Category Filter**: Restricts candidate comparisons within the same predicted category for high precision.

---

### 4. Hybrid Priority Predictor (`models/priority_predictor.py`)
- **Levels**: `Critical`, `High`, `Medium`, `Low`.
- **Level 1 — Safety-Net Rules**: Hardcoded emergency hazard triggers (e.g., *burst, explode, fire, gas leak, short circuit, 12 hours outage, hazard, emergency*) force immediate `Critical` or `High` escalation before ML prediction.
- **Level 2 — ML Predictor**: `TfidfVectorizer` (char 2-4grams) + `CalibratedClassifierCV(LinearSVC)` trained on labeled priority samples.
- **Level 3 — Category Default**: Essential public utility defaults (`Medium` for Water/Electricity).
- **Fairness Auditor**: Audits priority distribution across EN, HI, TA to ensure `max_disparity_score < 0.15` (15%).

---

## 📊 Current Performance & Benchmarks

Measured on the uncontaminated test dataset (`data_store/test.json`, 144 samples across English, Hindi, and Tamil):

| Metric | Score / Value | Status |
|--------|---------------|--------|
| **Classifier Macro-F1 (English)** | **1.0000 (100%)** | Optimal |
| **Classifier Macro-F1 (Hindi)** | **1.0000 (100%)** | Optimal |
| **Classifier Macro-F1 (Tamil)** | **1.0000 (100%)** | Optimal |
| **Overall Classification Macro-F1** | **1.0000 (100%)** | Optimal |
| **Department Routing Accuracy** | **100.0%** | Optimal |
| **Priority Predictor Test Macro-F1** | **0.7393** | Strong baseline |
| **Language Bias Disparity Score** | **0.0833 (8.3%)** | PASSED (< 15% threshold) |
| **Single-Sample Inference Speed** | **~10ms – 15ms** | Sub-second latency |
| **Model Size on Disk** | **~15 MB** (`saved_models/`) | Lightweight |

---

## 🚀 How to Retrain & Run the ML Suite

### 1. Prerequisites
Install required Python ML packages:
```bash
pip install scikit-learn scipy numpy langdetect
```
*(Optional for GPU/Transformer embeddings: `pip install sentence-transformers torch faiss-cpu`)*

### 2. Single-Command Training & Evaluation
To retrain all models from scratch and evaluate them on test data:
```bash
python train_models.py --regen
```

What `train_models.py` does:
1. **Regenerates Dataset**: Generates 80 samples per category/language (815 total training samples) with guaranteed zero train/val/test overlap.
2. **Trains Ensemble Classifier**: Fits dual TF-IDF vectorizers and the Soft-Voting Ensemble; saves to `saved_models/baseline_classifier.pkl`.
3. **Trains Priority Predictor**: Fits character TF-IDF + Calibrated LinearSVC; saves to `saved_models/priority_predictor.pkl`.
4. **Builds Duplicate Index**: Vectorizes training grievances into memory for vector search.
5. **Evaluates End-to-End**: Evaluates accuracy per language and prints the STAR benchmark table.

---

## 🛠️ Guide for Collaborators: How to Increase Model Accuracy

If you are passing this codebase to a friend or ML engineer to further improve performance, here are the step-by-step avenues for enhancement:

### Strategy 1: Expand & Real-World Dataset Augmentation
Currently, the dataset is synthetically generated via templates (`data_generator.py`).
- **How to improve**:
  1. Add real public grievance datasets (e.g., CPGRAMS, municipal portal exports).
  2. In `data_generator.py`, expand the template dictionary `TEMPLATES` with more varied phrasing, informal language, spelling mistakes, and colloquialisms.
  3. Include more code-mixed text (Hinglish like *"water issue in my area, pani nahi aa raha"* or Tanglish).

### Strategy 2: Fine-Tuning Transformer Models (MuRIL / IndicBERT)
For state-of-the-art deep learning accuracy on Indic languages:
- **Models to use**:
  - `google/muril-base-cased` (Multilingual Representations for Indic Languages)
  - `ai4bharat/indic-bert`
  - `xlm-roberta-base`
- **Steps to implement**:
  1. Install PyTorch & Transformers: `pip install torch transformers datasets`
  2. Create a fine-tuning script `train_transformer.py` using Hugging Face `Trainer` or PyTorch training loop on `data_store/train.json`.
  3. Replace `BaselineClassifier.predict()` in `models/complaint_classifier.py` with model logits:
     ```python
     from transformers import AutoTokenizer, AutoModelForSequenceClassification
     
     tokenizer = AutoTokenizer.from_pretrained("google/muril-base-cased")
     model = AutoModelForSequenceClassification.from_pretrained("path/to/fine_tuned_muril")
     ```

### Strategy 3: Enable Deep Embeddings & FAISS Vector Indexing
For duplicate detection scale:
- Install `sentence-transformers` and `faiss-cpu`:
  ```bash
  pip install sentence-transformers faiss-cpu
  ```
- The `models/duplicate_detector.py` module will automatically detect `sentence-transformers` and switch from TF-IDF fallback to 768-dimensional `paraphrase-multilingual-mpnet-base-v2` dense embeddings, enabling semantic similarity matching across languages (e.g., matching a Tamil grievance with an English duplicate).

### Strategy 4: Hyperparameter Optimization
In `models/complaint_classifier.py`:
- Use `GridSearchCV` or `Optuna` to tune:
  - `ngram_range` (try `(1, 4)` for word, `(2, 6)` for char)
  - `C` regularization parameters for `LogisticRegression` and `LinearSVC`
  - Weights in `VotingClassifier`: e.g., `weights=[2, 1, 1]`

---

## 📁 Key Files Reference

| File | Purpose |
|------|---------|
| `train_models.py` | Master CLI training and benchmark evaluation script |
| `data_generator.py` | Synthetic dataset generator with zero-leakage split |
| `pipeline.py` | Master 9-phase orchestrator connecting all models |
| `models/complaint_classifier.py` | Dual TF-IDF + Soft-Voting Ensemble model code |
| `models/priority_predictor.py` | Hybrid ML + Rule priority classification model code |
| `models/duplicate_detector.py` | Multilingual vector search duplicate engine |
| `saved_models/baseline_classifier.pkl` | Trained pickle artifact for category classifier |
| `saved_models/priority_predictor.pkl` | Trained pickle artifact for priority predictor |
