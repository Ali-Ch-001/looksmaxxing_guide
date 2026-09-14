"""Comprehensive Adversarial Vulnerability Regression Suite.

Verifies fixes for the critical holes identified during the deep architectural audit:
1. Written English numbers ("ten mg", "twenty milligrams") bypass prevention
2. Full unit name ("milligrams", "micrograms", "percent") bypass prevention
3. Medical Latin and dynamic interval frequencies ("q6h", "every 6 hours", "4x daily")
4. Obfuscated and spaced subculture tropes in post-drafting gate ("b o n e   s m a s h i n g")
5. False positive citation grounding rejection on benign step numbers and treatment durations
6. False negative citation grounding rejection on ungrounded dosages matching cohort numbers
"""

import pytest
from src.safety.dosage_checker import DeterministicDosageEngine, extract_frequency_multiplier
from src.verification.toxic_detector import ToxicSlangDetector
from src.verification.citation_verifier import CitationGroundingVerifier
from src.schemas.pipeline_state import PipelineState, ArticleDraft, FAQItem


def test_written_word_numbers_intercepted():
    """Confirms 'ten mg' oral minoxidil is caught by dosage engine."""
    passed, violations, _ = DeterministicDosageEngine.verify_protocols(
        ["Administer ten mg oral minoxidil daily for alopecia."],
        default_compound="oral minoxidil"
    )
    assert passed is False
    assert any("exceeds absolute safety ceiling" in v for v in violations)


def test_full_unit_name_intercepted():
    """Confirms '10 milligrams' oral minoxidil is caught by dosage engine."""
    passed, violations, _ = DeterministicDosageEngine.verify_protocols(
        ["Administer 10 milligrams of oral minoxidil daily."],
        default_compound="oral minoxidil"
    )
    assert passed is False
    assert any("exceeds absolute safety ceiling" in v for v in violations)


def test_dynamic_frequency_multipliers():
    """Confirms q6h, q4h, and every 6 hours calculate daily cumulative doses correctly."""
    assert extract_frequency_multiplier("Take 2.5 mg every 6 hours") == 4.0
    assert extract_frequency_multiplier("Take 2.5 mg q6h") == 4.0
    assert extract_frequency_multiplier("Take 2.5 mg q4h") == 6.0
    assert extract_frequency_multiplier("Take 2.5 mg 4 times daily") == 4.0

    # 2.5mg q6h = 10mg daily -> must fail oral minoxidil (ceiling is 5.0mg)
    passed, violations, _ = DeterministicDosageEngine.verify_protocols(
        ["Administer 2.5 mg oral minoxidil q6h."],
        default_compound="oral minoxidil"
    )
    assert passed is False
    assert any("CRITICAL FREQUENCY OVERDOSE" in v or "exceeds" in v for v in violations)


def test_spaced_banned_practice_in_draft_detected():
    """Confirms spaced letters 'b o n e   s m a s h i n g' in draft are caught by ToxicSlangDetector."""
    draft = ArticleDraft(
        title="Clinical Guide to Facial Aesthetics",
        slug="guide",
        target_kw="facial aesthetics",
        scientific_summary="Evidence appraisal.",
        actionable_protocol=["Try b o n e   s m a s h i n g on jawline daily."],
        contraindications=["None"],
        citations=["PMID:31256594"],
        structured_faq=[FAQItem(question="Is this safe?", answer="No")]
    )
    passed, violations = ToxicSlangDetector.scan(draft)
    assert passed is False
    assert any("bone smashing" in v.lower() for v in violations)


def test_procedural_numbers_and_durations_do_not_cause_false_rejection():
    """Confirms 'Step 3' and '6 months' are not falsely flagged as ungrounded drug quantities."""
    draft = ArticleDraft(
        title="Clinical Guide to Tretinoin",
        slug="tretinoin-guide",
        target_kw="tretinoin",
        scientific_summary="Summary of evidence.",
        actionable_protocol=["Step 3: Apply 0.025% tretinoin cream for 6 months [PMID:31256594]."],
        contraindications=["Pregnancy"],
        citations=["PMID:31256594"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes at 0.025% concentration.")]
    )
    state = PipelineState(
        raw_topic="tretinoin",
        retrieved_papers=[{
            "id": "PMID:31256594",
            "title": "Topical Tretinoin in Photoaging and Acne",
            "abstract": "Topical tretinoin 0.025% is effective.",
            "snippet": "0.025% works.",
            "standard_dosage": 0.025
        }],
        draft=draft
    )
    passed, unverified, errors = CitationGroundingVerifier.verify(state)
    assert passed is True
    assert len(errors) == 0


def test_false_number_grounding_against_patient_counts_rejected():
    """Confirms '20 mg' is rejected when abstract only contains '20 patients' with no mass unit."""
    draft = ArticleDraft(
        title="Clinical Guide to Minoxidil",
        slug="minoxidil-guide",
        target_kw="minoxidil",
        scientific_summary="Summary of evidence.",
        actionable_protocol=["Administer 20 mg daily [PMID:33675122]."],
        contraindications=["Heart disease"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(
        raw_topic="minoxidil",
        retrieved_papers=[{
            "id": "PMID:33675122",
            "title": "Study published in 2020",
            "abstract": "We evaluated 20 patients in this trial.",
            "snippet": "20 patients evaluated.",
            "standard_dosage": 1.25
        }],
        draft=draft
    )
    passed, unverified, errors = CitationGroundingVerifier.verify(state)
    assert passed is False
    assert any("FACTUAL ASSERTION DRIFT" in err for err in errors)
