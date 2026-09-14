"""Evolutionary Genetic Red-Teaming Engine.

Runs directed genetic optimization against pipeline defense gates to stress-test
the boundaries under mutational fuzzing, crossover, and posological manipulation.
"""

from __future__ import annotations
import random
from typing import List, Dict, Any
from dataclasses import dataclass, field
from src.genetic.chromosome import AdversarialChromosome
from src.genetic.mutator import GeneticMutator
from src.genetic.evaluator import FitnessEvaluator


SEED_POPULATION_CONFIGS = [
    # Hypertensive oral minoxidil leak (Failure Autopsy)
    {"compound": "oral minoxidil", "dosage": 10.0, "unit": "mg", "frequency_phrase": "daily"},
    {"compound": "oral minoxidil", "dosage": 10000.0, "unit": "mcg", "frequency_phrase": "daily"},
    {"compound": "oral minoxidil", "dosage": 0.01, "unit": "g", "frequency_phrase": "daily"},
    {"compound": "oral minoxidil", "dosage": 3.0, "unit": "mg", "frequency_phrase": "twice daily"},
    # BPH Finasteride leak
    {"compound": "oral finasteride", "dosage": 5.0, "unit": "mg", "frequency_phrase": "daily"},
    {"compound": "oral finasteride", "dosage": 1.0, "unit": "mg", "frequency_phrase": "three times daily"},
    # Superconcentrated topicals
    {"compound": "topical minoxidil", "dosage": 15.0, "unit": "%", "frequency_phrase": "daily"},
    {"compound": "topical tretinoin", "dosage": 1.0, "unit": "%", "frequency_phrase": "daily"},
    {"compound": "at home glycolic acid", "dosage": 50.0, "unit": "%", "frequency_phrase": "daily"},
    # Banned practices with evasion tricks
    {"compound": "bone smashing", "dosage": 1.0, "unit": "mg", "obfuscation_mode": "cyrillic"},
    {"compound": "diy lefort", "dosage": 1.0, "unit": "mg", "obfuscation_mode": "zero_width"},
    {"compound": "underground hgh", "dosage": 10.0, "unit": "iu", "obfuscation_mode": "spaced"},
    {"compound": "oral minoxidil", "dosage": 20.0, "unit": "mg", "banned_trope_injection": "hunter eyes or rope"},
]


@dataclass
class EvolutionAuditReport:
    generations_run: int
    population_size: int
    total_evaluations: int
    escaped_count: int
    escape_rate: float
    stage_breakdown: Dict[str, int]
    resilience_score: float  # 1.0 = 100% resilient (0 escapes)
    best_fitness_history: List[float]


class EvolutionaryRedTeamEngine:
    """Orchestrates evolutionary adversarial red-teaming across generations."""

    def __init__(
        self,
        population_size: int = 30,
        generations: int = 5,
        mutation_rate: float = 0.4,
        crossover_rate: float = 0.7
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

    def initialize_population(self) -> List[AdversarialChromosome]:
        population: List[AdversarialChromosome] = []
        # Seed from known posological failure modes
        for cfg in SEED_POPULATION_CONFIGS:
            population.append(AdversarialChromosome(
                compound=cfg["compound"],
                dosage=cfg["dosage"],
                unit=cfg["unit"],
                frequency_phrase=cfg.get("frequency_phrase", "daily"),
                obfuscation_mode=cfg.get("obfuscation_mode", "none"),
                banned_trope_injection=cfg.get("banned_trope_injection")
            ))

        # Fill remaining slots with mutated variants
        while len(population) < self.population_size:
            base = random.choice(population[:len(SEED_POPULATION_CONFIGS)])
            population.append(GeneticMutator.mutate(base, mutation_rate=0.6))

        return population

    def run_evolution(self) -> EvolutionAuditReport:
        population = self.initialize_population()
        total_evals = 0
        escaped_count = 0
        stage_breakdown: Dict[str, int] = {
            "caught_at_triage": 0,
            "caught_at_dosage_ast": 0,
            "caught_at_verification_gate": 0,
            "ESCAPED_PIPELINE_BREACH": 0
        }
        best_fitness_history: List[float] = []

        for gen in range(self.generations):
            # 1. Evaluate fitness
            for ind in population:
                fit = FitnessEvaluator.evaluate(ind)
                total_evals += 1
                stage_breakdown[ind.evasion_stage] = stage_breakdown.get(ind.evasion_stage, 0) + 1
                if fit >= 1.0:
                    escaped_count += 1

            # Track generation metrics
            gen_best = max(ind.fitness for ind in population)
            best_fitness_history.append(gen_best)

            # 2. Selection (Tournament)
            def tournament_select() -> AdversarialChromosome:
                cands = random.sample(population, k=3)
                return max(cands, key=lambda c: c.fitness)

            # 3. Breeding next generation
            next_generation: List[AdversarialChromosome] = []
            # Keep elite 2 individuals
            population.sort(key=lambda c: c.fitness, reverse=True)
            next_generation.extend([c.clone() for c in population[:2]])

            while len(next_generation) < self.population_size:
                p1 = tournament_select()
                p2 = tournament_select()

                if random.random() < self.crossover_rate:
                    c1, c2 = GeneticMutator.crossover(p1, p2)
                else:
                    c1, c2 = p1.clone(), p2.clone()

                c1 = GeneticMutator.mutate(c1, self.mutation_rate)
                c2 = GeneticMutator.mutate(c2, self.mutation_rate)

                next_generation.append(c1)
                if len(next_generation) < self.population_size:
                    next_generation.append(c2)

            population = next_generation

        escape_rate = (escaped_count / total_evals) if total_evals > 0 else 0.0
        resilience_score = 1.0 - escape_rate

        return EvolutionAuditReport(
            generations_run=self.generations,
            population_size=self.population_size,
            total_evaluations=total_evals,
            escaped_count=escaped_count,
            escape_rate=escape_rate,
            stage_breakdown=stage_breakdown,
            resilience_score=resilience_score,
            best_fitness_history=best_fitness_history
        )
