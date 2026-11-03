"""Fixed-budget portfolio of uniform Tabu and Tabu with D-MAB.

Both trajectories use the same instance, seed and initialisation settings.
The best feasible result is retained. The operator selector learns online
inside the D-MAB trajectory; budget allocation between trajectories is fixed.
"""

from __future__ import annotations

import argparse
import copy
import json
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal

from ..instances import load_instance
from ..model import InstanceContext
from ..objective import Quality
from ..scheduler import ScheduleEntry, schedule_instance_solution
from ..tabu import TabuConfig, TabuResult, run_tabu


@dataclass(frozen=True, slots=True)
class PortfolioResult:
    """Both component results and the chosen feasible calendar."""

    seed: int
    instance_id: str
    instance_digest: str
    total_budget: int
    component_config: TabuConfig
    uniform: TabuResult
    dmab: TabuResult
    selected_policy: Literal["uniform", "dmab"]
    final_quality: Quality
    best_solution: dict[str, Any]
    schedule: tuple[ScheduleEntry, ...]
    evaluations: int
    feasible_evaluations: int
    runtime_seconds: float


def run_portfolio(
    context: InstanceContext,
    seed: int,
    budget: int = 6060,
    config: TabuConfig = TabuConfig(),
) -> PortfolioResult:
    """Run the two trajectories sequentially with half the total budget each.

    ``budget`` counts candidate evaluations during the search, including
    the initial population in each component. It must be an even integer and cover
    both populations. ``config.evaluation_budget`` is replaced by
    ``budget // 2``; the remaining settings are shared. A final partial
    candidate batch is supported, as in ``run_tabu``.

    Identical seeds produce identical initial populations. Subsequent
    trajectories differ as operators consume random draws differently.
    Preserving the uniform component only protects its half-budget result;
    it does not guarantee improvement over uniform Tabu using the full
    budget, nor does either method certify global optimality.
    """
    if isinstance(budget, bool) or not isinstance(budget, int):
        raise ValueError("total budget must be an even integer")
    if budget % 2 != 0:
        raise ValueError("total budget must be even to split it equally")
    if budget < 2 * config.population_size:
        raise ValueError(
            "total budget must cover both initial populations "
            f"(at least {2 * config.population_size} evaluations)"
        )
    component_config = replace(config, evaluation_budget=budget // 2)
    started = time.perf_counter()
    uniform = run_tabu(context, seed, "uniform", component_config)
    dmab = run_tabu(context, seed, "dmab", component_config)
    selected = min(
        (uniform, dmab),
        key=lambda item: (item.final_quality.objective, item.final_quality.makespan),
    )
    solution = copy.deepcopy(selected.best_solution)
    _, schedule = schedule_instance_solution(context, solution)
    # Final calendar validation is separate from the charged search budget.
    evaluations = uniform.evaluations + dmab.evaluations
    if evaluations != budget:
        raise RuntimeError("component evaluations do not match the total budget")
    return PortfolioResult(
        seed=seed,
        instance_id=context.instance_id,
        instance_digest=context.digest,
        total_budget=budget,
        component_config=component_config,
        uniform=uniform,
        dmab=dmab,
        selected_policy=selected.policy,
        final_quality=selected.final_quality,
        best_solution=solution,
        schedule=schedule,
        evaluations=evaluations,
        feasible_evaluations=uniform.feasible_evaluations + dmab.feasible_evaluations,
        runtime_seconds=time.perf_counter() - started,
    )


def main(argv: list[str] | None = None) -> None:
    """Save the portfolio, its component diagnostics and selected schedule."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, required=True, help="instance YAML file")
    parser.add_argument("--seed", type=int, default=60, help="shared initialisation seed")
    parser.add_argument("--budget", type=int, default=6060, help="total evaluation budget")
    parser.add_argument("--output", type=Path, required=True, help="destination JSON file")
    args = parser.parse_args(argv)
    try:
        context = load_instance(args.instance)
        result = run_portfolio(context, args.seed, args.budget)
        document = {"schema_version": 1, **asdict(result)}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(document, ensure_ascii=False, allow_nan=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(
        f"{result.instance_id}: selected={result.selected_policy}, "
        f"objective={result.final_quality.objective:.6f}, "
        f"makespan={result.final_quality.makespan:.3f}, "
        f"evaluations={result.evaluations}, "
        f"runtime_seconds={result.runtime_seconds:.3f}\n{args.output}"
    )
