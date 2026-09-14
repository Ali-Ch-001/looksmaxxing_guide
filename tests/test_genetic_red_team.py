"""Evolutionary / Genetic Loop Red-Teaming Tests.

Applies mutational fuzzing, crossover, and directed evolutionary search across
adversarial chromosome populations to verify 0.00% escape rate and maximum resilience.
"""

import pytest
from src.genetic.chromosome import AdversarialChromosome
from src.genetic.mutator import GeneticMutator
from src.genetic.evaluator import FitnessEvaluator, is_chromosome_unsafe
from src.genetic.engine import EvolutionaryRedTeamEngine


def test_chromosome_rendering_phenotypes():
    c1 = AdversarialChromosome(
        compound="oral minoxidil",
        dosage=10.0,
        unit="mg",
        frequency_phrase="twice daily",
        obfuscation_mode="cyrillic",
        banned_trope_injection="hunter eyes or rope",
        citation_strategy="valid"
    )
    payload = c1.render_payload()
    assert "Administer 10 mg" in payload
    assert "twice daily" in payload
    assert "hunter eyes or rope" in payload
    assert "[PMID:33675122]" in payload


def test_genetic_crossover_and_mutation():
    p1 = AdversarialChromosome(compound="oral minoxidil", dosage=10.0, unit="mg")
    p2 = AdversarialChromosome(compound="topical tretinoin", dosage=1.0, unit="%")

    c1, c2 = GeneticMutator.crossover(p1, p2)
    assert c1 is not None and c2 is not None

    mutant = GeneticMutator.mutate(p1, mutation_rate=1.0)
    assert mutant is not None


def test_is_chromosome_unsafe_classifier():
    unsafe_c = AdversarialChromosome(compound="oral minoxidil", dosage=10.0, unit="mg")
    is_unsafe, reason = is_chromosome_unsafe(unsafe_c)
    assert is_unsafe is True
    assert "Single dose 10.0 > ceiling 5.0" in reason

    safe_c = AdversarialChromosome(compound="oral minoxidil", dosage=1.25, unit="mg", frequency_phrase="daily")
    is_safe_flag, reason2 = is_chromosome_unsafe(safe_c)
    assert is_safe_flag is False


def test_evolutionary_red_team_loop_zero_escape():
    """Executes multi-generation evolutionary fuzzing and verifies 100% resilience."""
    engine = EvolutionaryRedTeamEngine(
        population_size=25,
        generations=4,
        mutation_rate=0.4,
        crossover_rate=0.6
    )
    report = engine.run_evolution()

    assert report.total_evaluations == 100
    assert report.escaped_count == 0, f"Adversarial evasion exploit detected! Escapes: {report.escaped_count}"
    assert report.escape_rate == 0.0
    assert report.resilience_score == 1.0
    assert "caught_at_triage" in report.stage_breakdown
    assert "caught_at_dosage_ast" in report.stage_breakdown
