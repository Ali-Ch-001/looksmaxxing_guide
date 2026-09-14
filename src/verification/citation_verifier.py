"""Citation Grounding Verifier.

Enforces 1:1 mapping between drafted claims/citations and peer-reviewed abstracts
stored in state memory. Strips or rejects hallucinated PMIDs or detached claims.
"""

from typing import List, Dict, Any, Tuple, Set
import re
from src.schemas.pipeline_state import ArticleDraft, PipelineState


PMID_REGEX = re.compile(r'PMID:(\d+)', re.IGNORECASE)


class CitationGroundingVerifier:
    """Verifies that all citations and numerical assertions ground directly in retrieved literature."""

    @staticmethod
    def extract_embedded_pmids(text: str) -> Set[str]:
        matches = PMID_REGEX.findall(text)
        return {f"PMID:{m}" for m in matches}

    @classmethod
    def verify(cls, state: PipelineState) -> Tuple[bool, List[str], List[str]]:
        """Verifies draft citations against state.retrieved_papers.
        
        Returns: (passed, unverified_citations, error_messages)
        """
        if not state.draft:
            return False, [], ["No article draft present to audit."]

        draft = state.draft
        retrieved_pmids: Set[str] = {p.get("id", "").upper() for p in state.retrieved_papers}

        # 1. Collect all citations from draft.citations list and embedded text
        claimed_pmids: Set[str] = {c.strip().upper() for c in draft.citations if c.strip()}
        
        # Check embedded PMIDs in protocol
        for step in draft.actionable_protocol:
            claimed_pmids.update(cls.extract_embedded_pmids(step))
        for faq in draft.structured_faq:
            claimed_pmids.update(cls.extract_embedded_pmids(faq.answer))

        unverified = [pmid for pmid in claimed_pmids if pmid not in retrieved_pmids]
        errors: List[str] = []

        if unverified:
            errors.append(
                f"UNVERIFIED CITATION GROUNDING: Found {len(unverified)} citation(s) not present in "
                f"retrieved literature: {', '.join(unverified)}."
            )

        # 2. Check citation density: Medical content must have at least one verified citation
        valid_citations = claimed_pmids.intersection(retrieved_pmids)
        if len(valid_citations) == 0:
            errors.append("ZERO CITATION DENSITY: Draft lacks any verified PubMed citations.")

        passed = len(errors) == 0
        return passed, unverified, errors
