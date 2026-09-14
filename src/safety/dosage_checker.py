"""Deterministic Regex AST and Unit Dosage Range Engine (Posological AST Engine v2).

Decouples numerical and posological verification from LLM judgment.
Features:
- Canonical mass & concentration unit normalization (mcg -> mg, g -> mg)
- Frequency modifier extraction (bid = 2x, tid = 3x, etc.)
- Daily equivalent dose and cumulative multi-dose posological tracking
- Accidental topical ingestion / poisoning detection
- Strict inequality assertions against the clinical lookup dictionary
"""

from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from src.safety.clinical_dictionary import CLINICAL_DICTIONARY, find_clinical_bound, ClinicalDosageCeiling


# Regex to extract numeric value and dosage unit
DOSAGE_PATTERN = re.compile(
    r'(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|ug|g|%|percent|ml|mm|iu|spf)(?![a-zA-Z0-9])',
    re.IGNORECASE
)

# Frequency parsing patterns
FREQUENCY_PATTERNS = [
    (re.compile(r'\b(twice\s+(?:a\s+)?day|twice\s+daily|two\s+times\s+daily|2x\s+daily|b\.?i\.?d\.?|every\s+12\s+hours?|morning\s+and\s+(?:night|evening)|am\s+and\s+pm)\b', re.I), 2.0),
    (re.compile(r'\b(three\s+times\s+(?:a\s+)?day|three\s+times\s+daily|3x\s+daily|t\.?i\.?d\.?|every\s+8\s+hours?)\b', re.I), 3.0),
    (re.compile(r'\b(four\s+times\s+(?:a\s+)?day|four\s+times\s+daily|4x\s+daily|q\.?i\.?d\.?)\b', re.I), 4.0),
    (re.compile(r'\b(every\s+other\s+day|alternate\s+days?|q\.?o\.?d\.?)\b', re.I), 0.5),
    (re.compile(r'\b(twice\s+(?:a\s+)?week|2\s+times\s+(?:a\s+)?week)\b', re.I), 2.0 / 7.0),
    (re.compile(r'\b(once\s+(?:a\s+)?week|weekly|1x\s+(?:a\s+)?week)\b', re.I), 1.0 / 7.0),
    (re.compile(r'\b(once\s+(?:a\s+)?day|daily|every\s+day|1x\s+daily|q\.?d\.?|each\s+morning|each\s+night)\b', re.I), 1.0),
]

INGESTION_VERBS = {"swallow", "drink", "ingest", "consume", "sublingual", "oral intake"}


def normalize_unit(numeric_value: float, source_unit: str, target_unit: str) -> Tuple[Optional[float], Optional[str]]:
    """Converts mass units to standard base units (e.g. mcg -> mg, g -> mg).
    
    Returns: (normalized_value, error_message)
    """
    src = source_unit.lower()
    tgt = target_unit.lower()

    if src == "percent":
        src = "%"

    # Mass conversions (target: mg)
    if tgt == "mg":
        if src == "mg":
            return numeric_value, None
        elif src in ("mcg", "ug"):
            return numeric_value * 0.001, None
        elif src == "g":
            return numeric_value * 1000.0, None
        else:
            return None, f"Unit mismatch: expected mass unit (mg/mcg/g), found '{source_unit}'"

    # Concentration conversions (target: %)
    if tgt == "%":
        if src == "%":
            return numeric_value, None
        else:
            return None, f"Unit mismatch: expected concentration '%', found '{source_unit}'"

    # Needle length conversions (target: mm)
    if tgt == "mm":
        if src == "mm":
            return numeric_value, None
        else:
            return None, f"Unit mismatch: expected length 'mm', found '{source_unit}'"

    # Fallback identical match
    if src == tgt:
        return numeric_value, None

    return None, f"Incompatible units: cannot reconcile '{source_unit}' with clinical standard '{target_unit}'"


def extract_frequency_multiplier(sentence: str) -> float:
    """Extracts daily frequency multiplier from a sentence."""
    for pattern, multiplier in FREQUENCY_PATTERNS:
        if pattern.search(sentence):
            return multiplier
    return 1.0


class DosageExtractionResult:
    def __init__(
        self,
        raw_sentence: str,
        compound_name: Optional[str],
        numeric_value: float,
        unit: str,
        normalized_value: Optional[float],
        frequency_multiplier: float,
        daily_equivalent_dose: Optional[float],
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
        self.normalized_value = normalized_value
        self.frequency_multiplier = frequency_multiplier
        self.daily_equivalent_dose = daily_equivalent_dose
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
            "normalized_value": self.normalized_value,
            "frequency": self.frequency_multiplier,
            "daily_dose": self.daily_equivalent_dose,
            "ceiling": self.ceiling.absolute_ceiling if self.ceiling else None,
            "is_violation": self.is_violation,
            "violation_reason": self.violation_reason,
            "is_warning": self.is_warning,
            "warning_reason": self.warning_reason,
        }


