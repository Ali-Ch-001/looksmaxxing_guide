"""Comprehensive Verification Suite for Roadmap AI Agent Enhancements.

Tests the 4 strategic roadmap capabilities:
1. Hybrid Deterministic/Semantic Verifier with Chain-of-Thought (CoT)
2. Targeted Programmatic Repair Loop using AST violation diff feedback
3. Dynamic MeSH Query Expansion for autonomous PubMed retrieval refinement
4. Cache Invalidation on Guideline Updates via CLINICAL_DICTIONARY fingerprinting
"""

import pytest
from src.verification.hybrid_critic import HybridClinicalCritic
from src.verification.gate_engine import DeterministicVerificationGate
from src.retrieval.mesh_expander import MeSHQueryExpander
from src.safety.clinical_dictionary import get_dictionary_fingerprint, CLINICAL_DICTIONARY
from src.persistence.state_graph import compute_idempotency_key, StateGraphManager
from src.persistence.db import StateStore
from src.schemas.pipeline_state import PipelineState, ArticleDraft, FAQItem


# ==============================================================================
# Roadmap 1: Hybrid Deterministic/Semantic Verifier with Chain-of-Thought (CoT)
# ==============================================================================

def test_roadmap_1_hybrid_critic_detects_missing_sunscreen():
    """Confirms semantic critic catches retinoid photosensitization without SPF."""
    critic = HybridClinicalCritic()
    draft = ArticleDraft(
        title="Clinical Tretinoin Protocol",
        slug="tretinoin-test",
        target_kw="tretinoin",
        scientific_summary="Summary.",
        actionable_protocol=["Apply 0.025% tretinoin cream nightly [PMID:31256594]."],
        contraindications=["Pregnancy"],
        citations=["PMID:31256594"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(raw_topic="tretinoin", draft=draft)

    critique = critic._deterministic_semantic_inference(draft, state)
    assert critique.passed is False
    assert any("Sunscreen omitted" in c for c in critique.contraindication_conflicts)
    assert "Photosensitization Risk" in critique.chain_of_thought


def test_roadmap_1_hybrid_critic_passes_compliant_cot():
    """Confirms compliant oral minoxidil with cardiovascular contraindications passes."""
    critic = HybridClinicalCritic()
    draft = ArticleDraft(
        title="Oral Minoxidil Protocol",
        slug="minoxidil-test",
        target_kw="oral minoxidil",
        scientific_summary="Summary.",
        actionable_protocol=["Take 1.25 mg oral minoxidil daily [PMID:33675122]."],
        contraindications=["Severe angina pectoris and heart failure"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    state = PipelineState(raw_topic="oral minoxidil", draft=draft)

    critique = critic._deterministic_semantic_inference(draft, state)
    assert critique.passed is True
    assert "satisfies semantic clinical criteria" in critique.chain_of_thought


# ==============================================================================
# Roadmap 2: Targeted Programmatic Repair Loop with AST Diff Feedback
# ==============================================================================

@pytest.mark.asyncio
async def test_roadmap_2_targeted_repair_injects_ast_diff_safeguards():
    """Verifies that missing SPF photoprotection is surgically added to protocol."""
    retrieved = [{"id": "PMID:31256594", "title": "Tretinoin Paper"}]
    draft = ArticleDraft(
        title="Tretinoin Draft",
        slug="tretinoin-draft",
        target_kw="tretinoin",
        scientific_summary="Summary.",
        actionable_protocol=["Apply 0.025% tretinoin cream nightly [PMID:31256594]."],
        contraindications=["Pregnancy"],
        citations=["PMID:31256594"],
        structured_faq=[FAQItem(
            question="Is topical tretinoin safe for long-term use?",
            answer="Yes, systematic reviews indicate high tolerability when titrated conservatively with moisturizer."
        )]
    )
    state = PipelineState(
        raw_topic="tretinoin",
        retrieved_papers=retrieved,
        draft=draft
    )

    repaired_state = await DeterministicVerificationGate.evaluate_and_repair_loop(state)
    assert repaired_state.audit_passed is True
    assert any("SPF 50+" in p for p in repaired_state.draft.actionable_protocol)
    assert repaired_state.repair_attempts > 0


# ==============================================================================
# Roadmap 3: Dynamic MeSH Query Expansion
# ==============================================================================

def test_roadmap_3_mesh_expansion_resolves_layperson_terms():
    """Verifies mapping of subculture / colloquial aesthetic terms to NLM MeSH."""
    # Test hair thinning
    expanded_hair, terms_hair = MeSHQueryExpander.expand("hair loss and balding protocol")
    assert "Alopecia" in expanded_hair
    assert len(terms_hair) >= 1

    # Test acne and retinoids
    expanded_skin, terms_skin = MeSHQueryExpander.expand("pimples and tretinoin treatment")
    assert "Acne Vulgaris" in expanded_skin
    assert "Tretinoin" in expanded_skin

    # Test jawline & mewing
    expanded_ortho, terms_ortho = MeSHQueryExpander.expand("mewing jawline exercises")
    assert "Tongue" in expanded_ortho or "Dental Occlusion" in expanded_ortho


# ==============================================================================
# Roadmap 4: Cache Invalidation on Guideline Updates
# ==============================================================================

def test_roadmap_4_clinical_dictionary_fingerprint_invalidation():
    """Verifies that altering dictionary ceilings invalidates SQLite checkpoint keys."""
    fingerprint = get_dictionary_fingerprint()
    assert len(fingerprint) == 16

    key_standard = compute_idempotency_key("oral minoxidil")
    key_tightened_guideline = compute_idempotency_key(
        "oral minoxidil",
        dictionary_hash="tightened_ceiling_hash_999"
    )

    assert key_standard != key_tightened_guideline

    # Test with StateStore: Checkpoint with old key does not hit with new key
    store = StateStore(":memory:")
    mgr = StateGraphManager(store)
    exec_id, key, state = mgr.create_execution("oral minoxidil")
    state.audit_passed = True
    state.draft = ArticleDraft(
        title="Cached Minoxidil Draft",
        slug="cached-minoxidil",
        target_kw="oral minoxidil",
        scientific_summary="Summary.",
        actionable_protocol=["Take 1.25 mg daily."],
        contraindications=["Heart failure"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    mgr.record_transition(exec_id, key, "audit", state)

    # Retrieval with identical guideline fingerprint hits cache
    _, key_hit, restored = mgr.create_execution("oral minoxidil")
    assert restored.draft is not None
    assert restored.draft.title == "Cached Minoxidil Draft"

    # Retrieval after guideline revision (different hash) bypasses stale cache
    key_invalidated = compute_idempotency_key("oral minoxidil", dictionary_hash="new_2026_guideline_hash")
    stale_check = store.get_latest_checkpoint(key_invalidated)
    assert stale_check is None, "Stale cache was returned after guideline update!"
