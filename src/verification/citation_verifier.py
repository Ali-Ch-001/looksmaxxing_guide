"""Citation Grounding & Semantic Claim Verifier.

Enforces 1:1 mapping between drafted claims/citations and peer-reviewed abstracts
stored in state memory. Validates numerical assertion consistency between protocol steps
and source study text, populating structured ClaimVerification records.
"""

from typing import List, Dict, Any, Tuple, Set
import re
from src.schemas.pipeline_state import ArticleDraft, PipelineState, ClaimVerification


PMID_REGEX = re.compile(r'PMID:(\d+)', re.IGNORECASE)
NUMBER_REGEX = re.compile(r'(\d+(?:\.\d+)?)\s*(?:mg|mcg|%|g|ml|mm|iu|spf)?', re.IGNORECASE)


class CitationGroundingVerifier:
    """Verifies that citations and numerical assertions ground directly in retrieved literature."""

    @staticmethod
    def extract_embedded_pmids(text: str) -> Set[str]:
        matches = PMID_REGEX.findall(text)
        return {f"PMID:{m}" for m in matches}

    @classmethod
    def verify(cls, state: PipelineState) -> Tuple[bool, List[str], List[str]]:
        """Verifies draft citations and numerical grounding against state.retrieved_papers.
        
        Returns: (passed, unverified_citations, error_messages)
        """
        if not state.draft:
            return False, [], ["No article draft present to audit."]

        draft = state.draft
        retrieved_papers_by_pmid: Dict[str, Dict[str, Any]] = {
            p.get("id", "").upper(): p for p in state.retrieved_papers
        }
        retrieved_pmids: Set[str] = set(retrieved_papers_by_pmid.keys())

        # 1. Collect all citations from draft.citations list and embedded text
        claimed_pmids: Set[str] = {c.strip().upper() for c in draft.citations if c.strip()}
        
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

        # 3. Semantic & Numerical Assertion Verification against Source Abstracts
        verified_claims_list: List[ClaimVerification] = []

        for step in draft.actionable_protocol:
            step_pmids = cls.extract_embedded_pmids(step)
            for pmid in step_pmids:
                paper = retrieved_papers_by_pmid.get(pmid.upper())
                if not paper:
                    continue

                searchable_paper_text = (
                    paper.get("abstract", "") + " " +
                    paper.get("snippet", "") + " " +
                    paper.get("dosage_range", "") + " " +
                    str(paper.get("standard_dosage", "")) + " " +
                    paper.get("title", "")
                ).lower()

                # Extract numbers in protocol step, excluding the PMID citation itself
                clean_step_for_nums = PMID_REGEX.sub('', step)
                step_numbers = NUMBER_REGEX.findall(clean_step_for_nums)
                grounded = True
                unsupported_numbers = []

                for num in step_numbers:
                    # Check if number appears in paper text
                    if num not in searchable_paper_text:
                        # Allow standard small integers (e.g. step numbers)
                        try:
                            val = float(num)
                            if val in [1.0, 2.0]:  # e.g. "twice daily", "1 ml"
                                continue
                        except ValueError:
                            pass
                        unsupported_numbers.append(num)

                if unsupported_numbers:
                    errors.append(
                        f"FACTUAL ASSERTION DRIFT: Protocol step asserts quantity ({', '.join(unsupported_numbers)}) "
                        f"citing {pmid}, but {pmid} contains no corroborating quantitative evidence."
                    )
                    grounded = False

                verified_claims_list.append(ClaimVerification(
                    claim=step,
                    evidence_found=grounded,
                    source_pmid_or_doi=pmid,
                    risk_level="safe" if grounded else "caution",
                    harm_reduction_note="Verified against abstract corpus" if grounded else "Discrepancy in source numbers"
                ))

        state.verified_claims = verified_claims_list
        passed = len(errors) == 0
        return passed, unverified, errors
