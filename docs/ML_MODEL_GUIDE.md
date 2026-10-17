# Machine Learning Model & Training Guide

## 1. Model Status & Benchmark Metrics

Dataset split: 815 train, 144 val, 144 test (80 samples per category per language across EN, HI, TA). Guaranteed zero text overlap between splits.

| Model / Stage | Architecture | Train Score | Val Score | Test Score | Status |
|---|---|---|---|---|---|
| **Complaint Classifier** | Dual TF-IDF (word 1-3gram + char 2-5gram) -> Soft-Voting Ensemble (LogisticRegression, CalibratedLinearSVC, SGDClassifier) | 1.000 Macro-F1 | 0.791 Macro-F1 | 1.000 Macro-F1 | Production Ready |
| **Priority Predictor** | Emergency Rules Safety-Net + CalibratedLinearSVC (char 2-4gram TF-IDF) | 0.834 Macro-F1 | N/A | 0.739 Macro-F1 | Trained Baseline |
| **Duplicate Detector** | SentenceTransformer (`paraphrase-multilingual-mpnet-base-v2`) / TF-IDF Cosine Fallback | 1.000 Self-Match | N/A | 0.295 Non-Dup Sim | Active Index (815 vectors) |
| **Language Fairness** | Audit across EN, HI, TA priority ratio disparity | N/A | N/A | 0.083 Disparity | Passed (< 0.15 limit) |

---

## 2. Pipeline Architecture

```
Input Text -> [Language Detector (Unicode Script + langdetect)]
           -> [Classifier Ensemble (Dual TF-IDF + Soft-Voting LR/SVC/SGD)] -> Category
           -> [Duplicate Detector (TF-IDF Cosine / MPNet)]                 -> Is Duplicate & Match
           -> [Priority Predictor (Rules + Calibrated SVC)]                 -> Priority & Rationale
           -> [Department Router & Explainer]                              -> Target Department
```

---

## 3. Retraining Commands

```bash
# Install dependencies
pip install scikit-learn scipy numpy langdetect

# Retrain all models from scratch and print test metrics
python train_models.py --regen
```

Key artifacts produced:
- `saved_models/baseline_classifier.pkl` (Classifier ensemble)
- `saved_models/priority_predictor.pkl` (Priority model)
- `data_store/train.json`, `val.json`, `test.json` (Dataset splits)

---

## 4. Technical Roadmap to Increase Accuracy

### A. Real-World Data Ingestion
- Current data in `data_generator.py` is synthetic.
- Replace synthetic samples with real citizen grievance datasets (e.g., CPGRAMS, municipal logs).
- Add code-mixed entries (Hinglish/Tanglish) to `TEMPLATES` in `data_generator.py`.

### B. Transformer Fine-Tuning (MuRIL / IndicBERT)
- Fine-tune `google/muril-base-cased` or `ai4bharat/indic-bert` on `data_store/train.json` using Hugging Face PyTorch:
  ```bash
  pip install torch transformers datasets
  ```
- Swap the model in `models/complaint_classifier.py`:
  ```python
  from transformers import AutoTokenizer, AutoModelForSequenceClassification
  tokenizer = AutoTokenizer.from_pretrained("google/muril-base-cased")
  model = AutoModelForSequenceClassification.from_pretrained("path/to/weights")
  ```

### C. Dense Vector Search (FAISS + SentenceTransformers)
- Install sentence-transformers to switch `models/duplicate_detector.py` from TF-IDF fallback to 768-dim dense cross-lingual embeddings:
  ```bash
  pip install sentence-transformers faiss-cpu
  ```

### D. Hyperparameter Tuning
- Tune `max_features` (currently 15k word / 20k char) and C regularization values in `models/complaint_classifier.py` and `models/priority_predictor.py` using `GridSearchCV`.

---

## 5. File Mapping

- `train_models.py`: Master CLI training & benchmark script.
- `pipeline.py`: Pipeline orchestrator.
- `models/complaint_classifier.py`: Dual TF-IDF + Soft-Voting classifier.
- `models/priority_predictor.py`: Hybrid rules + ML priority classifier.
- `models/duplicate_detector.py`: Vector similarity duplicate engine.
- `data_generator.py`: Synthetic dataset generator.
