"""Treatment Engine — recommendations and treatment ranking."""
from backend.app.bse.adapters import legacy


class TreatmentEngine:
    @staticmethod
    def recommend(audit_answers: dict) -> dict | None:
        return legacy.compute_recommendation(audit_answers)