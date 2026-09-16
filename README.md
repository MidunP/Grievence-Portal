# Grievance Portal - AI Model Layer Architecture

A production-grade, multilingual AI model layer for citizen grievance systems supporting **English, Hindi, and Tamil** across 5 public administration categories:
1. **Water Supply & Quality**
2. **Sanitation & Garbage**
3. **Roads & Potholes**
4. **Electricity & Power Cut**
5. **Public Healthcare & Clinics**

---

## 🚀 Architecture Overview (9 Phases Built)

| Phase | Component | Technology / Implementation |
|-------|-----------|-----------------------------|
| **Phase 1** | **Data Foundation** | Multi-lingual synthetic dataset generator & `train/val/test` splitters for English, Hindi, and Tamil |
| **Phase 2** | **Language Detection** | `langdetect` + script Unicode heuristic fallbacks (Devanagari, Tamil, Latin, Code-mixed Hinglish/Tanglish) |
| **Phase 3** | **Complaint Classification** | Baseline Naive Bayes / TF-IDF + Logistic Regression & Hugging Face MuRIL / IndicBERT fine-tuning pipeline |
| **Phase 4** | **Duplicate Detection** | Multilingual sentence embeddings (`paraphrase-multilingual-mpnet-base-v2`) with vector similarity thresholding (0.85) |
| **Phase 5** | **Priority Prediction** | Hybrid urgency rule engine + ML classifier predicting **Critical, High, Medium, Low** with language bias auditing |
| **Phase 6** | **Department Routing** | Category & SLA-based direct routing to target government departments |
| **Phase 7** | **Explainability** | Diagnostic term extraction & confidence explanations for citizen & administrative auditing |
| **Phase 8** | **API Integration** | Standardized FastAPI microservice with endpoints (`/detect-language`, `/classify`, `/duplicate-check`, `/priority`, `/route`, `/process-grievance`) |
| **Phase 9** | **Evaluation & Fairness** | STAR research evaluation suite evaluating Accuracy, Macro-F1, Routing Accuracy, and Language Disparity |

---

## 📁 Repository Structure

```
c:\Users\Midun\Documents\Grievance Portal\
├── config.py                   # Central settings, categories, departments, language definitions
├── data_generator.py           # Phase 1: Dataset generation & train/val/test split
├── pipeline.py                 # Integrated Master AI Pipeline orchestrator
├── api.py                      # Phase 8: FastAPI endpoints wrapper
├── evaluate.py                 # Phase 9: Evaluation & fairness audit benchmark
├── requirements.txt            # System dependencies
└── models/
    ├── language_detector.py    # Phase 2: Multilingual language detector
    ├── complaint_classifier.py # Phase 3: Baseline & transformer classifier
    ├── duplicate_detector.py   # Phase 4: Vector similarity & duplicate matching
    ├── priority_predictor.py   # Phase 5: Priority prediction & fairness audit
    ├── department_router.py    # Phase 6: Department routing table & SLA solver
    └── explainer.py            # Phase 7: Explainability engine
```

---

## 🛠️ Quick Start & Execution

### 1. Run Data Generation & Train/Val/Test Split (Phase 1)
```bash
python data_generator.py
```

### 2. Run Language Detector Test (Phase 2)
```bash
python models/language_detector.py
```

### 3. Train & Evaluate Classification Baseline (Phase 3)
```bash
python -m models.complaint_classifier
```

### 4. Run Vector Duplicate Detection Check (Phase 4)
```bash
python -m models.duplicate_detector
```

### 5. Run Priority Prediction & Fairness Audit (Phase 5)
```bash
python -m models.priority_predictor
```

### 6. Run Integrated End-to-End Master Pipeline
```bash
python pipeline.py
```

### 7. Run Research Evaluation Suite (Phase 9 STAR Metrics)
```bash
python evaluate.py
```

### 8. Start FastAPI Server (Phase 8)
```bash
uvicorn api:app --reload --port 8000
```

---

## 📊 Sample API Response (`/process-grievance`)

```json
{
  "input_text": "वार्ड नंबर 10 में पानी की पाइपलाइन फट गई है और गंदा पानी सड़कों पर बह रहा है।",
  "language_detection": {
    "language": "hi",
    "confidence": 0.99,
    "method": "langdetect"
  },
  "classification": {
    "predicted_category": "Water Supply & Quality",
    "confidence": 0.98
  },
  "duplicate_check": {
    "is_duplicate": false,
    "similarity_score": 0.42
  },
  "priority": {
    "priority": "Critical",
    "confidence": 0.95,
    "reason": "Triggered critical hazard/emergency keywords (पानी की पाइपलाइन फट गई)"
  },
  "routing": {
    "target_department": "Department of Water Resources & Sanitation",
    "sla_target_hours": 24
  },
  "explanation": {
    "summary": "Grievance classified as 'Water Supply & Quality' with 98.0% confidence. Assigned priority 'Critical' (Triggered critical hazard/emergency keywords). Routed to 'Department of Water Resources & Sanitation'.",
    "key_diagnostic_terms": ["पानी", "पाइपलाइन", "गंदा"]
  }
}
```

---

## 🎯 Fairness & Research Metrics
The system explicitly measures language disparity across English, Hindi, and Tamil test sets to ensure fair priority allocation and equal macro-F1 accuracy across all demographic segments.
