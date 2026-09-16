"""
Phase 2: Language Detection Module.
Provides fast, accurate detection for English (en), Hindi (hi), Tamil (ta), and code-mixed inputs.
Combines langdetect / fasttext with script unicode range fallbacks.
"""

import re
from typing import Dict

try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


def detect_script_heuristic(text: str) -> str:
    """Fallback script detector using Unicode ranges."""
    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text)) # Hindi
    tamil_count = len(re.findall(r'[\u0B80-\u0BFF]', text))      # Tamil
    latin_count = len(re.findall(r'[a-zA-Z]', text))           # English

    total_chars = max(len(text.strip()), 1)

    if tamil_count / total_chars > 0.15:
        return "ta"
    elif devanagari_count / total_chars > 0.15:
        return "hi"
    elif latin_count / total_chars > 0.2:
        # Check for Hinglish / Tanglish code-mixing keywords
        hinglish_kw = ["pani", "kachra", "sadak", "bijli", "gadda", "nahi", "kar"]
        tanglish_kw = ["thanneer", "kuppai", "roadu", "current", "ille", "seri"]
        
        text_lower = text.lower()
        if any(w in text_lower for w in hinglish_kw):
            return "en-hi" # Code-mixed Hinglish
        if any(w in text_lower for w in tanglish_kw):
            return "en-ta" # Code-mixed Tanglish
            
        return "en"
    
    return "en"


def detect_language(text: str) -> Dict[str, str]:
    """
    Detects language of input grievance.
    Returns language code, confidence estimate, and method used.
    """
    if not text or not text.strip():
        return {"language": "en", "confidence": 0.50, "method": "default_empty"}

    if LANGDETECT_AVAILABLE:
        try:
            predictions = detect_langs(text)
            top_pred = predictions[0]
            lang_code = top_pred.lang
            confidence = round(top_pred.prob, 4)

            # Map langdetect output to supported set (en, hi, ta)
            if lang_code in ["hi", "ta", "en"]:
                return {
                    "language": lang_code,
                    "confidence": float(confidence),
                    "method": "langdetect"
                }
        except Exception:
            pass

    # Script heuristic fallback
    detected_lang = detect_script_heuristic(text)
    return {
        "language": detected_lang,
        "confidence": 0.90 if detected_lang in ["hi", "ta", "en"] else 0.75,
        "method": "script_heuristic"
    }


if __name__ == "__main__":
    test_cases = [
        "Main water pipeline burst near Church Street.",
        "वार्ड नंबर 12 में पानी नहीं आ रहा है।",
        "வார்டு 5 பகுதியில் சாக்கடை நீர் வழிகிறது.",
        "Pani nahi aa raha hai station road pe",
        "Kuppai lorry varala"
    ]
    
    for case in test_cases:
        res = detect_language(case)
        print(f"Text: '{case[:40]}...' -> Detected: {res['language']} ({res['method']}, conf: {res['confidence']})")
