"""Reproducible paired study: mixed Tabu, Tabu+D-MAB, and UCB1 ablation.

Run from the repository root, for example:
    python -m experiments.run_study --seed-start 40 --seed-count 20
Partial runs are saved after every solution and can be resumed with the same
arguments. Seeds 0–19 were exploratory (0–5 also tuned C and lambda) and seeds
20–39 validated the Entrega 1 configuration, so validation starts at 40.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

from scipy.stats import wilcoxon

from surgery_optim.bandit import MOVES
from surgery_optim.baselines import construct_baseline
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality
from surgery_optim.tabu import TabuConfig, run_tabu


ROOT = Path(__file__).resolve().parents[1]
SIZES = (15, 20, 25, 30)
POLICIES = ("uniform", "dmab", "ucb")
RULES = ("fifo", "spt", "lpt")
RUN_FIELDS = (
    "instance_id", "instance_digest", "size", "seed", "policy",
    "initial_objective", "objective", "makespan_minutes", "blocked_minutes",
    "max_wait_minutes", "cross_room_jobs", "evaluations", "feasible_evaluations",
    "runtime_seconds", "dmab_restarts", "repaired_candidates",
    *(f"attempted_{move}" for move in MOVES),
    *(f"evaluated_{move}" for move in MOVES),
)
BASELINE_FIELDS = (
    "instance_id", "instance_digest", "size", "rule", "objective",
    "makespan_minutes", "blocked_minutes", "max_wait_minutes", "cross_room_jobs",
)


def write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def median(values) -> float:
    return float(np.median(list(values)))


def build_manifest(paths: list[Path], seeds: list[int], config: TabuConfig) -> dict:
    code_paths = [ROOT / "src" / "surgery_optim" / name for name in (
        "model.py", "instances.py", "scheduler.py", "baselines.py",
        "encoding.py", "objective.py", "bandit.py", "tabu.py",
    )] + [ROOT / "experiments" / "run_study.py"]
    return {
        "protocol_version": "2.0",
        "status": "running",
        "source_repository": "https://github.com/Saicooh/OII464_Hospitales",
        "source_head_checked_in_prior_pilot": "ecd30e3dbc1962d856c09b3470d1870c3b139a9a",
        "instance_paths": [str(path.relative_to(ROOT)) for path in paths],
        "instance_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in paths},
        "instance_digests": {load_instance(path).instance_id: load_instance(path).digest
                             for path in paths},
        "code_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in code_paths},
        "seeds": seeds,
        "policies": POLICIES,
        "baseline_rules": RULES,
        "config": asdict(config),
        "objective": "Cmax + 1e-6*sum(operation starts) + 0.5*sum(waits) + 1.4*max(wait); no room-balance term",
        "feasibility": "strict per-surgery max_wait; free and independent anesthesia/surgery rooms; no forced balance",
        "reward": "max(0, local_before_batch - candidate)/max(1, 0.02*initial), clipped to 1; duplicate -> 0",
        "bandit": "UCB1 with exploration scale C (config.exploration), per-arm "
                  "Page-Hinkley restart for dmab; no restart for ucb",
        "tuning": "C and lambda chosen on exploratory seeds 0-5 "
                  "(experiments/results/calibration_0_5); validation seeds untouched",
        "tabu_memory": "attribute = job moved by the accepted candidate",
        "rng": "NumPy default_rng(seed) for initial keys; random.Random(seed) for neighbors; "
               "common random numbers: every policy draws the uniform move",
        "statistics": "two-sided Wilcoxon signed-rank on paired objective differences "
                      "(zero_method='zsplit'), Holm correction within each family",
        "runtime_environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": np.__version__, "yaml": yaml.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "historical_results": "seeds 0..19 were explored earlier and are not mixed into this validation",
    }


def save_manifest(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


COMPARISONS = (("dmab", "uniform"), ("ucb", "uniform"), ("dmab", "ucb"))


def holm(p_values: list[float]) -> list[float]:
    """Holm–Bonferroni adjusted p-values, in the input order."""
    order = sorted(range(len(p_values)), key=lambda index: p_values[index])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[index]))
        adjusted[index] = running
    return adjusted


def paired_test(differences: np.ndarray) -> float:
    if np.all(np.abs(differences) <= 1e-9):
        return 1.0
    return float(wilcoxon(differences, zero_method="zsplit").pvalue)


def statistical_tests(runs: list[dict], contexts) -> list[dict]:
    """Wilcoxon signed-rank tests on objective differences (alternative − reference).

    Family "global": the three comparisons over all instance–seed pairs.
    Family "per_instance": the 12 instances × 3 comparisons. Holm correction
    is applied within each family.
    """
    by_key = {(row["instance_id"], int(row["seed"]), row["policy"]): float(row["objective"])
              for row in runs}
    seeds = sorted({int(row["seed"]) for row in runs})
    results: list[dict] = []
    for family, groups in (
        ("global", [("all", [c.instance_id for c in contexts])]),
        ("per_instance", [(c.instance_id, [c.instance_id]) for c in contexts]),
    ):
        family_rows = []
        for alternative, reference in COMPARISONS:
            for label, instances in groups:
                diffs = np.array([by_key[i, seed, alternative] - by_key[i, seed, reference]
                                  for i in instances for seed in seeds])
                family_rows.append({
                    "family": family, "scope": label, "alternative": alternative,
                    "reference": reference, "pairs": len(diffs),
                    "mean_difference": float(np.mean(diffs)),
                    "median_difference": float(np.median(diffs)),
                    "wins": int(np.sum(diffs < -1e-9)),
                    "ties": int(np.sum(np.abs(diffs) <= 1e-9)),
                    "losses": int(np.sum(diffs > 1e-9)),
                    "wilcoxon_p": paired_test(diffs),
                })
        for row, adjusted in zip(family_rows, holm([r["wilcoxon_p"] for r in family_rows])):
            row["holm_p"] = adjusted
        results.extend(family_rows)
    return results


def summaries_and_plot(output: Path, contexts, runs: list[dict], baselines: list[dict]) -> None:
    expected = len(contexts) * len({int(row["seed"]) for row in runs}) * len(POLICIES)
    if len(runs) != expected:
        raise ValueError(f"incomplete study: {len(runs)} of {expected} rows")
    summaries: list[dict] = []
    paired: list[dict] = []
    for context in contexts:
        subset = [row for row in runs if row["instance_id"] == context.instance_id]
        by_key = {(int(row["seed"]), row["policy"]): row for row in subset}
        seeds = sorted({int(row["seed"]) for row in subset})
        for policy in POLICIES:
            rows = [by_key[seed, policy] for seed in seeds]
            summaries.append({
                "instance_id": context.instance_id, "size": len(context.jobs),
                "policy": policy, "runs": len(rows),
                "median_objective": median(float(row["objective"]) for row in rows),
                "median_makespan_minutes": median(float(row["makespan_minutes"]) for row in rows),
                "median_blocked_minutes": median(float(row["blocked_minutes"]) for row in rows),
                "median_runtime_seconds": median(float(row["runtime_seconds"]) for row in rows),
                "minimum_objective": min(float(row["objective"]) for row in rows),
                "maximum_objective": max(float(row["objective"]) for row in rows),
            })
        for alternative in ("dmab", "ucb"):
            for metric in ("objective", "makespan_minutes", "blocked_minutes"):
                differences = np.array([
                    float(by_key[seed, alternative][metric])
                    - float(by_key[seed, "uniform"][metric]) for seed in seeds
                ])
                paired.append({
                    "instance_id": context.instance_id, "size": len(context.jobs),
                    "reference": "uniform", "alternative": alternative,
                    "metric": metric, "runs": len(seeds),
                    "median_difference": float(np.median(differences)),
                    "mean_difference": float(np.mean(differences)),
                    "wins": int(np.sum(differences < -1e-9)),
                    "ties": int(np.sum(np.abs(differences) <= 1e-9)),
                    "losses": int(np.sum(differences > 1e-9)),
                })
    write_csv(output / "summary.csv", summaries, tuple(summaries[0]))
    write_csv(output / "paired.csv", paired, tuple(paired[0]))
    tests = statistical_tests(runs, contexts)
    write_csv(output / "statistics.csv", tests, tuple(tests[0]))

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.7), layout="constrained")
    metrics = (
        ("median_objective", "Objetivo combinado"),
        ("median_makespan_minutes", "Makespan (min)"),
        ("median_blocked_minutes", "Bloqueo total (min)"),
    )
    palette = {"uniform": "#365978", "dmab": "#bd6b25", "ucb": "#318665"}
    labels = {"uniform": "Tabu mixto", "dmab": "Tabu + D-MAB", "ucb": "Tabu + UCB1"}
    for axis, (field, title) in zip(axes, metrics):
        for policy in POLICIES:
            line = []
            for size in SIZES:
                values = [float(row[field]) for row in summaries
                          if row["size"] == size and row["policy"] == policy]
                line.append(median(values))
                axis.scatter([size] * len(values), values, color=palette[policy], alpha=.4, s=20)
            axis.plot(SIZES, line, "-o", color=palette[policy], label=labels[policy])
        baseline_metric = {"median_objective": "objective",
                           "median_makespan_minutes": "makespan_minutes",
                           "median_blocked_minutes": "blocked_minutes"}[field]
        baseline_line = [median(min(float(row[baseline_metric]) for row in baselines
                                    if row["instance_id"] == context.instance_id)
                                for context in contexts if len(context.jobs) == size)
                         for size in SIZES]
        axis.plot(SIZES, baseline_line, "--s", color="#202020", label="Mejor regla clásica")
        axis.set_xticks(SIZES)
        axis.set_xlabel("Cirugías por instancia")
        axis.set_ylabel(title)
        axis.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    seed_list = sorted({int(row["seed"]) for row in runs})
    fig.suptitle(f"Validación: 12 instancias sintéticas, semillas {seed_list[0]}–{seed_list[-1]}")
    fig.savefig(output / "comparison.png", dpi=170)
    fig.savefig(output / "comparison.pdf")
    plt.close(fig)

    lines = [
        "# Validación emparejada (semillas nuevas)", "",
        "Menor valor es mejor. Las celdas son medianas de 20 semillas por instancia. "
        "El objetivo incluye makespan y bloqueo; sus componentes se reportan por separado.", "",
        "| Instancia | Mejor regla | Tabu mixto | Tabu + D-MAB | Tabu + UCB1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for context in contexts:
        best_rule = min(float(row["objective"]) for row in baselines
                        if row["instance_id"] == context.instance_id)
        values = {row["policy"]: float(row["median_objective"]) for row in summaries
                  if row["instance_id"] == context.instance_id}
        lines.append(f"| {context.instance_id} | {best_rule:.3f} | "
                     f"{values['uniform']:.3f} | {values['dmab']:.3f} | {values['ucb']:.3f} |")
    for alt, label in (("dmab", "D-MAB"), ("ucb", "UCB1")):
        objective_pairs = [row for row in paired if row["alternative"] == alt
                           and row["metric"] == "objective"]
        wins = sum(row["wins"] for row in objective_pairs)
        ties = sum(row["ties"] for row in objective_pairs)
        losses = sum(row["losses"] for row in objective_pairs)
        instance_medians = [float(row["median_difference"]) for row in objective_pairs]
        lines.extend(["", f"**{label} frente a Tabu mixto:** {wins} victorias, "
                      f"{ties} empates y {losses} derrotas en pares instancia-semilla. "
                      f"Mediana de las 12 diferencias medianas: {median(instance_medians):+.3f}."])
    labels_text = {"dmab": "D-MAB", "ucb": "UCB1", "uniform": "Tabu mixto"}
    lines.extend(["", "## Pruebas estadísticas", "",
                  "Wilcoxon de rangos con signo, bilateral, sobre las diferencias emparejadas "
                  "del objetivo (alternativa − referencia; negativo favorece a la alternativa). "
                  "Holm corrige las tres comparaciones globales.", "",
                  "| Comparación | Pares | Media dif. | Gana / empata / pierde | p | p Holm |",
                  "|---|---:|---:|---:|---:|---:|"])
    for row in tests:
        if row["family"] != "global":
            continue
        lines.append(f"| {labels_text[row['alternative']]} vs {labels_text[row['reference']]} | "
                     f"{row['pairs']} | {row['mean_difference']:+.3f} | {row['wins']} / "
                     f"{row['ties']} / {row['losses']} | {row['wilcoxon_p']:.3g} | "
                     f"{row['holm_p']:.3g} |")
    significant = [row for row in tests if row["family"] == "per_instance"
                   and row["holm_p"] < 0.05]
    lines.extend(["", f"Por instancia (36 pruebas, Holm): {len(significant)} con p Holm < 0,05"
                  + (": " + ", ".join(
                      f"{row['scope']} ({labels_text[row['alternative']]} vs "
                      f"{labels_text[row['reference']]}, media {row['mean_difference']:+.2f})"
                      for row in significant) if significant else "") + ".",
                  "Detalle en `statistics.csv`."])
    lines.extend([
        "", "Estos resultados son empíricos y específicos del catálogo sintético. "
        "No prueban optimalidad ni una mejora universal del controlador. "
        "Las instancias de 15–30 cirugías no son los cuatro JSON históricos del repositorio oficial.",
        "", "`runs.csv` conserva cada corrida; `baselines.csv`, `summary.csv`, "
        "`paired.csv` y `manifest.json` permiten auditar protocolo y comparaciones.", "",
    ])
    (output / "ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=40)
    parser.add_argument("--seed-count", type=int, default=20)
    parser.add_argument("--budget", type=int, default=3030)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments" / "results" / "validation_40_59")
    args = parser.parse_args()
    if args.seed_count < 1 or args.seed_start < 0:
        parser.error("seed range must be nonempty and nonnegative")
    seeds = list(range(args.seed_start, args.seed_start + args.seed_count))
    if any(seed < 40 for seed in seeds):
        parser.error("validation seeds must start at 40 or later (0-39 already used)")
    config = TabuConfig(evaluation_budget=args.budget)
    paths = [ROOT / "instances" / "standard" / f"HOSP-STD-{size}-{replica:02d}.yaml"
             for size in SIZES for replica in (1, 2, 3)]
    contexts = [load_instance(path) for path in paths]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    expected_manifest = build_manifest(paths, seeds, config)
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in ("instance_sha256", "code_sha256", "seeds", "policies", "config"):
            if prior[key] != expected_manifest[key]:
                raise ValueError(f"cannot resume with changed {key}")
    else:
        save_manifest(manifest_path, expected_manifest)

    baseline_path = output / "baselines.csv"
    if not baseline_path.exists():
        baseline_rows = []
        for context in contexts:
            for rule in RULES:
                measured = quality(context, construct_baseline(context, rule))
                baseline_rows.append({
                    "instance_id": context.instance_id, "instance_digest": context.digest,
                    "size": len(context.jobs), "rule": rule,
                    "objective": measured.objective, "makespan_minutes": measured.makespan,
                    "blocked_minutes": measured.blocked_minutes,
                    "max_wait_minutes": measured.max_wait_minutes,
                    "cross_room_jobs": measured.cross_room_jobs,
                })
        write_csv(baseline_path, baseline_rows, BASELINE_FIELDS)
    baselines = read_csv(baseline_path)
    run_path = output / "runs.csv"
    existing = read_csv(run_path)
    completed = {(row["instance_id"], int(row["seed"]), row["policy"]) for row in existing}
    if not run_path.exists():
        write_csv(run_path, [], RUN_FIELDS)
    with run_path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=RUN_FIELDS)
        for context in contexts:
            for seed in seeds:
                initial = None
                for policy in POLICIES:
                    key = (context.instance_id, seed, policy)
                    if key in completed:
                        prior_row = next(row for row in existing
                                         if (row["instance_id"], int(row["seed"]), row["policy"]) == key)
                        if initial is None:
                            initial = float(prior_row["initial_objective"])
                        continue
                    result = run_tabu(context, seed, policy, config)
                    measured = result.final_quality
                    if result.evaluations != args.budget or result.feasible_evaluations != args.budget:
                        raise RuntimeError(f"budget/feasibility failure for {key}")
                    if initial is None:
                        initial = result.initial_objective
                    elif not math.isclose(initial, result.initial_objective, abs_tol=1e-9):
                        raise RuntimeError(f"paired initialization mismatch for {key}")
                    row = {
                        "instance_id": context.instance_id, "instance_digest": context.digest,
                        "size": len(context.jobs), "seed": seed, "policy": policy,
                        "initial_objective": result.initial_objective,
                        "objective": measured.objective, "makespan_minutes": measured.makespan,
                        "blocked_minutes": measured.blocked_minutes,
                        "max_wait_minutes": measured.max_wait_minutes,
                        "cross_room_jobs": measured.cross_room_jobs,
                        "evaluations": result.evaluations,
                        "feasible_evaluations": result.feasible_evaluations,
                        "runtime_seconds": result.runtime_seconds,
                        "dmab_restarts": result.dmab_restarts,
                        "repaired_candidates": result.repaired_candidates,
                        **{f"attempted_{move}": result.attempted_choices[move] for move in MOVES},
                        **{f"evaluated_{move}": result.evaluated_choices[move] for move in MOVES},
                    }
                    writer.writerow(row)
                    stream.flush()
                    completed.add(key)
                print(f"{context.instance_id}, seed {seed}: complete", flush=True)
    runs = read_csv(run_path)
    expected_rows = len(contexts) * len(seeds) * len(POLICIES)
    if len(runs) != expected_rows:
        raise ValueError(f"expected {expected_rows} runs, found {len(runs)}")
    summaries_and_plot(output, contexts, runs, baselines)
    expected_manifest["status"] = "completed"
    expected_manifest["run_count"] = len(runs)
    save_manifest(manifest_path, expected_manifest)
    print(f"Study complete: {len(runs)} runs in {output}")


if __name__ == "__main__":
    main()
