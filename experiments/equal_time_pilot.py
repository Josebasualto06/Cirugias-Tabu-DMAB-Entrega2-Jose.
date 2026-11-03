"""Task 4 of the Entrega 2 protocol: descriptive pilot at equal wall-clock time.

Gives uniform Tabu and Tabu with D-MAB the same time limit per trajectory, in a
single process, on the -01 standard instances with seeds 110-114:

    python -m experiments.equal_time_pilot

The limit is half the median portfolio time measured by Task 1. The search
stops at the first batch boundary after the limit, so a run may overshoot by
one batch. This pilot supports no inferential claim.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from statistics import mean, median

from experiments.entrega2_common import (
    ROOT, SIZES, base_manifest, instance_hashes, prepare_output, read_rows, sha256,
    write_manifest, write_rows,
)
from experiments.portfolio_search import SearchTrajectory
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality
from surgery_optim.tabu import TabuConfig


SEEDS = tuple(range(110, 115))
POLICIES = ("uniform", "dmab")
TIMINGS = ROOT / "experiments/results/entrega2_entorno_80_84/summary.csv"


def run_limited(context, seed: int, policy: str, limit: float) -> tuple[SearchTrajectory, float]:
    started = time.perf_counter()
    trajectory = SearchTrajectory(context, seed, policy, TabuConfig())
    while time.perf_counter() - started < limit:
        trajectory.advance(TabuConfig().candidates_per_batch)
    return trajectory, time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_tiempo_110_114")
    args = parser.parse_args()
    output = prepare_output(args.output)
    limits = {int(row["size"]): float(row["median_seconds"]) / 2 for row in read_rows(TIMINGS)}
    paths = [ROOT / f"instances/standard/HOSP-STD-{size}-01.yaml" for size in SIZES]
    manifest = base_manifest("entrega2-tiempo-v1", Path(__file__),
                             ROOT / "experiments/portfolio_search.py")
    manifest.update({"instance_sha256": instance_hashes(paths), "seeds": SEEDS,
                     "time_limit_seconds": limits, "timings_sha256": sha256(TIMINGS),
                     "execution": "sequential, single process"})
    write_manifest(output, manifest)

    rows = []
    for path in paths:
        context = load_instance(path)
        for seed in SEEDS:
            for policy in POLICIES:
                trajectory, elapsed = run_limited(context, seed, policy, limits[len(context.jobs)])
                measured = quality(context, trajectory.best_solution)
                rows.append({
                    "instance_id": context.instance_id, "size": len(context.jobs), "seed": seed,
                    "policy": policy, "time_limit_seconds": limits[len(context.jobs)],
                    "elapsed_seconds": elapsed, "evaluations": trajectory.spent,
                    "objective": measured.objective, "makespan": measured.makespan,
                    "blocked": measured.blocked_minutes,
                })
        print(f"{context.instance_id}: completa", flush=True)
    write_rows(output / "runs.csv", rows)

    summary = []
    for size in SIZES:
        current = [row for row in rows if row["size"] == size]
        pick = lambda policy, field: [row[field] for row in current if row["policy"] == policy]
        differences = [d - u for d, u in zip(pick("dmab", "objective"), pick("uniform", "objective"))]
        summary.append({
            "size": size, "time_limit_seconds": limits[size],
            "median_evaluations_uniform": median(pick("uniform", "evaluations")),
            "median_evaluations_dmab": median(pick("dmab", "evaluations")),
            "mean_difference_dmab_minus_uniform": mean(differences),
            "wins": sum(d < -0.25 for d in differences),
            "similar": sum(abs(d) <= 0.25 for d in differences),
            "losses": sum(d > 0.25 for d in differences),
        })
    write_rows(output / "summary.csv", summary)
    lines = ["# Piloto a igual tiempo", "",
             "Instancias estándar `-01`, semillas 110–114, un solo proceso. Es un piloto "
             "descriptivo: no sustenta conclusiones ni se mezcla con otros estudios.", "",
             "| Cirugías | Límite por camino (s) | Evaluaciones uniforme (mediana) | "
             "Evaluaciones D-MAB (mediana) | Media D-MAB − uniforme | Mejora / similar / empeora |",
             "|---:|---:|---:|---:|---:|---|"]
    for row in summary:
        lines.append(f"| {row['size']} | {row['time_limit_seconds']:.2f} | "
                     f"{row['median_evaluations_uniform']:.0f} | {row['median_evaluations_dmab']:.0f} | "
                     f"{row['mean_difference_dmab_minus_uniform']:+.3f} | "
                     f"{row['wins']} / {row['similar']} / {row['losses']} |")
    lines += ["", "El tiempo depende del equipo y de su carga.", ""]
    (output / "PILOTO.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
