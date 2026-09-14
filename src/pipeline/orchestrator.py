"""Master End-to-End Evidence-Led SEO Engine Pipeline Orchestrator."""

import uuid
import time
from datetime import datetime
from typing import Optional, Dict
from src.schemas.pipeline_state import PipelineState, ExecutionTelemetry
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
        t0 = time.perf_counter()
        start_iso = datetime.utcnow().isoformat() + "Z"
        stage_latencies: Dict[str, float] = {}

        execution_id, idempotency_key, state = self.graph_mgr.create_execution(
            raw_topic, retrieval_version=retrieval_version
        )

        # If we already have a fully audited checkpoint for this key, return it with telemetry
        if state.audit_passed and state.draft:
            if not state.telemetry:
                state.telemetry = ExecutionTelemetry(
                    start_time_iso=start_iso,
                    duration_ms=(time.perf_counter() - t0) * 1000.0,
                    stage_latencies_ms={"checkpoint_lookup": (time.perf_counter() - t0) * 1000.0},
                    idempotent_hit=True
                )
            else:
                state.telemetry.idempotent_hit = True
            return state

        # Step 1: Layer 1 Safety & Topic Triage
        s0 = time.perf_counter()
        state = SafetyTriageAgent.triage(state)
        stage_latencies["triage"] = (time.perf_counter() - s0) * 1000.0
        self.graph_mgr.record_transition(execution_id, idempotency_key, "triage", state)

        # If banned / self-harm, route directly to crisis notice and stop
        if state.risk_category == "banned" or state.is_crisis_routed:
            state.output_cms_markdown = CMSExporter.render_markdown(state)
            self.graph_mgr.record_transition(execution_id, idempotency_key, "crisis_routed", state)
            state.telemetry = ExecutionTelemetry(
                start_time_iso=start_iso,
                duration_ms=(time.perf_counter() - t0) * 1000.0,
                stage_latencies_ms=stage_latencies,
                gate_checks_performed=1
            )
            return state

        # Step 2: PubMed Discipline-Isolated Retrieval
        s1 = time.perf_counter()
        state.step_history.append("step_pubmed_retrieval")
        papers = await self.pubmed.search(state.raw_topic, explicit_namespace=state.discipline_namespace)
        state.retrieved_papers = papers
        stage_latencies["retrieval"] = (time.perf_counter() - s1) * 1000.0
        self.graph_mgr.record_transition(execution_id, idempotency_key, "retrieval", state)

        # Step 3: Structured Extraction & Evidence Matrix Generation
        s2 = time.perf_counter()
        state = StructuredExtractionAgent.extract_evidence(state)
        stage_latencies["evidence_extraction"] = (time.perf_counter() - s2) * 1000.0
        self.graph_mgr.record_transition(execution_id, idempotency_key, "evidence_extraction", state)

        # Step 4: Dual-Constraint Drafting (High citation density, zero slang)
        s3 = time.perf_counter()
        state = await self.drafter.draft(state)
        stage_latencies["drafting"] = (time.perf_counter() - s3) * 1000.0
        self.graph_mgr.record_transition(execution_id, idempotency_key, "drafting", state)

        # Step 5: Deterministic Verification Gate & Critique/Repair Loops
        s4 = time.perf_counter()
        state = await DeterministicVerificationGate.evaluate_and_repair_loop(state)
        stage_latencies["verification_gate"] = (time.perf_counter() - s4) * 1000.0
        self.graph_mgr.record_transition(execution_id, idempotency_key, "verification_gate", state)

        # Step 6: CMS / SSG Deployment Export
        s5 = time.perf_counter()
        if state.audit_passed and state.draft:
            state.output_cms_markdown = CMSExporter.render_markdown(state)
            stage_latencies["cms_export"] = (time.perf_counter() - s5) * 1000.0
            self.graph_mgr.record_transition(execution_id, idempotency_key, "cms_export", state)

        # Finalize Telemetry Metrics
        total_duration_ms = (time.perf_counter() - t0) * 1000.0
        tokens_est = sum(len(p.get("abstract", "").split()) for p in state.retrieved_papers) + (
            len(state.output_cms_markdown.split()) if state.output_cms_markdown else 0
        )
        state.telemetry = ExecutionTelemetry(
            start_time_iso=start_iso,
            duration_ms=total_duration_ms,
            stage_latencies_ms=stage_latencies,
            tokens_processed_est=tokens_est,
            gate_checks_performed=len(state.audit_history),
            repairs_executed=state.repair_attempts
        )

        return state
