"""
Phase 7: Explainability Engine.
Generates human-readable, auditable explanations for classification and priority decisions.
"""

import re
from typing import Dict, List
from config import URGENCY_KEYWORDS


class GrievanceExplainer:
    """Generates transparency explanations for model decisions."""

    @staticmethod
    def extract_key_terms(text: str, language: str) -> List[str]:
        """Extracts top diagnostic terms from grievance text."""
        words = re.findall(r'\w+', text.lower())
        
        # Priority urgency keywords
        urgency_kws = set(URGENCY_KEYWORDS.get(language, []) + URGENCY_KEYWORDS["en"] + URGENCY_KEYWORDS["hi"] + URGENCY_KEYWORDS["ta"])
        found_urgency = [w for w in words if w in urgency_kws]

        # Domain terms
        domain_terms = {
            "water", "pipeline", "tap", "sewage", "garbage", "waste", "road", "pothole",
            "transformer", "electricity", "power", "hospital", "clinic", "doctor",
            "पानी", "कचरा", "नाली", "सड़क", "बिजली", "अस्पताल",
            "தண்ணீர்", "குப்பை", "சாக்கடை", "சாலை", "மின்சாரம்", "மருத்துவமனை"
        }
        found_domain = [w for w in words if w in domain_terms]

        # Combine unique terms
        key_terms = list(dict.fromkeys(found_urgency + found_domain))
        if not key_terms:
            key_terms = words[:4] # Fallback to first 4 words

        return key_terms

    def format_explanation(
        self,
        text: str,
        language: str,
        category_res: Dict,
        priority_res: Dict,
        routing_res: Dict
    ) -> Dict:
        """Formats comprehensive explanation dictionary."""
        key_terms = self.extract_key_terms(text, language)

        cat_name = category_res["predicted_category"]
        cat_conf = category_res["confidence"]
        prio_name = priority_res["priority"]
        prio_reason = priority_res["reason"]
        dept_name = routing_res["target_department"]

        summary_template = (
            f"Grievance classified as '{cat_name}' with {round(cat_conf * 100, 1)}% confidence. "
            f"Assigned priority '{prio_name}' ({prio_reason}). "
            f"Routed to '{dept_name}'."
        )

        return {
            "summary": summary_template,
            "key_diagnostic_terms": key_terms,
            "category_confidence": cat_conf,
            "priority_explanation": prio_reason,
            "target_department": dept_name
        }


if __name__ == "__main__":
    explainer = GrievanceExplainer()
    sample_text = "Main water pipeline burst near Church Street crossing."
    ex = explainer.format_explanation(
        text=sample_text,
        language="en",
        category_res={"predicted_category": "Water Supply & Quality", "confidence": 0.98},
        priority_res={"priority": "Critical", "reason": "Hazard keyword 'burst' detected"},
        routing_res={"target_department": "Department of Water Resources & Sanitation"}
    )
    print("Formatted Explanation:")
    print(ex["summary"])
    print("Key Terms:", ex["key_diagnostic_terms"])
