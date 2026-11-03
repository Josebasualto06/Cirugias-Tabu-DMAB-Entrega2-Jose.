"""Task 3b of the Entrega 2 protocol: comparisons C1-C4 under congestion.

Runs the frozen configuration on instances/congestion, seeds 90-109:

    python -m experiments.study_congestion --workers 12

Each pair executes four trajectories and reports six alternatives: the 3,030
prefix of uniform Tabu is reused, so alternatives are not independent runs.
Partial results are saved after every pair and resume only with unchanged code,
data and seeds. No statistic is computed until every pair has finished.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from experiments.entrega2_common import (
    ROOT, base_manifest, instance_hashes, prepare_output, read_rows, write_manifest, write_rows,
)
from experiments.portfolio_search import SearchTrajectory
from experiments.power_analysis import variance_components
from experiments.run_study import holm
from surgery_optim.baselines import construct_baseline
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality
from surgery_optim.tabu import TabuConfig, run_tabu


SEEDS = tuple(range(90, 110))
HALF_BUDGET = 3030
TOTAL_BUDGET = 6060
SECOND_SEED_OFFSET = 1_000_000
BLOCK = 150
PRACTICAL_THRESHOLD = 0.25
BOOTSTRAP_REPLICATES = 5000
BOOTSTRAP_SEED = 20261102
METHODS = ("uniform3030", "dmab3030", "ucb3030", "uniform6060",
           "two_uniform6060", "fixed_portfolio6060")
LABELS = {
    "uniform3030": "Tabu uniforme (3.030)", "dmab3030": "Tabu + D-MAB (3.030)",
    "ucb3030": "Tabu + UCB1 (3.030)", "uniform6060": "Tabu prolongado (6.060)",
    "two_uniform6060": "Dos Tabu (6.060)", "fixed_portfolio6060": "Cartera fija (6.060)",
}
COMPARISONS = (
    ("C1", "dmab3030", "uniform3030", 3030),
    ("C2", "fixed_portfolio6060", "uniform6060", 6060),
    ("C3", "fixed_portfolio6060", "two_uniform6060", 6060),
    ("C4", "dmab3030", "ucb3030", 3030),
)
FIELDS = ("instance_id", "size", "seed", "method", "objective", "makespan", "blocked",
          "max_wait", "evaluations", "feasible_evaluations", "runtime_seconds",
          "dmab_restarts", "repaired_candidates", "last_improvement", "selected_path")


def advance_tracked(trajectory: SearchTrajectory, target: int, last: int) -> int:
    """Advance to ``target``; return the block of the latest improvement."""
    while trajectory.spent < target:
        before = trajectory.best
        trajectory.advance(min(BLOCK, target - trajectory.spent))
        if trajectory.best < before:
            last = trajectory.spent
    return last


def evaluate_pair(task: tuple[str, int]) -> dict:
    path, seed = task
    context = load_instance(path)
    config = TabuConfig(evaluation_budget=HALF_BUDGET)
    rows, solutions = [], []

    def record(method, solution, evaluations, feasible, runtime, restarts=0, repaired=0,
               last=0, selected=""):
        measured = quality(context, solution)
        rows.append(dict(zip(FIELDS, (
            context.instance_id, len(context.jobs), seed, method, measured.objective,
            measured.makespan, measured.blocked_minutes, measured.max_wait_minutes,
            evaluations, feasible, runtime, restarts, repaired, last, selected,
        ))))
        solutions.append({"instance_id": context.instance_id, "seed": seed,
                          "method": method, "solution": solution})
        return measured

    try:
        started = time.perf_counter()
        uniform = SearchTrajectory(context, seed, "uniform", config)
        u_last = advance_tracked(uniform, HALF_BUDGET, uniform.spent)
        u_time = time.perf_counter() - started
        u_solution, u_feasible, u_repaired = uniform.best_solution, uniform.feasible, uniform.repaired
        u_quality = record("uniform3030", u_solution, HALF_BUDGET, u_feasible, u_time,
                           repaired=u_repaired, last=u_last)

        started = time.perf_counter()
        last_long = advance_tracked(uniform, TOTAL_BUDGET, u_last)
        record("uniform6060", uniform.best_solution, TOTAL_BUDGET, uniform.feasible,
               u_time + time.perf_counter() - started, repaired=uniform.repaired, last=last_long)

        started = time.perf_counter()
        dynamic = SearchTrajectory(context, seed, "dmab", config)
        d_last = advance_tracked(dynamic, HALF_BUDGET, dynamic.spent)
        d_time = time.perf_counter() - started
        d_quality = record("dmab3030", dynamic.best_solution, HALF_BUDGET, dynamic.feasible, d_time,
                           dynamic.bandit.restarts, dynamic.repaired, d_last)

        keeps_uniform = (u_quality.objective, u_quality.makespan) <= (d_quality.objective,
                                                                      d_quality.makespan)
        record("fixed_portfolio6060", u_solution if keeps_uniform else dynamic.best_solution,
               TOTAL_BUDGET, u_feasible + dynamic.feasible, u_time + d_time,
               dynamic.bandit.restarts, u_repaired + dynamic.repaired,
               u_last if keeps_uniform else d_last, "uniform" if keeps_uniform else "dmab")

        ucb = run_tabu(context, seed, "ucb", config)
        improved = [row["evaluations"] for earlier, row in zip(ucb.trace, ucb.trace[1:])
                    if row["best_objective"] < earlier["best_objective"]]
        record("ucb3030", ucb.best_solution, HALF_BUDGET, ucb.feasible_evaluations,
               ucb.runtime_seconds, repaired=ucb.repaired_candidates,
               last=improved[-1] if improved else config.population_size)

        started = time.perf_counter()
        restart = SearchTrajectory(context, seed + SECOND_SEED_OFFSET, "uniform", config)
        r_last = advance_tracked(restart, HALF_BUDGET, restart.spent)
        r_time = time.perf_counter() - started
        r_quality = quality(context, restart.best_solution)
        keeps_first = (u_quality.objective, u_quality.makespan) <= (r_quality.objective,
                                                                    r_quality.makespan)
        record("two_uniform6060", u_solution if keeps_first else restart.best_solution,
               TOTAL_BUDGET, u_feasible + restart.feasible, u_time + r_time,
               repaired=u_repaired + restart.repaired, last=u_last if keeps_first else r_last,
               selected="first" if keeps_first else "second")
    except (AssertionError, RuntimeError, ValueError) as error:
        return {"failed": {"instance_id": context.instance_id, "seed": seed,
                           "error": f"{type(error).__name__}: {str(error)[:160]}"}}
    return {"rows": rows, "solutions": solutions}


def clustered_interval(groups: list[np.ndarray], rng: np.random.Generator) -> tuple[float, float]:
    """Hierarchical bootstrap: instances, then paired seeds within instance."""
    means = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled = rng.integers(len(groups), size=len(groups))
        means.append(np.mean([
            np.mean(group[rng.integers(len(group), size=len(group))])
            for group in (groups[index] for index in sampled)
        ]))
    return tuple(float(value) for value in np.quantile(means, [.025, .975]))


def analyze(output: Path, paths: list[Path]) -> dict:
    rows = read_rows(output / "runs.csv")
    failures = read_rows(output / "failures.csv")
    indexed = {(r["instance_id"], int(r["seed"]), r["method"]): r for r in rows}
    pairs = sorted({(r["instance_id"], int(r["seed"])) for r in rows})
    instances = sorted({instance for instance, _ in pairs})
    seeds = sorted({seed for _, seed in pairs})
    expected = len(paths) * len(SEEDS)
    fail_share = len(failures) / expected

    def value(instance, seed, method, field="objective"):
        return float(indexed[instance, seed, method][field])

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    results = []
    for code, method, reference, budget in COMPARISONS:
        groups = {instance: [] for instance in instances}
        for instance, seed in pairs:
            groups[instance].append(value(instance, seed, method) - value(instance, seed, reference))
        arrays = [np.asarray(groups[instance]) for instance in instances]
        means = [float(array.mean()) for array in arrays]
        flat = np.concatenate(arrays)
        low, high = clustered_interval(arrays, rng)
        results.append({
            "comparison": code, "method": method, "reference": reference, "budget": budget,
            "pairs": len(flat), "instances": len(instances),
            "mean_difference": float(flat.mean()), "ci_low": low, "ci_high": high,
            "wins": int((flat < -PRACTICAL_THRESHOLD).sum()),
            "similar": int((np.abs(flat) <= PRACTICAL_THRESHOLD).sum()),
            "losses": int((flat > PRACTICAL_THRESHOLD).sum()),
            "instances_better": sum(mean < -1e-9 for mean in means),
            "instances_worse": sum(mean > 1e-9 for mean in means),
            "wilcoxon_p": float(wilcoxon(means, zero_method="zsplit").pvalue),
        })
    for row, adjusted in zip(results, holm([row["wilcoxon_p"] for row in results])):
        row["holm_p"] = adjusted
    write_rows(output / "comparisons.csv", results)

    descriptive = []
    for method in METHODS:
        current = [indexed[instance, seed, method] for instance, seed in pairs]
        objective = np.array([float(r["objective"]) for r in current])
        makespan = np.array([float(r["makespan"]) for r in current])
        blocked = np.array([float(r["blocked"]) for r in current])
        descriptive.append({
            "method": method, "budget": int(current[0]["evaluations"]),
            "mean_objective": float(objective.mean()), "mean_makespan": float(makespan.mean()),
            "mean_blocked": float(blocked.mean()),
            "mean_max_wait": float(np.mean([float(r["max_wait"]) for r in current])),
            "waiting_share": float((blocked > 0).mean()),
            "mean_objective_minus_makespan": float((objective - makespan).mean()),
            "feasible_share": sum(int(r["feasible_evaluations"]) for r in current)
            / sum(int(r["evaluations"]) for r in current),
            "median_last_improvement": float(np.median([int(r["last_improvement"]) for r in current])),
            "median_runtime_seconds": float(np.median([float(r["runtime_seconds"]) for r in current])),
        })
    write_rows(output / "descriptive.csv", descriptive)

    primary = next(row for row in results if row["comparison"] == "C1")
    supported = (primary["holm_p"] < 0.05 and primary["ci_high"] < 0
                 and primary["mean_difference"] <= -PRACTICAL_THRESHOLD)
    complete = [instance for instance in instances
                if all((instance, seed) in {pair for pair in pairs} for seed in seeds)]
    matrix = np.array([[value(i, s, "dmab3030") - value(i, s, "uniform3030") for s in seeds]
                       for i in complete])
    components = variance_components(matrix)
    realized = {"sd_difference": float(matrix.std(ddof=1)),
                "sd_instance_means": float(matrix.mean(axis=1).std(ddof=1)), **components}

    lines = ["# Estudio de congestión: comparaciones C1–C4", "",
             f"{len(instances)} instancias, {len(seeds)} semillas (90–109), {len(pairs)} pares. "
             f"Pares fallidos: {len(failures)} de {expected}. Menor es mejor; la diferencia es "
             "alternativa menos referencia.", ""]
    for budget in (3030, 6060):
        lines += [f"## Presupuesto {budget:,}".replace(",", "."), "",
                  "| Id | Comparación | Media dif. | IC 95 % agrupado | Mejora / similar / empeora | "
                  "Instancias mejor / peor | p | p Holm |",
                  "|---|---|---:|---|---|---|---:|---:|"]
        for row in results:
            if row["budget"] != budget:
                continue
            lines.append(
                f"| {row['comparison']} | {LABELS[row['method']]} vs {LABELS[row['reference']]} | "
                f"{row['mean_difference']:+.3f} | [{row['ci_low']:+.3f}, {row['ci_high']:+.3f}] | "
                f"{row['wins']} / {row['similar']} / {row['losses']} | "
                f"{row['instances_better']} / {row['instances_worse']} | "
                f"{row['wilcoxon_p']:.3f} | {row['holm_p']:.3f} |")
        lines += ["", "| Alternativa | Objetivo medio | Makespan medio | Espera total media | "
                  "Espera máxima media | Finales con espera | Última mejora (mediana) | Factibles |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for row in descriptive:
            if row["budget"] != budget:
                continue
            lines.append(
                f"| {LABELS[row['method']]} | {row['mean_objective']:.3f} | "
                f"{row['mean_makespan']:.3f} | {row['mean_blocked']:.3f} | "
                f"{row['mean_max_wait']:.3f} | {row['waiting_share']:.1%} | "
                f"{row['median_last_improvement']:.0f} | {row['feasible_share']:.1%} |")
        lines.append("")
    lines += ["## Decisión pre-registrada sobre H1", "",
              f"C1: media {primary['mean_difference']:+.3f}, IC [{primary['ci_low']:+.3f}, "
              f"{primary['ci_high']:+.3f}], p Holm {primary['holm_p']:.3f}. "
              + ("**H1 queda respaldada.**" if supported else "**H1 no queda respaldada.**"),
              "La falta de significación no prueba equivalencia entre métodos.", "",
              "## Variabilidad realizada de C1", "",
              f"DE de la diferencia {realized['sd_difference']:.3f}; DE de medias por instancia "
              f"{realized['sd_instance_means']:.3f}; ICC {realized['icc']:.3f}.", "",
              "Las alternativas de una misma pareja comparten prefijos y no son independientes. "
              "Estos resultados no se mezclan con estudios anteriores.", ""]
    (output / "ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")
    return {"h1_supported": supported, "failed_pairs": len(failures), "pairs": len(pairs),
            "exploratory_after_failures": fail_share > 0.01, "realized_variability": realized}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--directory", type=Path, default=ROOT / "instances/congestion")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_congestion_90_109")
    args = parser.parse_args()
    output = prepare_output(args.output)
    paths = sorted(args.directory.resolve().glob("HOSP-CONG-*.yaml"))
    if not paths:
        raise FileNotFoundError("the congestion catalog has not been generated")
    manifest = base_manifest("entrega2-congestion-v1", Path(__file__),
                             ROOT / "experiments/portfolio_search.py",
                             ROOT / "experiments/power_analysis.py")
    manifest.update({
        "instance_sha256": instance_hashes(paths), "seeds": SEEDS, "methods": METHODS,
        "search_config": "TabuConfig() defaults", "half_budget": HALF_BUDGET,
        "total_budget": TOTAL_BUDGET, "second_seed_offset": SECOND_SEED_OFFSET,
        "bootstrap": {"replicates": BOOTSTRAP_REPLICATES, "seed": BOOTSTRAP_SEED},
        "practical_threshold": PRACTICAL_THRESHOLD,
        "statistics": "Wilcoxon on instance means, Holm over C1-C4, hierarchical bootstrap",
        "pairing": "same seed; four trajectories per pair; uniform prefix reused",
    })
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("code_sha256", "instance_sha256", "seeds"):
            if json.loads(json.dumps(previous[key])) != json.loads(json.dumps(manifest[key])):
                raise ValueError(f"cannot resume changed protocol: {key}")
    write_manifest(output, manifest)

    run_path = output / "runs.csv"
    existing = read_rows(run_path)
    done = {(row["instance_id"], int(row["seed"])) for row in existing}
    done |= {(row["instance_id"], int(row["seed"])) for row in read_rows(output / "failures.csv")}
    tasks = [(str(path), seed) for path in paths for seed in SEEDS if (path.stem, seed) not in done]
    with run_path.open("a", newline="", encoding="utf-8") as runs, \
            (output / "solutions.jsonl").open("a", encoding="utf-8") as solutions, \
            (output / "failures.csv").open("a", newline="", encoding="utf-8") as failed:
        writer = csv.DictWriter(runs, fieldnames=FIELDS)
        failure_writer = csv.DictWriter(failed, fieldnames=("instance_id", "seed", "error"))
        if not existing:
            writer.writeheader()
        if (output / "failures.csv").stat().st_size == 0:
            failure_writer.writeheader()
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(evaluate_pair, task) for task in tasks]
            for count, future in enumerate(as_completed(futures), 1):
                result = future.result()
                if "failed" in result:
                    failure_writer.writerow(result["failed"])
                else:
                    writer.writerows(result["rows"])
                    for row in result["solutions"]:
                        solutions.write(json.dumps(row, ensure_ascii=False) + "\n")
                runs.flush(); solutions.flush(); failed.flush()
                if count % 40 == 0 or count == len(futures):
                    print(f"{count}/{len(futures)} pares", flush=True)

    baselines = []
    for path in paths:
        context = load_instance(path)
        for rule in ("fifo", "spt", "lpt"):
            measured = quality(context, construct_baseline(context, rule))
            baselines.append({"instance_id": context.instance_id, "rule": rule,
                              "objective": measured.objective, "makespan": measured.makespan,
                              "blocked": measured.blocked_minutes,
                              "max_wait": measured.max_wait_minutes})
    write_rows(output / "baselines.csv", baselines)
    manifest["outcome"] = analyze(output, paths)
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print((output / "ANALYSIS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
