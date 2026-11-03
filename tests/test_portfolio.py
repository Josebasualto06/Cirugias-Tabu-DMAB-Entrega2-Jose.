from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from experiments.portfolio_search import ContextualAllocator, SearchTrajectory, run_allocation
from surgery_optim import TabuConfig, load_instance, run_tabu
from surgery_optim.objective import quality


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("policy", ["uniform", "dmab"])
@pytest.mark.parametrize("seed", [0, 60])
def test_pausing_preserves_exact_search_trajectory(policy, seed):
    context = load_instance(ROOT / "instances/standard/HOSP-STD-15-01.yaml")
    config = TabuConfig(evaluation_budget=630)
    expected = run_tabu(context, seed, policy, config)
    paused = SearchTrajectory(context, seed, policy, config)
    for _ in range(4):
        paused.advance(150)
    assert paused.spent == expected.evaluations
    assert paused.feasible == expected.feasible_evaluations
    assert paused.best_solution == expected.best_solution
    assert paused.best == expected.final_quality.objective
    assert paused.repaired == expected.repaired_candidates


def test_protected_allocator_charges_trials_and_keeps_complete_baseline():
    context = load_instance(ROOT / "instances/standard/HOSP-STD-15-02.yaml")
    baseline = run_tabu(context, 60, "uniform", TabuConfig())
    result = run_allocation(context, 60, budget=3660, protected=True)
    assert result.floor_objective == baseline.final_quality.objective
    assert result.objective <= baseline.final_quality.objective
    assert result.evaluations == result.feasible_evaluations == 3660
    assert result.uniform_evaluations + result.dmab_evaluations == 3660
    assert result.uniform_evaluations >= 3030
    assert result.dmab_evaluations >= 180
    assert quality(context, result.best_solution).objective == result.objective
    repeat = run_allocation(context, 60, budget=3660, protected=True)
    assert repeat.best_solution == result.best_solution
    assert repeat.decisions == result.decisions


def test_linear_update_matches_direct_regularized_solution():
    allocator = ContextualAllocator()
    rng = np.random.default_rng(17)
    dimension = len(allocator.target[0])
    x = rng.normal(size=(20, dimension))
    y = rng.random(20)
    for row, reward in zip(x, y):
        allocator.update(0, row, reward)
    expected = np.linalg.solve(np.eye(dimension) + x.T @ x, x.T @ y)
    assert np.allclose(allocator.inverse[0] @ allocator.target[0], expected)
