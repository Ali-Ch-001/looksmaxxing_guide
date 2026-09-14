"""Unit and integration tests for LangGraph StateGraph pipeline."""

import pytest
from src.pipeline.langgraph_pipeline import (
    build_langgraph_pipeline,
    route_triage_decision,
    route_verification_decision,
    triage_node,
    GraphState,
)
from src.schemas.pipeline_state import AuditGateResult


def test_route_triage_decision():
    state_safe: GraphState = {"risk_category": "dermatology_trichology", "is_crisis_routed": False} # type: ignore
    assert route_triage_decision(state_safe) == "retrieval"

    state_banned: GraphState = {"risk_category": "banned", "is_crisis_routed": True} # type: ignore
    assert route_triage_decision(state_banned) == "crisis_router"


def test_route_verification_decision():
    # Passed
    state_passed: GraphState = {"audit_passed": True, "audit_history": [], "repair_attempts": 0, "max_repair_attempts": 2} # type: ignore
    assert route_verification_decision(state_passed) == "export"

    # Soft failure with repair remaining
    soft_audit = AuditGateResult(passed=False, can_auto_repair=True)
    state_repair: GraphState = {"audit_passed": False, "audit_history": [soft_audit], "repair_attempts": 0, "max_repair_attempts": 2} # type: ignore
    assert route_verification_decision(state_repair) == "repair"

    # Hard failure
    hard_audit = AuditGateResult(passed=False, can_auto_repair=False)
    state_hard: GraphState = {"audit_passed": False, "audit_history": [hard_audit], "repair_attempts": 0, "max_repair_attempts": 2} # type: ignore
    assert route_verification_decision(state_hard) == "human_review"


@pytest.mark.asyncio
async def test_langgraph_full_execution_topical_tretinoin():
    app = build_langgraph_pipeline()
    initial_state: GraphState = {
        "raw_topic": "topical tretinoin",
        "normalized_topic": "",
        "risk_category": "fitness",
        "discipline_namespace": "general",
        "retrieved_papers": [],
        "evidence_matrix": None,
        "draft": None,
        "audit_passed": False,
        "rejection_reason": None,
        "is_crisis_routed": False,
        "crisis_payload": None,
        "repair_attempts": 0,
        "max_repair_attempts": 2,
        "audit_history": [],
        "step_history": [],
        "output_cms_markdown": None,
        "output_json_ld": None,
        "telemetry": None
    }

    result = await app.ainvoke(initial_state)
    assert result["audit_passed"] is True
    assert result["risk_category"] == "dermatology_trichology"
    assert result["output_cms_markdown"] is not None
    assert "The Clinical Evidence Guide to Topical Tretinoin" in result["output_cms_markdown"]
