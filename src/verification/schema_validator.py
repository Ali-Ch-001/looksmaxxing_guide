"""Schema.org JSON-LD Validator for Answer Engine Readiness."""

from typing import Tuple, List, Dict, Any, Optional
from src.schemas.pipeline_state import ArticleDraft
from src.schemas.schema_org import MedicalWebPageSchema, FAQPageSchema


class SchemaValidator:
    """Validates structural and semantic compliance with Schema.org standards."""

    @staticmethod
    def validate(draft: ArticleDraft) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
        errors: List[str] = []

        if not draft.title or len(draft.title) < 10:
            errors.append("Schema Error: Title must be at least 10 characters.")
        if not draft.slug:
            errors.append("Schema Error: Slug is required.")
        if not draft.contraindications:
            errors.append("Schema Error: MedicalWebPage requires explicit contraindications.")
        if not draft.citations:
            errors.append("Schema Error: MedicalWebPage requires explicit citations.")
        if not draft.structured_faq:
            errors.append("Schema Error: FAQPage requires at least one Question/Answer pair.")
        else:
            for idx, item in enumerate(draft.structured_faq):
                if not item.question or len(item.question.strip()) < 5:
                    errors.append(f"Schema Error: FAQ item #{idx+1} has invalid question.")
                if not item.answer or len(item.answer.strip()) < 10:
                    errors.append(f"Schema Error: FAQ item #{idx+1} has incomplete answer.")

        if errors:
            return False, errors, None

        # Build schema objects
        medical_page = MedicalWebPageSchema(
            headline=draft.title,
            url=f"https://evidence.looksmaxxing.guide/protocols/{draft.slug}",
            description=draft.scientific_summary,
            medicalAudience=draft.audience_demographic,
            contraindication=draft.contraindications,
            citation=draft.citations,
            about=[{"@type": "MedicalCondition", "name": draft.target_kw}]
        )

        faq_items = [{"question": f.question, "answer": f.answer} for f in draft.structured_faq]
        faq_page = FAQPageSchema.from_items(faq_items)

        compiled_json_ld = {
            "@context": "https://schema.org",
            "@graph": [
                medical_page.to_json_ld(),
                faq_page.to_json_ld()
            ]
        }

        return True, [], compiled_json_ld
