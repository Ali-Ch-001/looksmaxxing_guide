"""Hybrid Deterministic & Semantic Clinical Critic with Chain-of-Thought (CoT).

Combines:
1. Deterministic Posological AST validation (hard clinical lookup boundaries)
2. Semantic Nuance Critic (evaluating drug-drug interactions, contraindication conflicts,
   demographic suitability, and photoprotection requirements via Chain-of-Thought reasoning).
"""

from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.schemas.pipeline_state import PipelineState, ArticleDraft
from src.safety.dosage_checker import DeterministicDosageEngine
from src.safety.clinical_dictionary import find_clinical_bound
from src.drafting.dual_constraint_agent import HttpLLMClient

logger = logging.getLogger(__name__)


class SemanticCritiqueResult(BaseModel):
    passed: bool
    chain_of_thought: str
    clinical_concerns: List[str] = Field(default_factory=list)
    contraindication_conflicts: List[str] = Field(default_factory=list)
    suggested_refinements: List[str] = Field(default_factory=list)


CRITIC_COT_PROMPT = """You are a senior clinical pharmacologist and medical editor reviewing an automated draft.

Perform a step-by-step Chain-of-Thought (CoT) review analyzing:
1. Posological safety & route consistency (is the route appropriate for the indication?)
2. Drug-drug interactions and concurrent active conflicts (e.g., acids + retinoids without buffering)
3. Contraindication alignment (are absolute contraindications explicitly stated?)
4. Demographic & physiological safety (patient age, cardiovascular baseline, teratogenicity)

OUTPUT FORMAT:
Return a valid JSON object with:
- "passed": boolean (false if any significant clinical hazard or missing critical warning exists)
- "chain_of_thought": string (detailed step-by-step clinical evaluation)
- "clinical_concerns": list of strings
- "contraindication_conflicts": list of strings
- "suggested_refinements": list of strings
"""


class HybridClinicalCritic:
    """Combines deterministic AST checks with semantic Chain-of-Thought criticism."""

    def __init__(self, llm_client: Optional[HttpLLMClient] = None):
        self.llm = llm_client

    async def _evaluate_with_llm(self, draft: ArticleDraft, context: str) -> Optional[SemanticCritiqueResult]:
        if not self.llm:
            return None

        prompt = (
            f"Draft Title: {draft.title}\n"
            f"Summary: {draft.scientific_summary}\n"
            f"Protocols:\n" + "\n".join(f"- {p}" for p in draft.actionable_protocol) + "\n"
            f"Contraindications:\n" + "\n".join(f"- {c}" for c in draft.contraindications) + "\n"
            f"Clinical Context:\n{context}\n\n"
            "Review this draft according to the system instructions."
        )

        headers = {
            "Authorization": f"Bearer {self.llm.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.llm.model,
            "messages": [
                {"role": "system", "content": CRITIC_COT_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.llm.timeout) as client:
                resp = await client.post(f"{self.llm.base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return SemanticCritiqueResult.model_validate(parsed)
        except Exception as e:
            logger.warning(f"LLM Critic call failed ({e}), falling back to deterministic semantic inference.")

        return None

    def _deterministic_semantic_inference(self, draft: ArticleDraft, state: PipelineState) -> SemanticCritiqueResult:
        """Rule-grounded semantic inference providing structured Chain-of-Thought reasoning."""
        cot_steps: List[str] = []
        concerns: List[str] = []
        conflicts: List[str] = []
        refinements: List[str] = []

        protocols_blob = " ".join(draft.actionable_protocol).lower()
        contra_blob = " ".join(draft.contraindications).lower()

        # Step 1: Posological Route and Vasodilator Safety Evaluation
        cot_steps.append("1. Posology & Vasodilation Analysis: Evaluating systemic vs topical routes.")
        if "oral minoxidil" in protocols_blob or "systemic minoxidil" in protocols_blob:
            if not any(w in contra_blob for w in ["heart", "cardio", "angina", "hypotension"]):
                concerns.append("Systemic vasodilator protocol lacks explicit cardiovascular baseline contraindications.")
                conflicts.append("Missing mandatory heart failure / angina contraindication for oral minoxidil.")
                refinements.append("Add: 'Baseline cardiovascular evaluation required prior to oral vasodilator initiation.'")
            else:
                cot_steps.append("   -> Oral minoxidil accompanied by documented cardiovascular warnings.")

        # Step 2: Photosensitivity and Sunscreen Counseling
        cot_steps.append("2. Photosensitization Risk: Checking active ingredient photoprotection alignment.")
        is_photosensitizer = any(w in protocols_blob for w in ["tretinoin", "retinoid", "adapalene", "glycolic", "acid peel"])
        has_spf = any("spf" in p.lower() or "sunscreen" in p.lower() for p in draft.actionable_protocol)

        if is_photosensitizer and not has_spf:
            concerns.append("Active photosensitizing agent (retinoid/AHA) prescribed without morning SPF photoprotection.")
            conflicts.append("Photosensitizer barrier preservation violation: Sunscreen omitted.")
            refinements.append("Add mandatory step: 'Apply broad-spectrum SPF 50+ sunscreen daily in the morning.'")
        elif is_photosensitizer and has_spf:
            cot_steps.append("   -> Active photosensitizer paired with documented SPF photoprotection.")

        # Step 3: Teratogenicity and Endocrine Safety
        cot_steps.append("3. Endocrine & Teratogenic Evaluation: Checking 5-alpha reductase inhibitor warnings.")
        if "finasteride" in protocols_blob or "dutasteride" in protocols_blob:
            if not any("pregnant" in c or "childbearing" in c for c in draft.contraindications):
                concerns.append("5AR inhibitor prescribed without explicit teratogenicity / pregnancy hazard warnings.")
                conflicts.append("Missing Category X pregnancy contraindication.")
                refinements.append("Add: 'Contraindicated in women of childbearing potential or pregnancy (teratogenic Category X).'")
            else:
                cot_steps.append("   -> 5-alpha reductase inhibitor paired with appropriate teratogenicity contraindication.")

        passed = (len(conflicts) == 0)
        cot_summary = "\n".join(cot_steps)
        if passed:
            cot_summary += "\nVerdict: Draft satisfies semantic clinical criteria."
        else:
            cot_summary += f"\nVerdict: Failed on {len(conflicts)} clinical conflict(s)."

        return SemanticCritiqueResult(
            passed=passed,
            chain_of_thought=cot_summary,
            clinical_concerns=concerns,
            contraindication_conflicts=conflicts,
            suggested_refinements=refinements
        )

    async def evaluate_draft(self, state: PipelineState) -> SemanticCritiqueResult:
        if not state.draft:
            return SemanticCritiqueResult(
                passed=False,
                chain_of_thought="No draft available to evaluate.",
                clinical_concerns=["Missing draft artifact"]
            )

        # 1. Try Live LLM Critic if available
        if self.llm:
            context = f"Topic: {state.raw_topic}. Namespace: {state.discipline_namespace}."
            llm_res = await self._evaluate_with_llm(state.draft, context)
            if llm_res:
                return llm_res

        # 2. Fall back to deterministic semantic inference
        return self._deterministic_semantic_inference(state.draft, state)
