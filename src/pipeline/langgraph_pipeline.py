"""LangGraph StateGraph Workflow Orchestration for Clinical SEO Pipeline.

Implements an acyclic/cyclic state graph with:
- Safety & Topic Triage branching
- Context-split PubMed retrieval
- Evidence Matrix extraction
- Dual-Constraint Drafting
- Deterministic Verification Gate
- Critique / Auto-Repair cycles (max 2 loops)
- Human Clinical Review routing for hard posological violations
- CMS Deployment Export
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, TypedDict, Annotated
import time
from datetime import datetime

from langgraph.graph import StateGraph, END
from src.schemas.pipeline_state import (
    PipelineState,
    ArticleDraft,
    EvidenceMatrix,
    AuditGateResult,
    ExecutionTelemetry,
)
from src.safety.triage import SafetyTriageAgent
from src.retrieval.pubmed_client import PubMedClient
from src.extraction.evidence_matrix import StructuredExtractionAgent
from src.drafting.dual_constraint_agent import DualConstraintDraftingAgent
from src.verification.gate_engine import DeterministicVerificationGate
from src.deployment.cms_exporter import CMSExporter


class GraphState(TypedDict):
    raw_topic: str
    normalized_topic: str
    risk_category: str
    discipline_namespace: str
    retrieved_papers: List[Dict[str, Any]]
    evidence_matrix: Optional[EvidenceMatrix]
    draft: Optional[ArticleDraft]
    audit_passed: bool
    rejection_reason: Optional[str]
    is_crisis_routed: bool
    crisis_payload: Optional[Dict[str, Any]]
    repair_attempts: int
    max_repair_attempts: int
    audit_history: List[AuditGateResult]
    step_history: List[str]
    output_cms_markdown: Optional[str]
    output_json_ld: Optional[Dict[str, Any]]
    telemetry: Optional[ExecutionTelemetry]


def _to_pydantic_state(state: GraphState) -> PipelineState:
    return PipelineState(
        raw_topic=state["raw_topic"],
        normalized_topic=state.get("normalized_topic", ""),
        risk_category=state.get("risk_category", "fitness"),
        discipline_namespace=state.get("discipline_namespace", "general"),
        retrieved_papers=state.get("retrieved_papers", []),
        evidence_matrix=state.get("evidence_matrix"),
        draft=state.get("draft"),
        audit_passed=state.get("audit_passed", False),
        rejection_reason=state.get("rejection_reason"),
        is_crisis_routed=state.get("is_crisis_routed", False),
        crisis_payload=state.get("crisis_payload"),
        repair_attempts=state.get("repair_attempts", 0),
        max_repair_attempts=state.get("max_repair_attempts", 2),
        audit_history=state.get("audit_history", []),
        step_history=state.get("step_history", []),
        output_cms_markdown=state.get("output_cms_markdown"),
        output_json_ld=state.get("output_json_ld")
    )


def _from_pydantic_state(p_state: PipelineState, state: GraphState) -> GraphState:
    state["normalized_topic"] = p_state.normalized_topic
    state["risk_category"] = p_state.risk_category
    state["discipline_namespace"] = p_state.discipline_namespace
    state["retrieved_papers"] = p_state.retrieved_papers
    state["evidence_matrix"] = p_state.evidence_matrix
    state["draft"] = p_state.draft
    state["audit_passed"] = p_state.audit_passed
    state["rejection_reason"] = p_state.rejection_reason
    state["is_crisis_routed"] = p_state.is_crisis_routed
    state["crisis_payload"] = p_state.crisis_payload
    state["repair_attempts"] = p_state.repair_attempts
    state["audit_history"] = p_state.audit_history
    state["step_history"] = list(dict.fromkeys(state.get("step_history", []) + p_state.step_history))
    state["output_cms_markdown"] = p_state.output_cms_markdown
    state["output_json_ld"] = p_state.output_json_ld
    return state


# ==============================================================================
# Graph Node Callables
# ==============================================================================

def triage_node(state: GraphState) -> GraphState:
    """Evaluates Layer 1 Safety and categorizes discipline."""
    p_state = _to_pydantic_state(state)
    p_state = SafetyTriageAgent.triage(p_state)
    return _from_pydantic_state(p_state, state)


def crisis_router_node(state: GraphState) -> GraphState:
    """Routes banned topics or self-harm tropes to Crisis Notice."""
    p_state = _to_pydantic_state(state)
    p_state.output_cms_markdown = CMSExporter.render_markdown(p_state)
    return _from_pydantic_state(p_state, state)


async def retrieval_node(state: GraphState) -> GraphState:
    """Executes discipline-isolated PubMed retrieval."""
    client = PubMedClient()
    papers = await client.search(state["raw_topic"], explicit_namespace=state["discipline_namespace"])
    state["retrieved_papers"] = papers
    state["step_history"].append("step_pubmed_retrieval")
    return state


def extraction_node(state: GraphState) -> GraphState:
    """Extracts EvidenceMatrix prior to text drafting."""
    p_state = _to_pydantic_state(state)
    p_state = StructuredExtractionAgent.extract_evidence(p_state)
    return _from_pydantic_state(p_state, state)


async def drafting_node(state: GraphState) -> GraphState:
    """Generates dual-constraint article draft."""
    drafter = DualConstraintDraftingAgent()
    p_state = _to_pydantic_state(state)
    p_state = await drafter.draft(p_state)
    return _from_pydantic_state(p_state, state)


def verification_node(state: GraphState) -> GraphState:
    """Executes deterministic posological AST & citation grounding checks."""
    p_state = _to_pydantic_state(state)
    audit = DeterministicVerificationGate.execute_audit(p_state)
    p_state.audit_passed = audit.passed
    if not audit.passed:
        p_state.rejection_reason = audit.rejection_reason
    state["audit_history"].append(audit)
    state["step_history"].append("step_verification_audit")
    return _from_pydantic_state(p_state, state)


def repair_node(state: GraphState) -> GraphState:
    """Executes programmatic repair on soft failures."""
    p_state = _to_pydantic_state(state)
    last_audit = state["audit_history"][-1]
    DeterministicVerificationGate.attempt_repair(p_state, last_audit)
    p_state.repair_attempts += 1
    state["step_history"].append("step_critique_repair")
    return _from_pydantic_state(p_state, state)


def export_node(state: GraphState) -> GraphState:
    """Compiles markdown and Schema.org JSON-LD."""
    p_state = _to_pydantic_state(state)
    p_state.output_cms_markdown = CMSExporter.render_markdown(p_state)
    state["step_history"].append("step_cms_export")
    return _from_pydantic_state(p_state, state)


def human_review_node(state: GraphState) -> GraphState:
    """Quarantines unrecoverable violations to the Human Review Queue."""
    state["audit_passed"] = False
    state["step_history"].append("step_human_review_quarantine")
    return state


# ==============================================================================
# Conditional Edge Routers
# ==============================================================================

def route_triage_decision(state: GraphState) -> str:
    if state["risk_category"] == "banned" or state["is_crisis_routed"]:
        return "crisis_router"
    return "retrieval"


def route_verification_decision(state: GraphState) -> str:
    if state["audit_passed"]:
        return "export"

    last_audit = state["audit_history"][-1] if state["audit_history"] else None
    can_repair = last_audit.can_auto_repair if last_audit else False

    if can_repair and state["repair_attempts"] < state["max_repair_attempts"]:
        return "repair"
    return "human_review"


# ==============================================================================
# Graph Assembly & Compilation
# ==============================================================================

def build_langgraph_pipeline():
    """Constructs and compiles the production LangGraph workflow."""
    workflow = StateGraph(GraphState)

    # Register nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("crisis_router", crisis_router_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("drafting", drafting_node)
    workflow.add_node("verification", verification_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("export", export_node)
    workflow.add_node("human_review", human_review_node)

    # Set entrypoint
    workflow.set_entry_point("triage")

    # Conditional routing after triage
    workflow.add_conditional_edges(
        "triage",
        route_triage_decision,
        {
            "crisis_router": "crisis_router",
            "retrieval": "retrieval"
        }
    )

    # Linear pipelines
    workflow.add_edge("crisis_router", END)
    workflow.add_edge("retrieval", "extraction")
    workflow.add_edge("extraction", "drafting")
    workflow.add_edge("drafting", "verification")

    # Conditional routing after verification (with critique/repair loop)
    workflow.add_conditional_edges(
        "verification",
        route_verification_decision,
        {
            "export": "export",
            "repair": "repair",
            "human_review": "human_review"
        }
    )

    # Loop back from repair to re-verification
    workflow.add_edge("repair", "verification")
    workflow.add_edge("export", END)
    workflow.add_edge("human_review", END)

    return workflow.compile()
