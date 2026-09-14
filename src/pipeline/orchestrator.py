"""Master End-to-End Evidence-Led SEO Engine Pipeline Orchestrator."""

import uuid
from typing import Optional
from src.schemas.pipeline_state import PipelineState
from src.safety.triage import SafetyTriageAgent
from src.retrieval.pubmed_client import PubMedClient
from src.extraction.evidence_matrix import StructuredExtractionAgent
from src.drafting.dual_constraint_agent import DualConstraintDraftingAgent
from src.verification.gate_engine import DeterministicVerificationGate
from src.persistence.state_graph import StateGraphManager, compute_idempotency_key
from src.persistence.db import StateStore
from src.deployment.cms_exporter import CMSExporter


class EvidenceLedPipeline:
    """Full deterministic, citation-backed, harm-reduced SEO content engine."""

    def __init__(self, llm_client=None, store: Optional[StateStore] = None):
        self.llm = llm_client
        self.store = store or StateStore()
        self.graph_mgr = StateGraphManager(self.store)
        self.pubmed = PubMedClient()
        self.drafter = DualConstraintDraftingAgent(llm_client=self.llm)

    async def run(self, raw_topic: str, retrieval_version: str = "v1") -> PipelineState:
        execution_id, idempotency_key, state = self.graph_mgr.create_execution(
            raw_topic, retrieval_version=retrieval_version
        )

        # If we already have a fully audited checkpoint for this key, return it
        if state.audit_passed and state.draft:
            return state

        # Step 1: Layer 1 Safety & Topic Triage
        state = SafetyTriageAgent.triage(state)
        self.graph_mgr.record_transition(execution_id, idempotency_key, "triage", state)

        # If banned / self-harm, route directly to crisis notice and stop
        if state.risk_category == "banned" or state.is_crisis_routed:
            state.output_cms_markdown = CMSExporter.render_markdown(state)
            self.graph_mgr.record_transition(execution_id, idempotency_key, "crisis_routed", state)
            return state

        # Step 2: PubMed Discipline-Isolated Retrieval
        state.step_history.append("step_pubmed_retrieval")
        papers = await self.pubmed.search(state.raw_topic, explicit_namespace=state.discipline_namespace)
        state.retrieved_papers = papers
        self.graph_mgr.record_transition(execution_id, idempotency_key, "retrieval", state)

        # Step 3: Structured Extraction & Evidence Matrix Generation
        state = StructuredExtractionAgent.extract_evidence(state)
        self.graph_mgr.record_transition(execution_id, idempotency_key, "evidence_extraction", state)

        # Step 4: Dual-Constraint Drafting (High citation density, zero slang)
        state = await self.drafter.draft(state)
        self.graph_mgr.record_transition(execution_id, idempotency_key, "drafting", state)

        # Step 5: Deterministic Verification Gate & Critique/Repair Loops
        state = await DeterministicVerificationGate.evaluate_and_repair_loop(state)
        self.graph_mgr.record_transition(execution_id, idempotency_key, "verification_gate", state)

        # Step 6: CMS / SSG Deployment Export
        if state.audit_passed and state.draft:
            state.output_cms_markdown = CMSExporter.render_markdown(state)
            self.graph_mgr.record_transition(execution_id, idempotency_key, "cms_export", state)

        return state
