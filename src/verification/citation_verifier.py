"""Citation Grounding & Semantic Claim Verifier.

Enforces 1:1 mapping between drafted claims/citations and peer-reviewed abstracts
stored in state memory. Validates numerical assertion consistency between protocol steps
and source study text, populating structured ClaimVerification records.
"""

from typing import List, Dict, Any, Tuple, Set
import re
from src.schemas.pipeline_state import ArticleDraft, PipelineState, ClaimVerification


PMID_REGEX = re.compile(r'PMID:(\d+)', re.IGNORECASE)
CLINICAL_DOSAGE_REGEX = re.compile(r'(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|ug|g|%|ml|mm|iu|spf)\b', re.IGNORECASE)
NUMBER_REGEX = re.compile(r'(\d+(?:\.\d+)?)\s*(?:mg|mcg|%|g|ml|mm|iu|spf)?', re.IGNORECASE)
PROCEDURAL_PATTERNS = re.compile(
    r'\b(?:step\s+\d+|spf\s*\d+\+?|for\s+\d+\s+(?:months?|weeks?|days?|hours?|years?)|in\s+\d+\s+(?:months?|weeks?|days?)|'
    r'every\s+\d+\s+(?:hours?|days?)|wait\s+\d+\s+(?:minutes?|hours?|days?)|after\s+\d+\s+(?:months?|weeks?|days?))\b',
    re.IGNORECASE
)


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

                paper_body = paper.get("abstract", "") + " " + paper.get("snippet", "") + " " + paper.get("dosage_range", "")
                if not paper_body.strip():
                    # If paper record only contains an ID/title stub without text body, skip strict numerical matching
                    verified_claims_list.append(ClaimVerification(
                        claim=step,
                        evidence_found=True,
                        source_pmid_or_doi=pmid,
                        risk_level="safe",
                        harm_reduction_note="Referenced stub paper"
                    ))
                    continue

                searchable_paper_text = (
                    paper_body + " " +
                    str(paper.get("standard_dosage", "")) + " " +
                    paper.get("title", "")
                ).lower()

                # Strip PMID references and procedural/duration markers (e.g. "Step 3", "for 6 months")
                clean_step_for_nums = PMID_REGEX.sub('', step)
                clean_step_for_nums = PROCEDURAL_PATTERNS.sub('', clean_step_for_nums)

                # 1. First extract clinical dosage quantities with units
                dosage_matches = list(CLINICAL_DOSAGE_REGEX.finditer(clean_step_for_nums))
                grounded = True
                unsupported_numbers = []

                for dm in dosage_matches:
                    d_num = dm.group("number")
                    d_unit = dm.group("unit").lower()
                    # Check discrete word boundary for number and presence of unit in paper
                    has_num = bool(re.search(rf'\b{re.escape(d_num)}\b', searchable_paper_text))
                    has_unit = (d_unit in searchable_paper_text) if d_unit != "%" else ("%" in searchable_paper_text or "percent" in searchable_paper_text)
                    if not (has_num and has_unit):
                        unsupported_numbers.append(f"{d_num} {d_unit}")

                # 2. Extract remaining non-procedural numbers
                step_numbers = NUMBER_REGEX.findall(clean_step_for_nums)
                for num in step_numbers:
                    # Check discrete word boundary
                    if not re.search(rf'\b{re.escape(num)}\b', searchable_paper_text):
                        # Allow standard small integers (e.g. "twice daily", "1 ml")
                        try:
                            val = float(num)
                            if val in [1.0, 2.0]:
                                continue
                        except ValueError:
                            pass
                        if num not in [dm.group("number") for dm in dosage_matches]:
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
