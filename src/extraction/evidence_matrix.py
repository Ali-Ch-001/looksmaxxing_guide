"""Structured Extraction Agent.

Processes retrieved domain papers to build a machine-readable Evidence Matrix.
Extracts verified active compounds, routes, clinical dosage bounds, efficacy metrics,
and absolute contraindications prior to article prose generation.
"""

from typing import List, Dict, Any, Optional
from src.schemas.pipeline_state import EvidenceItem, EvidenceMatrix, PipelineState
from src.safety.clinical_dictionary import find_clinical_bound, CLINICAL_DICTIONARY


class StructuredExtractionAgent:
    """Extracts structured evidence items from peer-reviewed papers."""

    @staticmethod
    def extract_evidence(state: PipelineState) -> PipelineState:
        state.step_history.append("step_structured_extraction")

        if not state.retrieved_papers or state.risk_category == "banned":
            return state

        items: List[EvidenceItem] = []
        approved_pmids: List[str] = []
        hard_contraindications: List[str] = []

        for paper in state.retrieved_papers:
            pmid = paper.get("id", "")
            doi = paper.get("doi")
            compound = paper.get("compound", state.raw_topic)
            route_str = paper.get("route", "topical")
            route = route_str if route_str in ["topical", "oral", "physical", "systemic"] else "topical"

            bound = find_clinical_bound(compound, route_hint=route)
            if bound:
                max_safe = bound.absolute_ceiling
                std_dose = paper.get("standard_dosage", bound.standard_max)
                unit = bound.unit
                contra = list(set(paper.get("contraindications", []) + bound.absolute_contraindications))
            else:
                max_safe = float(paper.get("ceiling", 10.0))
                std_dose = float(paper.get("standard_dosage", 1.0))
                unit = paper.get("unit", "mg")
                contra = paper.get("contraindications", [])

            # Extract efficacy metric from snippet/abstract
            snippet = paper.get("snippet", "")
            efficacy = snippet if len(snippet) < 150 else snippet[:147] + "..."

            evidence_item = EvidenceItem(
                compound=compound,
                indication=paper.get("indication", "Evidence-led dermatological protocol"),
                route=route,
                standard_dosage_numeric=std_dose,
                unit=unit,
                max_safe_limit=max_safe,
                efficacy_metric=efficacy,
                contraindications=contra,
                pmid=pmid,
                doi=doi,
                snippet=snippet
            )
            items.append(evidence_item)
            approved_pmids.append(pmid)
            for c in contra:
                if c not in hard_contraindications:
                    hard_contraindications.append(c)

        primary_compound = items[0].compound if items else state.raw_topic

        state.evidence_matrix = EvidenceMatrix(
            discipline=state.discipline_namespace,
            primary_compound=primary_compound,
            items=items,
            approved_pmids=approved_pmids,
            hard_contraindications=hard_contraindications
        )
        return state
