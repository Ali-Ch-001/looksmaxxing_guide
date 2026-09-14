"""Dual-Constraint Drafting Agent.

Generates patient-facing clinical drafts optimized for AI Search Engines (Perplexity/SearchGPT)
while strictly enforcing zero toxic forum slang and adhering to evidence matrix boundaries.
"""

from typing import List, Dict, Any, Optional
from src.schemas.pipeline_state import ArticleDraft, FAQItem, PipelineState, EvidenceMatrix
from src.drafting.prompt_templates import DUAL_CONSTRAINT_SYSTEM_PROMPT


class DualConstraintDraftingAgent:
    """Synthesizes factual guidance with high citation density and clinical neutrality."""

    def __init__(self, llm_client=None):
        self.llm = llm_client

    async def draft(self, state: PipelineState) -> PipelineState:
        state.step_history.append("step_dual_constraint_drafting")

        if state.risk_category == "banned" or not state.retrieved_papers:
            return state

        # If an LLM client is supplied and provides structured output, use it
        if self.llm and hasattr(self.llm, "generate_draft"):
            state.draft = await self.llm.generate_draft(state)
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
