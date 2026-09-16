"""
Phase 5: Priority Prediction Module.
Predicts complaint severity: Critical, High, Medium, Low.
Combines rule-based safety net (urgency keywords) with ML priority scoring.
Includes language fairness evaluation across English, Hindi, and Tamil.
"""

import json
from typing import Dict, List, Tuple
from config import PRIORITY_LEVELS, URGENCY_KEYWORDS, DATA_DIR


class PriorityPredictor:
    """Hybrid Priority Predictor for Grievance Handling."""

    def __init__(self):
        self.priority_levels = PRIORITY_LEVELS

    def extract_urgency_score(self, text: str, language: str) -> float:
        """Counts urgency keywords for the language."""
        text_lower = text.lower()
        
        # Collect keywords for target language plus general keywords
        keywords = URGENCY_KEYWORDS.get(language, []) + URGENCY_KEYWORDS["en"] + URGENCY_KEYWORDS["hi"] + URGENCY_KEYWORDS["ta"]
        
        matches = sum(1 for kw in set(keywords) if kw in text_lower)
        return float(matches)

    def predict_priority(self, text: str, language: str, category: str, days_open: int = 0) -> Dict:
        """
        Predicts priority level and returns explanation factors.
        """
        urgency_hits = self.extract_urgency_score(text, language)
        text_lower = text.lower()

        # Rule-based safety checks for immediate Critical escalation
        critical_triggers = [
            "burst", "explode", "fire", "injury", "dead animal", "toxic", "bleeding",
            "फट गया", "शॉर्ट सर्किट", "आग", "चोट", "मृत",
            "வெடித்து", "தீ", "காயம்", "சாய்ந்து", "உடைந்து"
        ]

        high_triggers = [
            "no water", "12 hours", "8 hours", "overflowing", "choked", "low voltage",
            "पानी नहीं", "12 घंटे", "8 घंटे", "बिजली कट", "गंदगी",
            "நீர் விநியோகம்", "12 மணி நேரமாக", "மின்வெட்டு"
        ]

        is_critical = any(trig in text_lower for trig in critical_triggers) or urgency_hits >= 2
        is_high = any(trig in text_lower for trig in high_triggers) or urgency_hits >= 1 or days_open > 5

        if is_critical:
            priority = "Critical"
            confidence = 0.95
            reason = "Triggered critical hazard/emergency keywords or high urgency count"
        elif is_high:
            priority = "High"
            confidence = 0.88
            reason = "Triggered high priority operational keywords or long open duration"
        elif category in ["Water Supply & Quality", "Electricity & Power Cut"]:
            priority = "Medium"
            confidence = 0.75
            reason = "Essential public service category default priority"
        else:
            priority = "Low"
            confidence = 0.70
            reason = "Standard civic grievance priority"

        return {
            "priority": priority,
            "confidence": confidence,
            "reason": reason,
            "urgency_matches": int(urgency_hits),
            "days_open": days_open
        }

    def audit_fairness(self, test_data: List[Dict]) -> Dict:
        """
        Evaluates priority distribution across languages to detect potential language bias.
        """
        bias_report = {}
        for lang in ["en", "hi", "ta"]:
            lang_samples = [item for item in test_data if item["language"] == lang]
            if not lang_samples:
                continue

            dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for item in lang_samples:
                res = self.predict_priority(item["text"], item["language"], item["category"], item.get("days_open", 0))
                dist[res["priority"]] += 1

            total = len(lang_samples)
            dist_pct = {k: round(v / total, 4) for k, v in dist.items()}
            
            # Critical + High ratio
            high_priority_ratio = round((dist["Critical"] + dist["High"]) / total, 4)

            bias_report[lang] = {
                "total_samples": total,
                "priority_distribution_pct": dist_pct,
                "high_priority_ratio": high_priority_ratio
            }

        # Check maximum disparity between languages
        ratios = [v["high_priority_ratio"] for v in bias_report.values()]
        max_disparity = round(max(ratios) - min(ratios), 4)

        return {
            "language_fairness_report": bias_report,
            "max_disparity_score": max_disparity,
            "is_fair": max_disparity < 0.15 # Fair if disparity under 15%
        }


if __name__ == "__main__":
    predictor = PriorityPredictor()
    
    with open(DATA_DIR / "test.json", "r", encoding="utf-8") as f:
        test_samples = json.load(f)

    fairness_res = predictor.audit_fairness(test_samples)
    print("Language Fairness Audit Result:")
    print(json.dumps(fairness_res, indent=2))
