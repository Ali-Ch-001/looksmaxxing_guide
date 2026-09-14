"""Unit tests for Citation Grounding Verifier."""

import pytest
from src.verification.citation_verifier import CitationGroundingVerifier
from src.schemas.pipeline_state import PipelineState, ArticleDraft, FAQItem


def test_valid_citation_grounding():
    retrieved = [
        {"id": "PMID:31256594", "title": "Tretinoin Study"},
        {"id": "PMID:30138542", "title": "Sunscreen Study"}
    ]
    draft = ArticleDraft(
        title="Clinical Guide to Tretinoin",
        slug="tretinoin-guide",
        target_kw="tretinoin",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Apply 0.025% tretinoin [PMID:31256594]."],
        contraindications=["Pregnancy"],
        citations=["PMID:31256594"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(raw_topic="tretinoin", retrieved_papers=retrieved, draft=draft)

    passed, unverified, errors = CitationGroundingVerifier.verify(state)
    assert passed is True
    assert len(unverified) == 0
    assert len(errors) == 0


def test_hallucinated_pmid_rejection():
    retrieved = [{"id": "PMID:31256594", "title": "Tretinoin Study"}]
    draft = ArticleDraft(
        title="Clinical Guide to Tretinoin",
        slug="tretinoin-guide",
        target_kw="tretinoin",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Apply 0.025% tretinoin [PMID:99999999]."],
        contraindications=["Pregnancy"],
        citations=["PMID:99999999"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(raw_topic="tretinoin", retrieved_papers=retrieved, draft=draft)

    passed, unverified, errors = CitationGroundingVerifier.verify(state)
    assert passed is False
    assert "PMID:99999999" in unverified
    assert len(errors) > 0


def test_zero_citation_density_rejection():
    retrieved = [{"id": "PMID:31256594", "title": "Tretinoin Study"}]
    draft = ArticleDraft(
        title="Clinical Guide to Tretinoin",
        slug="tretinoin-guide",
        target_kw="tretinoin",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Apply 0.025% tretinoin without any citation."],
        contraindications=["Pregnancy"],
        citations=[],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(raw_topic="tretinoin", retrieved_papers=retrieved, draft=draft)

    passed, unverified, errors = CitationGroundingVerifier.verify(state)
    assert passed is False
    assert any("ZERO CITATION DENSITY" in err for err in errors)
