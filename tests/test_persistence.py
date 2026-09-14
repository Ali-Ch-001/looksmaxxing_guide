"""Unit tests for SQLite State Persistence and Idempotency Resumption."""

import pytest
from src.persistence.db import StateStore
from src.persistence.state_graph import StateGraphManager, compute_idempotency_key
from src.schemas.pipeline_state import PipelineState, ArticleDraft, FAQItem


def test_append_only_snapshot_saving():
    store = StateStore(":memory:")
    mgr = StateGraphManager(store)

    exec_id, key, state = mgr.create_execution("oral minoxidil")
    state.audit_passed = True
    state.draft = ArticleDraft(
        title="Valid Test Draft for Minoxidil",
        slug="test-slug",
        target_kw="minoxidil",
        scientific_summary="Summary.",
        actionable_protocol=["Take 1.25 mg daily."],
        contraindications=["Heart disease"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )

    row_id = mgr.record_transition(exec_id, key, "drafting", state)
    assert row_id > 0

    history = store.get_execution_history(exec_id)
    assert len(history) == 1
    assert history[0]["step_name"] == "drafting"
    assert history[0]["audit_passed"] == 1


def test_idempotency_checkpoint_resumption():
    store = StateStore(":memory:")
    mgr = StateGraphManager(store)

    exec_id1, key1, state1 = mgr.create_execution("oral minoxidil")
    state1.audit_passed = True
    state1.draft = ArticleDraft(
        title="Checkpointed Draft",
        slug="checkpointed-slug",
        target_kw="oral minoxidil",
        scientific_summary="Summary.",
        actionable_protocol=["Take 1.25 mg daily."],
        contraindications=["Heart disease"],
        citations=["PMID:33675122"],
        structured_faq=[FAQItem(question="Is it safe?", answer="Yes.")]
    )
    mgr.record_transition(exec_id1, key1, "verified", state1)

    # Subsequent run with same topic should restore checkpoint
    exec_id2, key2, state2 = mgr.create_execution("oral minoxidil")
    assert key1 == key2
    assert state2.audit_passed is True
    assert state2.draft is not None
    assert state2.draft.title == "Checkpointed Draft"
