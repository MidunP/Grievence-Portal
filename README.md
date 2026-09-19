# JanSeva Grievance Portal — AI-Powered Triage & Resolution System

A full-stack, multilingual AI grievance triage system supporting **English, Hindi, and Tamil** across 5 public administration categories:
1. **Water Supply & Quality**
2. **Sanitation & Garbage**
3. **Roads & Potholes**
4. **Electricity & Power Cut**
5. **Public Healthcare & Clinics**

---

## 🏛️ System Architecture

The project employs a hybrid Node.js + Python architecture designed for low-latency operational execution:

```
                  ┌────────────────────────────────────────┐
                  │   Browser Frontend (Vanilla JS + CSS)  │
                  │        public/index.html & app.js      │
                  └──────────────────┬─────────────────────┘
                                     │ REST APIs
                                     ▼
                  ┌────────────────────────────────────────┐
                  │    Canonical Express Backend Server    │
                  │               server.js                │
                  └──────────────────┬─────────────────────┘
                                     │ Subprocess Call (stdin/stdout)
                                     ▼
                  ┌────────────────────────────────────────┐
                  │        Python AI Pipeline Bridge       │
                  │          run_pipeline_bridge.py        │
                  └──────────────────┬─────────────────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────────┐
                  │      Master 9-Phase AI Orchestrator    │
                  │              pipeline.py               │
                  └────────────────────────────────────────┘
```

> **Note on Backend Reconciliation:**  
> The production entry point is `server.js` (Express on Port 3000). The `api_standalone_reference.py` file is a standalone FastAPI harness reserved for direct model testing and is NOT part of the production Web application flow.

---

## 🧩 9-Phase AI Pipeline

| Phase | Component | Active Implementation & Fallback Mechanics |
|-------|-----------|--------------------------------------------|
| **Phase 1** | **Data Foundation** | Synthetic generator (`data_generator.py`) with guaranteed zero train/val/test text leakage. |
| **Phase 2** | **Language Detection** | Script-based Unicode heuristics (Devanagari, Tamil, Latin) + `langdetect` fallback. |
| **Phase 3** | **Complaint Classification** | Baseline Pure Python Naive Bayes / TF-IDF + Logistic Regression fallback. |
| **Phase 4** | **Duplicate Detection** | Vector similarity using hybrid word+character 3-gram vectorizer (or `sentence-transformers`). |
| **Phase 5** | **Priority Prediction** | Urgency keyword rule engine + fairness auditor (**Critical, High, Medium, Low**). |
| **Phase 6** | **Department Routing** | Direct SLA and category mapping to responsible municipal departments. |
| **Phase 7** | **Explainability** | Diagnostic term extractor & confidence rationale generator. |
| **Phase 8** | **Integration Bridge** | Express JSON bridge (`run_pipeline_bridge.py`) for sub-second CLI invocation. |
| **Phase 9** | **Evaluation & Auditing** | STAR suite (`evaluate.py`) evaluating Accuracy, Macro-F1, and Language Bias. |

---

## 📂 Repository Structure

```
Grievance Portal/
├── config.py                     # Central configuration & department mappings
├── data_generator.py             # Synthetic dataset generator (leakage-safe split)
├── pipeline.py                   # Master AI Pipeline orchestrator
├── run_pipeline_bridge.py        # Express-to-Python JSON bridge script
├── server.js                     # Canonical Express REST backend server
├── api_standalone_reference.py   # Standalone FastAPI ML test harness
├── evaluate.py                   # Comprehensive STAR evaluation suite
├── test_e2e.py                   # Automated E2E integration test suite
├── requirements.txt              # System dependencies
├── data_store/
│   ├── grievances_db.json        # File-backed ticket database (with write-mutex guard)
│   ├── train.json                # Model training set
│   ├── val.json                  # Validation set
│   └── test.json                 # Uncontaminated test set
├── public/                       # Frontend SPA (HTML5, Vanilla CSS, JS, Chart.js)
│   ├── index.html
│   ├── app.js
│   └── style.css
└── models/                       # Modular ML pipeline stages
    ├── language_detector.py
    ├── complaint_classifier.py
    ├── duplicate_detector.py
    ├── priority_predictor.py
    ├── department_router.py
    └── explainer.py
```

---

## ⚡ Quick Start & Running the Application

### 1. Start the Production Server
```bash
node server.js
```
Open **`http://localhost:3000`** in your browser.

### 2. Run Data Generation & Clean Split (Phase 1)
```bash
python data_generator.py
```

### 3. Run Pipeline Diagnostics & Evaluation (Phase 9)
```bash
python evaluate.py
```

### 4. Run Automated End-to-End Integration Tests
Ensure `node server.js` is running, then in a separate terminal execute:
```bash
python test_e2e.py
```

---

## 🔒 Concurrency & Data Safety

The server includes a Promise-based **write-mutex lock (`withWriteLock`)** on `data_store/grievances_db.json`. This guarantees atomic read/write operations during high-concurrency ticket submissions and prevents JSON corruption.

---

## 🎯 Verification & Audit Summary

- **Backend Unified**: Single canonical backend (`server.js`).
- **Data Leakage Eliminated**: Verified 0 text-level overlap between train, val, and test splits.
- **Robust Fallbacks**: Pipeline runs seamlessly under minimal Python environments (numpy-only fallback mode supported).
- **Automated Testing**: 100% passing E2E suite covering validation, processing, duplicate flagging, admin updates, and analytics.
