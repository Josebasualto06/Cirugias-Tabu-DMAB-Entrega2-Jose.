"""Entrega 3 protocol: confirmatory comparison of UCB1 against uniform Tabu.

Runs the frozen configuration on instances/congestion with the fresh seeds
120-139 and 3,030 evaluations per trajectory:

    python -m experiments.confirm_ucb1 --workers 12

There is one pre-registered comparison (docs/protocolo-entrega3.md). Partial
results are saved after every pair and resume only with unchanged code, data
and seeds. No statistic is computed until every pair has finished.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from experiments.entrega2_common import (
    ROOT, base_manifest, instance_hashes, prepare_output, read_rows, sha256, write_manifest,
    write_rows,
)
from experiments.portfolio_search import SearchTrajectory
from experiments.power_analysis import t_test_power, variance_components
from experiments.study_congestion import (
    BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED, PRACTICAL_THRESHOLD, advance_tracked,
    clustered_interval,
)
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality
from surgery_optim.tabu import TabuConfig, run_tabu


PROTOCOL = "docs/protocolo-entrega3.md"
PARENT_PROTOCOL = "docs/protocolo-entrega2.md"
SEEDS = tuple(range(120, 140))
BUDGET = 3030
ALPHA = 0.05
METHODS = ("uniform3030", "ucb3030")
LABELS = {"uniform3030": "Tabu uniforme (3.030)", "ucb3030": "Tabu + UCB1 (3.030)"}
COMPARISON = ("E1", "ucb3030", "uniform3030", BUDGET)
PLANNING_SOURCE = "experiments/results/entrega2_congestion_90_109/runs.csv"
FIELDS = ("instance_id", "size", "seed", "method", "objective", "makespan", "blocked",
          "max_wait", "evaluations", "feasible_evaluations", "runtime_seconds",
          "dmab_restarts", "repaired_candidates", "last_improvement")


def evaluate_pair(task: tuple[str, int]) -> dict:
    """Run uniform Tabu and Tabu + UCB1 on one instance with one seed."""
    path, seed = task
    context = load_instance(path)
    config = TabuConfig(evaluation_budget=BUDGET)
    rows, solutions = [], []

    def record(method, solution, evaluations, feasible, runtime, restarts, repaired, last):
        measured = quality(context, solution)
        rows.append(dict(zip(FIELDS, (
            context.instance_id, len(context.jobs), seed, method, measured.objective,
            measured.makespan, measured.blocked_minutes, measured.max_wait_minutes,
            evaluations, feasible, runtime, restarts, repaired, last,
        ))))
        solutions.append({"instance_id": context.instance_id, "seed": seed,
                          "method": method, "solution": solution})

    try:
        started = time.perf_counter()
        uniform = SearchTrajectory(context, seed, "uniform", config)
        last = advance_tracked(uniform, BUDGET, uniform.spent)
        record("uniform3030", uniform.best_solution, uniform.spent, uniform.feasible,
               time.perf_counter() - started, 0, uniform.repaired, last)

        ucb = run_tabu(context, seed, "ucb", config)
        improved = [row["evaluations"] for earlier, row in zip(ucb.trace, ucb.trace[1:])
                    if row["best_objective"] < earlier["best_objective"]]
        record("ucb3030", ucb.best_solution, ucb.evaluations, ucb.feasible_evaluations,
               ucb.runtime_seconds, ucb.dmab_restarts, ucb.repaired_candidates,
               improved[-1] if improved else config.population_size)
    except (AssertionError, RuntimeError, ValueError) as error:
        return {"failed": {"instance_id": context.instance_id, "seed": seed,
                           "error": f"{type(error).__name__}: {str(error)[:160]}"}}
    return {"rows": rows, "solutions": solutions}


def planning_power() -> dict:
    """Planning power from the exploratory contrast of seeds 90-109 (protocol, section 7)."""
    rows = read_rows(ROOT / PLANNING_SOURCE)
    objective = {(r["instance_id"], r["seed"], r["method"]): float(r["objective"]) for r in rows}
    instances = sorted({r["instance_id"] for r in rows})
    seeds = sorted({r["seed"] for r in rows})
    means = np.array([
        np.mean([objective[i, s, "ucb3030"] - objective[i, s, "uniform3030"] for s in seeds])
        for i in instances
    ])
    observed, deviation = float(means.mean()), float(means.std(ddof=1))
    effects = {"observed": abs(observed), "half_observed": abs(observed) / 2, "0.65": 0.65}
    return {
        "source": PLANNING_SOURCE, "exploratory_mean_difference": observed,
        "sd_instance_means": deviation, "instances": len(instances), "alpha": ALPHA,
        "t_power": {name: {"effect": effect,
                           "power": t_test_power(len(instances), effect / deviation, ALPHA)}
                    for name, effect in effects.items()},
    }


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

    code, method, reference, budget = COMPARISON
    groups = {instance: [] for instance in instances}
    for instance, seed in pairs:
        groups[instance].append(value(instance, seed, method) - value(instance, seed, reference))
    arrays = [np.asarray(groups[instance]) for instance in instances]
    means = [float(array.mean()) for array in arrays]
    flat = np.concatenate(arrays)
    low, high = clustered_interval(arrays, np.random.default_rng(BOOTSTRAP_SEED))
    p_value = float(wilcoxon(means, zero_method="zsplit").pvalue)
    result = {
        "comparison": code, "method": method, "reference": reference, "budget": budget,
        "pairs": len(flat), "instances": len(instances),
        "mean_difference": float(flat.mean()), "ci_low": low, "ci_high": high,
        "wins": int((flat < -PRACTICAL_THRESHOLD).sum()),
        "similar": int((np.abs(flat) <= PRACTICAL_THRESHOLD).sum()),
        "losses": int((flat > PRACTICAL_THRESHOLD).sum()),
        "instances_better": sum(mean < -1e-9 for mean in means),
        "instances_worse": sum(mean > 1e-9 for mean in means),
        # A single comparison: Holm over a family of one leaves p unchanged.
        "wilcoxon_p": p_value, "holm_p": p_value,
    }
    write_rows(output / "comparisons.csv", [result])

    descriptive = []
    for name in METHODS:
        current = [indexed[instance, seed, name] for instance, seed in pairs]
        objective = np.array([float(r["objective"]) for r in current])
        makespan = np.array([float(r["makespan"]) for r in current])
        blocked = np.array([float(r["blocked"]) for r in current])
        descriptive.append({
            "method": name, "budget": int(current[0]["evaluations"]),
            "mean_objective": float(objective.mean()), "mean_makespan": float(makespan.mean()),
            "mean_blocked": float(blocked.mean()),
            "mean_max_wait": float(np.mean([float(r["max_wait"]) for r in current])),
            "waiting_share": float((blocked > 0).mean()),
            "feasible_share": sum(int(r["feasible_evaluations"]) for r in current)
            / sum(int(r["evaluations"]) for r in current),
            "mean_repaired_share": float(np.mean([
                int(r["repaired_candidates"]) / (int(r["evaluations"]) - 30) for r in current])),
            "median_last_improvement": float(np.median([int(r["last_improvement"]) for r in current])),
            "median_runtime_seconds": float(np.median([float(r["runtime_seconds"]) for r in current])),
        })
    write_rows(output / "descriptive.csv", descriptive)

    supported = (result["holm_p"] < ALPHA and result["ci_high"] < 0
                 and result["mean_difference"] <= -PRACTICAL_THRESHOLD)
    known = set(pairs)
    complete = [instance for instance in instances
                if all((instance, seed) in known for seed in seeds)]
    matrix = np.array([[value(i, s, method) - value(i, s, reference) for s in seeds]
                       for i in complete])
    realized = {"sd_difference": float(matrix.std(ddof=1)),
                "sd_instance_means": float(matrix.mean(axis=1).std(ddof=1)),
                **variance_components(matrix)}

    lines = [
        "# Confirmación pre-registrada: UCB1 sin reinicio frente a Tabu uniforme", "",
        f"{len(instances)} instancias de congestión, {len(seeds)} semillas "
        f"({min(seeds)}–{max(seeds)}), {len(pairs)} pares. Pares fallidos: {len(failures)} de "
        f"{expected}. Menor es mejor; la diferencia es alternativa menos referencia. "
        "Una sola comparación: no hay corrección múltiple.", "",
        "| Id | Comparación | Media dif. | IC 95 % agrupado | Mejora / similar / empeora | "
        "Instancias mejor / peor | p |",
        "|---|---|---:|---|---|---|---:|",
        f"| {code} | {LABELS[method]} vs {LABELS[reference]} | {result['mean_difference']:+.3f} | "
        f"[{result['ci_low']:+.3f}, {result['ci_high']:+.3f}] | "
        f"{result['wins']} / {result['similar']} / {result['losses']} | "
        f"{result['instances_better']} / {result['instances_worse']} | "
        f"{result['wilcoxon_p']:.4f} |", "",
        "| Alternativa | Objetivo medio | Makespan medio | Espera total media | "
        "Espera máxima media | Finales con espera | Reparación media | "
        "Última mejora (mediana) | Factibles |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in descriptive:
        lines.append(
            f"| {LABELS[row['method']]} | {row['mean_objective']:.3f} | "
            f"{row['mean_makespan']:.3f} | {row['mean_blocked']:.3f} | "
            f"{row['mean_max_wait']:.3f} | {row['waiting_share']:.1%} | "
            f"{row['mean_repaired_share']:.1%} | {row['median_last_improvement']:.0f} | "
            f"{row['feasible_share']:.1%} |")
    lines += [
        "", "## Decisión pre-registrada sobre H1c", "",
        f"{code}: media {result['mean_difference']:+.3f}, IC [{result['ci_low']:+.3f}, "
        f"{result['ci_high']:+.3f}], p {result['wilcoxon_p']:.4f}. "
        + ("**H1c queda respaldada.**" if supported else "**H1c no queda respaldada.**"),
        "La regla exige p menor que 0,05, IC completo bajo cero y media de a lo sumo −0,25. "
        "La falta de significación no prueba equivalencia entre métodos.", "",
        "## Variabilidad realizada", "",
        f"DE de la diferencia {realized['sd_difference']:.3f}; DE de medias por instancia "
        f"{realized['sd_instance_means']:.3f}; ICC {realized['icc']:.3f}.", "",
        "Las semillas nuevas sobre el mismo catálogo no miden generalización a otros "
        "hospitales. Estos resultados no se mezclan con estudios anteriores.", "",
    ]
    (output / "ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")
    return {"h1c_supported": supported, "failed_pairs": len(failures), "pairs": len(pairs),
            "exploratory_after_failures": fail_share > 0.01, "realized_variability": realized}


def protocol_commit() -> str:
    return subprocess.check_output(
        ["git", "log", "-n", "1", "--format=%H", "--", PROTOCOL], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--directory", type=Path, default=ROOT / "instances/congestion")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega3_confirmacion_ucb1")
    args = parser.parse_args()
    output = prepare_output(args.output)
    paths = sorted(args.directory.resolve().glob("HOSP-CONG-*.yaml"))
    if not paths:
        raise FileNotFoundError("the congestion catalog has not been generated")
    manifest = base_manifest("entrega3-confirmacion-ucb1-v1", Path(__file__),
                             ROOT / "experiments/portfolio_search.py",
                             ROOT / "experiments/power_analysis.py",
                             ROOT / "experiments/study_congestion.py")
    manifest.update({
        "parent_protocol": {"document": PARENT_PROTOCOL, "sha256": sha256(ROOT / PARENT_PROTOCOL)},
        "protocol_document": PROTOCOL, "protocol_sha256": sha256(ROOT / PROTOCOL),
        "protocol_commit": protocol_commit(),
        "instance_sha256": instance_hashes(paths), "seeds": SEEDS, "methods": METHODS,
        "search_config": "TabuConfig() defaults", "budget": BUDGET,
        "bootstrap": {"replicates": BOOTSTRAP_REPLICATES, "seed": BOOTSTRAP_SEED},
        "practical_threshold": PRACTICAL_THRESHOLD, "alpha": ALPHA,
        "statistics": "Wilcoxon on instance means (zsplit), one comparison, hierarchical bootstrap",
        "pairing": "same seed; two trajectories per pair",
        "planning_power": planning_power(),
    })
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("code_sha256", "instance_sha256", "seeds", "protocol_sha256"):
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

    manifest["outcome"] = analyze(output, paths)
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print((output / "ANALYSIS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
