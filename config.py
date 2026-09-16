"""
Configuration settings for Grievance AI System.
Defines supported languages, categories, departments, priority levels, and model constants.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data_store"
MODELS_DIR = BASE_DIR / "saved_models"

DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Supported Languages & Categories
LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil"
}

CATEGORIES = [
    "Water Supply & Quality",
    "Sanitation & Garbage",
    "Roads & Potholes",
    "Electricity & Power Cut",
    "Public Healthcare & Clinics"
]

DEPARTMENTS = {
    "Water Supply & Quality": "Department of Water Resources & Sanitation",
    "Sanitation & Garbage": "Municipal Solid Waste Management Department",
    "Roads & Potholes": "Public Works Department (PWD) - Roads Division",
    "Electricity & Power Cut": "State Electricity Distribution Corporation",
    "Public Healthcare & Clinics": "Department of Health & Family Welfare"
}

PRIORITY_LEVELS = ["Critical", "High", "Medium", "Low"]

# High priority urgency keywords across languages
URGENCY_KEYWORDS = {
    "en": ["leak", "fire", "injury", "danger", "burst", "sewage overflow", "hazard", "outage", "toxic", "contaminated"],
    "hi": ["रिसाव", "आग", "चोट", "खतरा", "पानी का रिसाव", "सीवर भर गया", "विषैला", "बिजली कट", "अस्पताल में आपातकाल"],
    "ta": ["கசிவு", "தீ", "காயம்", "ஆபத்து", "சாக்கடை பெருக்கு", "மின்வெட்டு", "நச்சு", "அவசரம்", "விபத்து"]
}

# Model Specifications
TRANSFORMER_MODELS = {
    "muril": "google/muril-base-cased",
    "indicbert": "ai4bharat/indic-bert",
    "sentence_embeddings": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
}

# Thresholds
DUPLICATE_SIMILARITY_THRESHOLD = 0.85
