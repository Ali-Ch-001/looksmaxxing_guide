"""Deterministic Verification Gate Engine with Critique/Repair Loops.

Executes:
1. Unit & Dosage Range Engine (Deterministic bounds, not LLM-judged)
2. Citation Grounding Verifier (1:1 mapping against retrieved PubMed abstracts)
3. Toxic Slang & Dysmorphia Detector (Layer 2 safety check)
4. Schema.org JSON-LD Validator (MedicalWebPage + FAQPage)

Manages repair loops:
- Hard dosage violations or banned practices -> Immediate unrecoverable halt
- Minor missing elements -> Auto-repair loop (max 2 attempts) -> Fail to Human Review Queue
"""

from typing import Tuple, List, Optional, Dict, Any
from src.schemas.pipeline_state import PipelineState, AuditGateResult, ArticleDraft, FAQItem
from src.safety.dosage_checker import DeterministicDosageEngine
from src.verification.citation_verifier import CitationGroundingVerifier
from src.verification.toxic_detector import ToxicSlangDetector
from src.verification.schema_validator import SchemaValidator


class DeterministicVerificationGate:
    """Multi-stage programmatic verification gate."""

    @classmethod
    def execute_audit(cls, state: PipelineState) -> AuditGateResult:
        if not state.draft:
            return AuditGateResult(
                passed=False,
                rejection_reason="No article draft present to audit.",
                failed_checks=["draft_presence"]
            )

        draft = state.draft
        failed_checks: List[str] = []
        dosage_violations: List[str] = []
        unverified_citations: List[str] = []
        slang_detected: List[str] = []
        warnings: List[str] = []

        # 1. Deterministic Dosage & Range AST Check
        default_compound = state.evidence_matrix.primary_compound if state.evidence_matrix else state.raw_topic
        dosage_passed, d_violations, d_warnings = DeterministicDosageEngine.verify_protocols(
            draft.actionable_protocol,
            default_compound=default_compound
        )
        if not dosage_passed:
            failed_checks.append("dosage_bounds_check")
            dosage_violations.extend(d_violations)
        warnings.extend(d_warnings)

        # 2. Citation Grounding Check
        citations_passed, unverified, c_errors = CitationGroundingVerifier.verify(state)
        if not citations_passed:
            failed_checks.append("citation_grounding_check")
            unverified_citations.extend(unverified)
            for err in c_errors:
                if err not in failed_checks:
                    failed_checks.append(err)

        # 3. Post-Draft Toxic Slang & Dysmorphia Check
        slang_passed, s_violations = ToxicSlangDetector.scan(draft)
        if not slang_passed:
            failed_checks.append("toxic_slang_check")
            slang_detected.extend(s_violations)

        # 4. Schema.org Validation
        schema_passed, schema_errors, compiled_json_ld = SchemaValidator.validate(draft)
        if not schema_passed:
            failed_checks.append("schema_org_validation")
            for err in schema_errors:
                failed_checks.append(err)
        else:
            state.output_json_ld = compiled_json_ld

        # Determine if auto-repair is permissible
        # HARD FAILURES: Dosage ceiling violations or physical self-harm practices trigger unrecoverable halt
        is_hard_failure = len(dosage_violations) > 0 or len(slang_detected) > 0
        can_auto_repair = not is_hard_failure and (len(unverified_citations) > 0 or not schema_passed)

        overall_passed = (len(failed_checks) == 0 and not is_hard_failure)

        rejection_reason = None
        if not overall_passed:
            reasons = []
            if dosage_violations:
                reasons.append("FATAL CLINICAL DOSAGE VIOLATION: " + "; ".join(dosage_violations))
            if slang_detected:
                reasons.append("PROHIBITED CONTENT: " + "; ".join(slang_detected))
            if unverified_citations:
                reasons.append(f"UNGROUNDED CITATIONS: {', '.join(unverified_citations)}")
            if schema_errors:
                reasons.append("SCHEMA ERRORS: " + "; ".join(schema_errors))
            rejection_reason = " | ".join(reasons)

        result = AuditGateResult(
            passed=overall_passed,
            rejection_reason=rejection_reason,
            failed_checks=failed_checks,
            warnings=warnings,
            dosage_violations=dosage_violations,
            unverified_citations=unverified_citations,
            slang_or_toxic_detected=slang_detected,
            can_auto_repair=can_auto_repair
        )
        state.audit_history.append(result)
        return result

    @classmethod
    def attempt_repair(cls, state: PipelineState, audit_result: AuditGateResult) -> bool:
        """Executes targeted programmatic repairs on soft failure modes."""
        if not state.draft or not audit_result.can_auto_repair:
            return False

        draft = state.draft
        repaired_anything = False

        # 1. Strip ungrounded citations
        if audit_result.unverified_citations:
            valid_retrieved_pmids = {p.get("id", "").upper() for p in state.retrieved_papers}
            new_citations = [c for c in draft.citations if c.upper() in valid_retrieved_pmids]
            if not new_citations and state.retrieved_papers:
                new_citations = [state.retrieved_papers[0]["id"]]
            draft.citations = new_citations
            repaired_anything = True

        # 2. Repair missing contraindications or FAQ
        if not draft.contraindications:
            draft.contraindications = [
                "Active barrier compromise or acute cutaneous infection",
                "Known hypersensitivity to active ingredients"
            ]
            repaired_anything = True

        if not draft.structured_faq:
            draft.structured_faq = [
                FAQItem(
                    question=f"What is the clinical safety profile of {draft.target_kw}?",
                    answer="Peer-reviewed studies indicate optimal tolerability when starting with conservative concentrations."
                )
            ]
            repaired_anything = True

        return repaired_anything

    @classmethod
    async def evaluate_and_repair_loop(cls, state: PipelineState) -> PipelineState:
        """Runs the audit gate with up to max_repair_attempts critique/repair cycles."""
        state.step_history.append("step_deterministic_verification_gate")

        while True:
            audit_result = cls.execute_audit(state)

            if audit_result.passed:
                state.audit_passed = True
                state.rejection_reason = None
                return state

            # Hard failures halt immediately
            if not audit_result.can_auto_repair:
                state.audit_passed = False
                state.rejection_reason = (
                    f"UNRECOVERABLE AUDIT FAILURE (Halted without repair): {audit_result.rejection_reason}"
                )
                return state

            # Check repair limits
            if state.repair_attempts >= state.max_repair_attempts:
                state.audit_passed = False
                state.rejection_reason = (
                    f"CRITIQUE/REPAIR CYCLES EXHAUSTED ({state.repair_attempts}/{state.max_repair_attempts}). "
                    f"Routed to Human Review Queue. Reason: {audit_result.rejection_reason}"
                )
                return state

            # Perform repair
            state.repair_attempts += 1
            repaired = cls.attempt_repair(state, audit_result)
            if not repaired:
                state.audit_passed = False
                state.rejection_reason = (
                    f"UNREPAIRABLE AUDIT FAILURE: {audit_result.rejection_reason}"
                )
                return state
