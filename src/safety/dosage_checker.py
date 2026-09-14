"""Deterministic Regex AST and Unit Dosage Range Engine.

Decouples numerical and posological verification from LLM judgment.
Parses numeric quantities and concentration units, resolves context to active compounds,
and performs strict inequality checks against the clinical lookup dictionary.
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple, Optional
from src.safety.clinical_dictionary import CLINICAL_DICTIONARY, find_clinical_bound, ClinicalDosageCeiling


# Regex to extract numeric value and dosage unit (supports % symbol which is not matched by \b)
DOSAGE_PATTERN = re.compile(
    r'(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|%|percent|g|ml|mm|iu|spf)(?![a-zA-Z0-9])',
    re.IGNORECASE
)

# Regex to extract frequency (e.g. 2 times a week, twice daily)
FREQUENCY_PATTERN = re.compile(
    r'(?P<freq>\d+|once|twice|thrice)\s*(?:times?)?\s*(?:a|per)\s*(?:day|daily|week|month)',
    re.IGNORECASE
)


class DosageExtractionResult:
    def __init__(
        self,
        raw_sentence: str,
        compound_name: Optional[str],
        numeric_value: float,
        unit: str,
        ceiling: Optional[ClinicalDosageCeiling],
        is_violation: bool,
        violation_reason: Optional[str] = None,
        is_warning: bool = False,
        warning_reason: Optional[str] = None
    ):
        self.raw_sentence = raw_sentence
        self.compound_name = compound_name
        self.numeric_value = numeric_value
        self.unit = unit
        self.ceiling = ceiling
        self.is_violation = is_violation
        self.violation_reason = violation_reason
        self.is_warning = is_warning
        self.warning_reason = warning_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence": self.raw_sentence,
            "compound": self.compound_name,
            "numeric_value": self.numeric_value,
            "unit": self.unit,
            "ceiling": self.ceiling.absolute_ceiling if self.ceiling else None,
            "is_violation": self.is_violation,
            "violation_reason": self.violation_reason,
            "is_warning": self.is_warning,
            "warning_reason": self.warning_reason,
        }


class DeterministicDosageEngine:
    """Evaluates text and protocol steps against clinical safety ceilings."""

    @staticmethod
    def extract_dosages_from_text(text: str, default_compound: Optional[str] = None) -> List[DosageExtractionResult]:
        results: List[DosageExtractionResult] = []
        # Split text into sentences or actionable lines without splitting on decimal numbers (e.g. 1.25)
        sentences = [s.strip() for s in re.split(r'(?:\r?\n|(?<!\d)\.(?!\d)|[;•])+', text) if s.strip()]

        for sentence in sentences:
            matches = list(DOSAGE_PATTERN.finditer(sentence))
            if not matches:
                continue

            for match in matches:
                num_str = match.group("number")
                unit_str = match.group("unit").lower()
                if unit_str == "percent":
                    unit_str = "%"

                try:
                    num_val = float(num_str)
                except ValueError:
                    continue

                # Find relevant compound in sentence or fallback to default
                compound_bound = find_clinical_bound(sentence)
                if not compound_bound and default_compound:
                    compound_bound = find_clinical_bound(default_compound)

                if not compound_bound:
                    # Generic unit sanity check if no specific compound bound
                    results.append(DosageExtractionResult(
                        raw_sentence=sentence,
                        compound_name=None,
                        numeric_value=num_val,
                        unit=unit_str,
                        ceiling=None,
                        is_violation=False
                    ))
                    continue

                is_violation = False
                violation_reason = None
                is_warning = False
                warning_reason = None

                # 1. Unit mismatch check (e.g. oral minoxidil written in %)
                if compound_bound.unit == "%" and unit_str == "mg":
                    is_violation = True
                    violation_reason = (
                        f"Unit mismatch for {compound_bound.canonical_name}: expected concentration '%', "
                        f"found systemic dose '{num_val} {unit_str}'."
                    )
                elif compound_bound.unit == "mg" and unit_str == "%":
                    is_violation = True
                    violation_reason = (
                        f"Unit mismatch for {compound_bound.canonical_name}: expected dose in 'mg', "
                        f"found '{num_val} %'."
                    )
                # 2. Hard clinical boundary check
                elif compound_bound.unit == unit_str:
                    if num_val > compound_bound.absolute_ceiling:
                        is_violation = True
                        violation_reason = (
                            f"CRITICAL DOSAGE VIOLATION: {compound_bound.canonical_name} dose of {num_val} {unit_str} "
                            f"exceeds absolute dermatological safety ceiling of {compound_bound.absolute_ceiling} {compound_bound.unit} "
                            f"[{compound_bound.failure_risk_tag}]."
                        )
                    elif compound_bound.warning_threshold and num_val > compound_bound.warning_threshold:
                        is_warning = True
                        warning_reason = (
                            f"Dosage elevation advisory: {num_val} {unit_str} exceeds standard baseline "
                            f"threshold of {compound_bound.warning_threshold} {compound_bound.unit}."
                        )

                results.append(DosageExtractionResult(
                    raw_sentence=sentence,
                    compound_name=compound_bound.canonical_name,
                    numeric_value=num_val,
                    unit=unit_str,
                    ceiling=compound_bound,
                    is_violation=is_violation,
                    violation_reason=violation_reason,
                    is_warning=is_warning,
                    warning_reason=warning_reason
                ))

        return results

    @classmethod
    def verify_protocols(
        cls,
        protocols: List[str],
        default_compound: Optional[str] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """Validates all lines in actionable protocols.
        
        Returns: (passed, list_of_violations, list_of_warnings)
        """
        violations: List[str] = []
        warnings: List[str] = []

        full_text = "\n".join(protocols)
        results = cls.extract_dosages_from_text(full_text, default_compound=default_compound)

        for res in results:
            if res.is_violation and res.violation_reason:
                violations.append(res.violation_reason)
            if res.is_warning and res.warning_reason:
                warnings.append(res.warning_reason)

        passed = len(violations) == 0
        return passed, violations, warnings
