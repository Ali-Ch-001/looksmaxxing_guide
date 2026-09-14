"""Unit tests for Deterministic Dosage Engine & Range Verifier."""

import pytest
from src.safety.dosage_checker import DeterministicDosageEngine
from src.safety.clinical_dictionary import CLINICAL_DICTIONARY, find_clinical_bound


def test_safe_oral_minoxidil_dose():
    passed, violations, warnings = DeterministicDosageEngine.verify_protocols(
        ["Administer 1.25 mg oral minoxidil daily [PMID:33675122]."],
        default_compound="oral minoxidil"
    )
    assert passed is True
    assert len(violations) == 0


def test_cardiology_drift_10mg_oral_minoxidil_rejection():
    # Direct test of the failure mode in Section 2 Autopsy
    passed, violations, warnings = DeterministicDosageEngine.verify_protocols(
        ["Administer 10 mg oral minoxidil daily for refractory hair thinning."],
        default_compound="oral minoxidil"
    )
    assert passed is False
    assert len(violations) >= 1
    assert "exceeds absolute safety ceiling" in violations[0]
    assert "CARDIOVASCULAR_HYPERTENSIVE_OVERDOSE_DRIFT" in violations[0]


def test_safe_topical_tretinoin_concentration():
    passed, violations, warnings = DeterministicDosageEngine.verify_protocols(
        ["Apply conservative concentration (0.025%) of tretinoin cream twice weekly."],
        default_compound="topical tretinoin"
    )
    assert passed is True
    assert len(violations) == 0


def test_excessive_tretinoin_rejection():
    passed, violations, warnings = DeterministicDosageEngine.verify_protocols(
        ["Apply 0.2% tretinoin cream directly to the skin."],
        default_compound="topical tretinoin"
    )
    assert passed is False
    assert len(violations) == 1


def test_unit_mismatch_detection():
    # Oral minoxidil specified with percentage concentration
    passed, violations, warnings = DeterministicDosageEngine.verify_protocols(
        ["Swallow 5% oral minoxidil daily."],
        default_compound="oral minoxidil"
    )
    assert passed is False
    assert len(violations) > 0


def test_decimal_preservation_not_split():
    # Verifies that 1.25 mg is not split into 25 mg
    results = DeterministicDosageEngine.extract_dosages_from_text(
        "Take 1.25 mg oral minoxidil daily."
    )
    assert len(results) == 1
    assert results[0].numeric_value == 1.25
    assert results[0].is_violation is False