class DeterministicDosageEngine:
    """Posological AST Engine v2: Decoupled numerical verification."""

    @staticmethod
    def extract_dosages_from_text(text: str, default_compound: Optional[str] = None) -> List[DosageExtractionResult]:
        results: List[DosageExtractionResult] = []
        sentences = [s.strip() for s in re.split(r'(?:\r?\n|(?<!\d)\.(?!\d)|[;•])+', text) if s.strip()]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            matches = list(DOSAGE_PATTERN.finditer(sentence))
            if not matches:
                continue

            frequency = extract_frequency_multiplier(sentence)

            for match in matches:
                num_str = match.group("number")
                unit_str = match.group("unit").lower()
                if unit_str == "percent":
                    unit_str = "%"

                try:
                    num_val = float(num_str)
                except ValueError:
                    continue

                compound_bound = find_clinical_bound(sentence)
                if not compound_bound and default_compound:
                    compound_bound = find_clinical_bound(default_compound)

                if not compound_bound:
                    results.append(DosageExtractionResult(
                        raw_sentence=sentence,
                        compound_name=None,
                        numeric_value=num_val,
                        unit=unit_str,
                        normalized_value=num_val,
                        frequency_multiplier=frequency,
                        daily_equivalent_dose=num_val * frequency,
                        ceiling=None,
                        is_violation=False
                    ))
                    continue

                is_violation = False
                violation_reason = None
                is_warning = False
                warning_reason = None

                # 1. Accidental Topical Ingestion / Toxic Route Guard
                has_ingestion = any(v in sentence_lower for v in INGESTION_VERBS)
                if has_ingestion and (compound_bound.route == "topical" or unit_str == "%"):
                    is_violation = True
                    violation_reason = (
                        f"FATAL TOXIC HAZARD: Ingestion verb detected for topical formulation of "
                        f"{compound_bound.canonical_name} ('{sentence}'). Oral consumption of topical solutions causes lethal poisoning."
                    )

                # 2. Canonical Unit Normalization
                norm_val, unit_err = normalize_unit(num_val, unit_str, compound_bound.unit)
                if unit_err and not is_violation:
                    is_violation = True
                    violation_reason = f"Posological Error: {unit_err} for {compound_bound.canonical_name}."

                daily_equivalent = norm_val * frequency if norm_val is not None else None

                # 3. Hard Clinical Boundary Checks
                if norm_val is not None and not is_violation:
                    # Single-dose ceiling check
                    if norm_val > compound_bound.absolute_ceiling:
                        is_violation = True
                        violation_reason = (
                            f"CRITICAL DOSAGE VIOLATION: {compound_bound.canonical_name} dose of {num_val} {unit_str} "
                            f"(normalized: {norm_val:.4g} {compound_bound.unit}) exceeds absolute safety ceiling "
                            f"of {compound_bound.absolute_ceiling} {compound_bound.unit} [{compound_bound.failure_risk_tag}]."
                        )
                    # Daily frequency-multiplied dose ceiling check
                    elif daily_equivalent is not None and daily_equivalent > compound_bound.absolute_ceiling:
                        is_violation = True
                        violation_reason = (
                            f"CRITICAL FREQUENCY OVERDOSE: {compound_bound.canonical_name} dose of {num_val} {unit_str} "
                            f"administered at frequency {frequency}x/day yields {daily_equivalent:.4g} {compound_bound.unit}/day, "
                            f"exceeding maximum daily ceiling of {compound_bound.absolute_ceiling} {compound_bound.unit}."
                        )
                    # Warning threshold check
                    elif compound_bound.warning_threshold and norm_val > compound_bound.warning_threshold:
                        is_warning = True
                        warning_reason = (
                            f"Dosage elevation advisory: {norm_val:.4g} {compound_bound.unit} exceeds standard baseline "
                            f"threshold of {compound_bound.warning_threshold} {compound_bound.unit}."
                        )

                results.append(DosageExtractionResult(
                    raw_sentence=sentence,
                    compound_name=compound_bound.canonical_name,
                    numeric_value=num_val,
                    unit=unit_str,
                    normalized_value=norm_val,
                    frequency_multiplier=frequency,
                    daily_equivalent_dose=daily_equivalent,
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
        """Validates all lines in actionable protocols, including cumulative multi-dose tracking.
        
        Returns: (passed, list_of_violations, list_of_warnings)
        """
        violations: List[str] = []
        warnings: List[str] = []
        cumulative_daily_by_compound: Dict[str, float] = defaultdict(float)
        compound_ceilings: Dict[str, ClinicalDosageCeiling] = {}

        full_text = "\n".join(protocols)
        results = cls.extract_dosages_from_text(full_text, default_compound=default_compound)

        for res in results:
            if res.is_violation and res.violation_reason:
                violations.append(res.violation_reason)
            if res.is_warning and res.warning_reason:
                warnings.append(res.warning_reason)

            # Track cumulative daily dose for systemic compounds
            if res.compound_name and res.daily_equivalent_dose is not None and res.ceiling:
                # Accumulate systemic oral dosages
                if res.ceiling.route == "oral":
                    cumulative_daily_by_compound[res.compound_name] += res.daily_equivalent_dose
                    compound_ceilings[res.compound_name] = res.ceiling

        # Check cumulative daily intake across all protocol instructions
        for comp_name, total_daily in cumulative_daily_by_compound.items():
            ceiling_obj = compound_ceilings[comp_name]
            if total_daily > ceiling_obj.absolute_ceiling:
                viol = (
                    f"CRITICAL CUMULATIVE POSOLOGY VIOLATION: Multi-dose protocol prescribes cumulative "
                    f"{total_daily:.4g} {ceiling_obj.unit}/day of {comp_name}, exceeding absolute daily ceiling "
                    f"of {ceiling_obj.absolute_ceiling} {ceiling_obj.unit}/day [{ceiling_obj.failure_risk_tag}]."
                )
                if viol not in violations:
                    violations.append(viol)

        passed = len(violations) == 0
        return passed, violations, warnings
