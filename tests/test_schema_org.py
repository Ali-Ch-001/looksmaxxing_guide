"""Unit tests for Schema.org JSON-LD generation and validation."""

import pytest
from src.verification.schema_validator import SchemaValidator
from src.schemas.pipeline_state import ArticleDraft, FAQItem


def test_valid_schema_generation():
    draft = ArticleDraft(
        title="Clinical Guide to Oral Minoxidil: Protocols and Evidence",
        slug="oral-minoxidil-guide",
        target_kw="oral minoxidil",
        audience_demographic="Men 18-35",
        scientific_summary="Evidence summary regarding low-dose oral minoxidil.",
        actionable_protocol=["Take 1.25 mg daily [PMID:33675122]."],
        contraindications=["Severe heart failure"],
        citations=["PMID:33675122"],
        structured_faq=[
            FAQItem(
                question="What is the standard low-dose hair protocol?",
                answer="Clinical consensus supports 1.25 mg to 2.5 mg daily under physician supervision."
            )
        ]
    )

    passed, errors, json_ld = SchemaValidator.validate(draft)
    assert passed is True
    assert len(errors) == 0
    assert json_ld is not None
    assert json_ld["@context"] == "https://schema.org"
    assert "@graph" in json_ld
    assert len(json_ld["@graph"]) == 2  # MedicalWebPage and FAQPage


def test_invalid_schema_missing_faq():
    draft = ArticleDraft(
        title="Clinical Guide to Oral Minoxidil",
        slug="oral-minoxidil-guide",
        target_kw="oral minoxidil",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Take 1.25 mg daily."],
        contraindications=["Severe heart failure"],
        citations=["PMID:33675122"],
        structured_faq=[]  # Empty!
    )

    passed, errors, json_ld = SchemaValidator.validate(draft)
    assert passed is False
    assert any("FAQPage requires at least one" in err for err in errors)
