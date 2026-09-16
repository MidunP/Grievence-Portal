"""
Phase 6: Department Routing Engine.
Routes grievances to correct municipal & state government departments based on category and text signals.
"""

from typing import Dict
from config import DEPARTMENTS


class DepartmentRouter:
    """Department Routing System for Grievances."""

    def __init__(self):
        self.mapping = DEPARTMENTS

    def route_complaint(self, category: str, text: str = "") -> Dict[str, str]:
        """Routes complaint to primary department and SLA timeframe."""
        department = self.mapping.get(category, "General Municipal Administration")
        
        # Estimate SLA based on category
        sla_hours = {
            "Electricity & Power Cut": 12,
            "Water Supply & Quality": 24,
            "Sanitation & Garbage": 48,
            "Public Healthcare & Clinics": 6,
            "Roads & Potholes": 72
        }.get(category, 48)

        return {
            "target_department": department,
            "category": category,
            "sla_target_hours": sla_hours
        }


if __name__ == "__main__":
    router = DepartmentRouter()
    print(router.route_complaint("Water Supply & Quality"))
