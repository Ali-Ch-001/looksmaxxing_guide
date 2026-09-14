"""End-to-End Integration Tests for Evidence-Led SEO Content Engine."""

import pytest
from src.pipeline.orchestrator import EvidenceLedPipeline
from src.persistence.db import StateStore


@pytest.mark.asyncio
async def test_e2e_valid_topical_tretinoin():
    store = StateStore(":memory:")
    pipeline = EvidenceLedPipeline(store=store)

    state = await pipeline.run("topical tretinoin")
    assert state.audit_passed is True
    assert state.risk_category == "dermatology_trichology"
    assert state.draft is not None
    assert len(state.draft.citations) > 0
    assert len(state.draft.contraindications) > 0
    assert len(state.draft.actionable_protocol) > 0
    assert state.output_json_ld is not None
    assert state.output_cms_markdown is not None
    assert "application/ld+json" in state.output_cms_markdown


@pytest.mark.asyncio
async def test_e2e_valid_oral_minoxidil():
    store = StateStore(":memory:")
    pipeline = EvidenceLedPipeline(store=store)

    state = await pipeline.run("oral minoxidil")
    assert state.audit_passed is True
    assert state.risk_category == "dermatology_trichology"
    # Ensure dose is <= 2.5mg and NOT 10mg
    assert any("1.25 mg" in p for p in state.draft.actionable_protocol)
    assert not any("10 mg" in p for p in state.draft.actionable_protocol)


@pytest.mark.asyncio
async def test_e2e_banned_bone_smashing_halts_and_routes_to_crisis():
    store = StateStore(":memory:")
    pipeline = EvidenceLedPipeline(store=store)

    state = await pipeline.run("bone smashing for facial symmetry")
    assert state.audit_passed is False
    assert state.risk_category == "banned"
    assert state.is_crisis_routed is True
    assert state.draft is None
    assert state.output_cms_markdown is not None
    assert "Clinical Harm-Reduction Advisory" in state.output_cms_markdown
    assert "988" in state.output_cms_markdown
