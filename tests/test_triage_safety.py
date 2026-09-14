"""Unit tests for Layer 1 Safety & Topic Triage."""

import pytest
from src.safety.triage import SafetyTriageAgent, check_banned_topic
from src.schemas.pipeline_state import PipelineState


def test_triage_valid_dermatology_topic():
    state = PipelineState(raw_topic="topical tretinoin for photoaging")
    triaged = SafetyTriageAgent.triage(state)

    assert triaged.risk_category == "dermatology_trichology"
    assert triaged.discipline_namespace == "dermatology_trichology"
    assert triaged.audit_passed is True
    assert triaged.is_crisis_routed is False


def test_triage_valid_orthodontics_topic():
    state = PipelineState(raw_topic="palatal resting tongue posture and mewing")
    triaged = SafetyTriageAgent.triage(state)

    assert triaged.risk_category == "orthodontics"
    assert triaged.discipline_namespace == "orthodontics"
    assert triaged.audit_passed is True


def test_triage_banned_practice_exact_match():
    state = PipelineState(raw_topic="bone smashing jawline")
    triaged = SafetyTriageAgent.triage(state)

    assert triaged.risk_category == "banned"
    assert triaged.audit_passed is False
    assert triaged.is_crisis_routed is True
    assert "bone smashing" in triaged.rejection_reason.lower()
    assert triaged.crisis_payload["violation_id"] == "BONE_SMASHING"


def test_triage_fuzzy_evasion_match():
    # Test leetspeak and obfuscated text: "b0ne smash1ng"
    is_banned, pattern, match = check_banned_topic("b0ne smash1ng tutorial")
    assert is_banned is True
    assert pattern["id"] == "BONE_SMASHING"


def test_triage_toxic_slang():
    state = PipelineState(raw_topic="hunter eyes or rope protocol")
    triaged = SafetyTriageAgent.triage(state)

    assert triaged.risk_category == "banned"
    assert triaged.audit_passed is False
    assert triaged.is_crisis_routed is True
