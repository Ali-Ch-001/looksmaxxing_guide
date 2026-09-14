"""Unit tests for the Critique/Repair loop in the verification gate."""

import pytest
import asyncio
from src.verification.gate_engine import DeterministicVerificationGate
from src.schemas.pipeline_state import PipelineState, ArticleDraft, FAQItem


@pytest.mark.asyncio
async def test_repair_loop_fixes_soft_citation_defect():
    """Checks that an ungrounded extra citation is stripped during auto-repair."""
    retrieved = [{"id": "PMID:31256594", "title": "Verified Tretinoin"}]
    # Draft includes a valid citation AND an unverified extra citation
    draft = ArticleDraft(
        title="Clinical Guide to Tretinoin Formulations",
        slug="tretinoin-guide",
        target_kw="tretinoin",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Apply 0.025% tretinoin [PMID:31256594]."],
        contraindications=["Pregnancy"],
        citations=["PMID:31256594", "PMID:99999999"],  # 99999999 is ungrounded
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes at 0.025% concentration.")]
    )
    state = PipelineState(
        raw_topic="tretinoin",
        retrieved_papers=retrieved,
        draft=draft
    )

    result_state = await DeterministicVerificationGate.evaluate_and_repair_loop(state)
    assert result_state.audit_passed is True
    assert "PMID:99999999" not in result_state.draft.citations
    assert "PMID:31256594" in result_state.draft.citations
    assert result_state.repair_attempts > 0


@pytest.mark.asyncio
async def test_repair_loop_halts_immediately_on_hard_dosage_violation():
    """Confirms that hard dosage violations halt without attempting auto-repair."""
    retrieved = [{"id": "PMID:33675122", "title": "Minoxidil"}]
    draft = ArticleDraft(
        title="Clinical Guide to Minoxidil",
        slug="minoxidil-guide",
        target_kw="oral minoxidil",
        scientific_summary="Evidence summary.",
        actionable_protocol=["Take 10 mg oral minoxidil daily [PMID:33675122]."],
        contraindications=["Heart failure"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(
        raw_topic="oral minoxidil",
        retrieved_papers=retrieved,
        draft=draft
    )

    result_state = await DeterministicVerificationGate.evaluate_and_repair_loop(state)
    assert result_state.audit_passed is False
    assert result_state.repair_attempts == 0  # No repair attempted on hard violations
    assert "UNRECOVERABLE AUDIT FAILURE" in result_state.rejection_reason
