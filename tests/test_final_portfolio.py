from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

from surgery_optim.instances import load_instance
from surgery_optim.objective import quality
from surgery_optim.portfolio import run_portfolio
from surgery_optim.tabu import TabuConfig, run_tabu


ROOT = Path(__file__).resolve().parents[1]
INSTANCE = ROOT / "instances/standard/HOSP-STD-15-01.yaml"


def test_components_reproduce_engines_and_preserve_best_feasible_result():
    context = load_instance(INSTANCE)
    config = TabuConfig()
    result = run_portfolio(context, seed=60, budget=120, config=config)
    component_config = replace(config, evaluation_budget=60)
    expected_uniform = run_tabu(context, 60, "uniform", component_config)
    expected_dmab = run_tabu(context, 60, "dmab", component_config)
    for actual, expected in (
        (result.uniform, expected_uniform), (result.dmab, expected_dmab)
    ):
        assert actual.best_solution == expected.best_solution
        assert actual.final_quality == expected.final_quality
        assert actual.trace == expected.trace
        assert actual.evaluations == expected.evaluations == 60
    assert result.uniform.initial_objective == result.dmab.initial_objective
    assert result.evaluations == result.feasible_evaluations == 120
    assert result.final_quality.objective == min(
        result.uniform.final_quality.objective, result.dmab.final_quality.objective
    )
    assert quality(context, result.best_solution) == result.final_quality
    assert len(result.schedule) == 2 * len(context.jobs)
    assert result.runtime_seconds >= (
        result.uniform.runtime_seconds + result.dmab.runtime_seconds
    )


def test_budget_covers_initialisations_and_final_partial_batches():
    context = load_instance(INSTANCE)
    result = run_portfolio(context, seed=61, budget=72)
    assert result.uniform.evaluations == result.dmab.evaluations == 36
    assert result.evaluations == 72
    assert result.uniform.trace[-1]["distinct_candidates"] == 6
    assert result.dmab.trace[-1]["distinct_candidates"] == 6


@pytest.mark.parametrize("budget", [59, 58, 120.0, True])
def test_invalid_budgets_are_rejected(budget):
    context = load_instance(INSTANCE)
    with pytest.raises(ValueError, match="budget"):
        run_portfolio(context, seed=60, budget=budget)


def test_cli_exports_inspectable_selected_schedule(tmp_path):
    output = tmp_path / "portfolio.json"
    completed = subprocess.run(
        [sys.executable, "-m", "surgery_optim.portfolio", "--instance", str(INSTANCE),
         "--seed", "60", "--budget", "120", "--output", str(output)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert document["evaluations"] == document["total_budget"] == 120
    assert document["uniform"]["evaluations"] == document["dmab"]["evaluations"] == 60
    assert document["selected_policy"] in ("uniform", "dmab")
    assert len(document["schedule"]) == 30
    assert document["best_solution"] == document[document["selected_policy"]]["best_solution"]
    assert document["final_quality"]["objective"] == min(
        document["uniform"]["final_quality"]["objective"],
        document["dmab"]["final_quality"]["objective"],
    )
    assert "evaluations=120" in completed.stdout
