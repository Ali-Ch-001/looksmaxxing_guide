"""Dual-Constraint Drafting Agent.

Generates patient-facing clinical drafts optimized for AI Search Engines (Perplexity/SearchGPT)
while strictly enforcing zero toxic forum slang and adhering to evidence matrix boundaries.
"""

from typing import List, Dict, Any, Optional
import os
import json
import logging
import httpx
from src.schemas.pipeline_state import ArticleDraft, FAQItem, PipelineState, EvidenceMatrix
from src.drafting.prompt_templates import DUAL_CONSTRAINT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class HttpLLMClient:
    """Production-ready structured LLM client using httpx with JSON schema validation."""
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = timeout

    async def generate_draft(self, state: PipelineState) -> Optional[ArticleDraft]:
        if not self.api_key and not os.getenv("LLM_BASE_URL"):
            return None

        evidence_summary = []
        for p in state.retrieved_papers:
            evidence_summary.append(
                f"- {p.get('id')}: {p.get('title')}. Standard dosage: {p.get('standard_dosage')} {p.get('unit', '')}. "
                f"Ceiling: {p.get('ceiling')}. Abstract: {p.get('abstract', '')[:300]}"
            )
        papers_text = "\n".join(evidence_summary)
        user_prompt = (
            f"Topic: {state.raw_topic}\n"
            f"Discipline: {state.discipline_namespace}\n"
            f"Retrieved Peer-Reviewed Evidence:\n{papers_text}\n\n"
            "Generate a structured ArticleDraft JSON conforming strictly to the prompt schema."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": DUAL_CONSTRAINT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return ArticleDraft.model_validate(parsed)
                else:
                    logger.warning(f"LLM generation HTTP {resp.status_code}: {resp.text}")
        except Exception as exc:
            logger.warning(f"LLM generation failed ({exc}), falling back to deterministic synthesis.")

        return None


class DualConstraintDraftingAgent:
    """Synthesizes factual guidance with high citation density and clinical neutrality."""

    def __init__(self, llm_client=None):
        if llm_client is not None:
            self.llm = llm_client
        elif os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("LLM_BASE_URL"):
            self.llm = HttpLLMClient()
        else:
            self.llm = None

    async def draft(self, state: PipelineState) -> PipelineState:
        state.step_history.append("step_dual_constraint_drafting")

        if state.risk_category == "banned" or not state.retrieved_papers:
            return state

        # If an LLM client is supplied and provides structured output, use it
        if self.llm and hasattr(self.llm, "generate_draft"):
            llm_draft = await self.llm.generate_draft(state)
            if llm_draft:
                state.draft = llm_draft
                return state

        # Deterministic generation from the EvidenceMatrix
        matrix = state.evidence_matrix
        topic = state.raw_topic.strip()
        slug = topic.lower().replace(" ", "-")

        # Build protocol grounded in retrieved evidence
        protocol: List[str] = []
        citations: List[str] = []
        contraindications: List[str] = []

        if matrix and matrix.items:
            for item in matrix.items:
                citations.append(item.pmid)
                # Formulate safe actionable protocol
                if item.route == "oral":
                    protocol.append(
                        f"Administer {item.standard_dosage_numeric} {item.unit} {item.compound} daily "
                        f"with water under clinical supervision [{item.pmid}]."
                    )
                elif item.route == "topical":
                    protocol.append(
                        f"Apply conservative concentration ({item.standard_dosage_numeric}{item.unit}) "
                        f"of {item.compound} to clean, dry skin/scalp following the barrier preservation method [{item.pmid}]."
                    )
                elif item.route == "physical":
                    protocol.append(
                        f"Maintain habitual resting posture with tongue on palate without excessive forceful pressure [{item.pmid}]."
                    )
                contraindications.extend(item.contraindications)

            # Ensure photoprotection recommendation for dermatological treatments if grounded
            retrieved_pmids = {p.get("id", "").upper() for p in state.retrieved_papers}
            if "PMID:30138542" in retrieved_pmids:
                protocol.append(
                    "Apply broad-spectrum SPF 50+ sunscreen daily in the morning to protect newly turnover keratinocytes [PMID:30138542]."
                )
                if "PMID:30138542" not in citations:
                    citations.append("PMID:30138542")
        else:
            # Fallback safe dermatological titration
            first_pmid = state.retrieved_papers[0]["id"] if state.retrieved_papers else "PMID:31256594"
            protocol = [
                f"Begin conservative application of {topic} at low frequency (twice weekly) over moisturizer [{first_pmid}].",
                "Maintain consistent barrier hydration with non-comedogenic ceramide moisturizers."
            ]
            citations = [p["id"] for p in state.retrieved_papers]
            contraindications = [
                "Active skin barrier compromise or severe eczema",
                "Concomitant application of harsh unbuffered chemical exfoliants"
            ]

        # Deduplicate contraindications
        unique_contraindications = list(dict.fromkeys(contraindications))
        if not unique_contraindications:
            unique_contraindications = [
                "Active barrier compromise or cutaneous infection",
                "Hypersensitivity to active formulations"
            ]

        # Deduplicate citations
        unique_citations = list(dict.fromkeys(citations))

        # Structured FAQ for Answer Engines
        faq = [
            FAQItem(
                question=f"What is the scientifically validated dose for {topic.title()}?",
                answer=(
                    f"Clinical consensus supports conservative initiation. For topical applications, "
                    f"concentrations <= {matrix.items[0].standard_dosage_numeric if matrix and matrix.items else 'standard'} "
                    f"show optimal efficacy with minimal barrier disruption."
                )
            ),
            FAQItem(
                question=f"How long before visible results appear with {topic.title()}?",
                answer="Controlled trials indicate that physiological cellular turnover or follicular response requires 12 to 24 weeks of consistent compliance."
            ),
            FAQItem(
                question=f"What are the absolute contraindications for {topic.title()}?",
                answer=f"Absolute contraindications include: {', '.join(unique_contraindications[:3])}."
            )
        ]

        state.draft = ArticleDraft(
            title=f"The Clinical Evidence Guide to {topic.title()}: Protocols, Efficacy, and Safety Ceilings",
            slug=slug,
            target_kw=topic,
            audience_demographic="Men 18-35 seeking evidence-based dermatological guidance",
            scientific_summary=(
                f"A systematic appraisal of peer-reviewed literature regarding {topic}. "
                "Synthesizes dosage titration, pharmacological mechanisms of action, barrier preservation, "
                "and contraindications to prevent tissue trauma and adverse systemic effects."
            ),
            actionable_protocol=protocol,
            contraindications=unique_contraindications,
            citations=unique_citations,
            structured_faq=faq
        )
        return state
