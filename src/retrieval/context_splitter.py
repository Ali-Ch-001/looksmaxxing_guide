"""Context Splitting & Disciplinary Namespace Isolation.

Isolates RAG collections and retrieval indexes by clinical discipline
(Dermatology/Trichology vs General Cardiology vs Orthodontics)
to permanently prevent context contamination from high-dose systemic literature.
"""

from typing import Dict, List, Set, Optional


class DisciplineNamespace:
    DERMATOLOGY_TRICHOLOGY = "dermatology_trichology"
    CARDIOLOGY_HYPERTENSION = "cardiology_hypertension"
    ORTHODONTICS = "orthodontics"
    FITNESS_NUTRITION = "fitness_nutrition"
    GENERAL = "general"


# Strict exclusionary keywords to prevent cardiology contamination in aesthetic queries
DISCIPLINE_EXCLUSIONS: Dict[str, List[str]] = {
    DisciplineNamespace.DERMATOLOGY_TRICHOLOGY: [
        "hypertensive emergency",
        "refractory hypertension",
        "antihypertensive",
        "essential hypertension",
        "blood pressure crisis",
        "pheochromocytoma crisis",
        "diuretic combination therapy for heart failure",
    ],
    DisciplineNamespace.ORTHODONTICS: [
        "bone smashing",
        "hammering",
        "lefort fracture trauma",
    ]
}


class ContextSplitter:
    """Enforces namespace boundaries and query sanitation for retrieval."""

    @staticmethod
    def resolve_namespace(topic: str) -> str:
        lowered = topic.lower()
        if any(w in lowered for w in ["hair", "scalp", "minoxidil", "finasteride", "dutasteride", "tretinoin", "skin", "acne", "retinoid", "wrinkle", "aging", "adapalene", "peel"]):
            return DisciplineNamespace.DERMATOLOGY_TRICHOLOGY
        elif any(w in lowered for w in ["teeth", "jaw", "palate", "mewing", "orthodontic", "occlusion"]):
            return DisciplineNamespace.ORTHODONTICS
        elif any(w in lowered for w in ["hypertension", "blood pressure", "cardiac"]):
            return DisciplineNamespace.CARDIOLOGY_HYPERTENSION
        elif any(w in lowered for w in ["posture", "muscle", "hypertrophy", "neck"]):
            return DisciplineNamespace.FITNESS_NUTRITION
        return DisciplineNamespace.GENERAL

    @classmethod
    def sanitize_query(cls, raw_query: str, target_namespace: str) -> str:
        """Appends boolean exclusionary filters to prevent context drift into off-target disciplines."""
        exclusions = DISCIPLINE_EXCLUSIONS.get(target_namespace, [])
        if not exclusions:
            return raw_query

        # In PubMed search syntax, add NOT clauses
        not_clause = " NOT (" + " OR ".join(f'"{exc}"[Title/Abstract]' for exc in exclusions[:3]) + ")"
        return f"({raw_query}) AND (dermatology OR trichology OR hair loss OR skin){not_clause}"

    @classmethod
    def filter_documents_for_namespace(cls, documents: List[Dict], namespace: str) -> List[Dict]:
        """Programmatically purges any retrieved chunks that belong to forbidden off-target disciplines."""
        clean_docs: List[Dict] = []
        forbidden_terms = DISCIPLINE_EXCLUSIONS.get(namespace, [])

        for doc in documents:
            doc_namespace = doc.get("discipline_namespace")
            # If doc has an explicit namespace, check it
            if doc_namespace and doc_namespace != namespace and doc_namespace != DisciplineNamespace.GENERAL:
                continue

            text = (doc.get("title", "") + " " + doc.get("snippet", "") + " " + doc.get("abstract", "")).lower()
            if any(term.lower() in text for term in forbidden_terms):
                # Dropping contaminated document
                continue
            clean_docs.append(doc)

        return clean_docs
