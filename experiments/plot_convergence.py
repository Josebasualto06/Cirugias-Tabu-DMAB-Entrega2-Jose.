"""Illustrative convergence traces for the first replica at each size.

The fixed seed 40 (first validation seed) was chosen before inspecting the outcomes.
These curves illustrate mechanism; statistical comparisons use all 240 pairs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from surgery_optim import TabuConfig, load_instance, run_tabu


ROOT = Path(__file__).resolve().parents[1]
SIZES = (15, 20, 25, 30)
POLICIES = ("uniform", "dmab", "ucb")
COLORS = {"uniform": "#365978", "dmab": "#bd6b25", "ucb": "#318665"}
LABELS = {"uniform": "Tabu mixto", "dmab": "Tabu + D-MAB", "ucb": "Tabu + UCB1"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=40)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/validation_40_59")
    args = parser.parse_args()
    output = args.output.resolve()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if args.seed not in manifest["seeds"] or manifest["status"] != "completed":
        raise ValueError("seed must belong to the completed validation")
    with (output / "runs.csv").open(newline="", encoding="utf-8") as stream:
        reference = {(row["instance_id"], int(row["seed"]), row["policy"]): row
                     for row in csv.DictReader(stream)}
    config = TabuConfig.from_manifest(manifest["config"])
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), layout="constrained")
    trace_rows = []
    for axis, size in zip(axes.flat, SIZES):
        context = load_instance(ROOT / "instances/standard"
                                / f"HOSP-STD-{size}-01.yaml")
        for policy in POLICIES:
            result = run_tabu(context, args.seed, policy, config)
            old = reference[context.instance_id, args.seed, policy]
            if not math.isclose(result.final_quality.objective,
                                float(old["objective"]), abs_tol=1e-9):
                raise ValueError("representative rerun did not reproduce results")
            x = [config.population_size] + [item["evaluations"] for item in result.trace]
            y = [result.initial_objective] + [item["best_objective"] for item in result.trace]
            axis.step(x, y, where="post", color=COLORS[policy], label=LABELS[policy])
            trace_rows.extend({
                "instance_id": context.instance_id, "size": size, "seed": args.seed,
                "policy": policy, "evaluations": spent, "best_objective": best,
            } for spent, best in zip(x, y))
        axis.set_title(f"{size} cirugías, réplica 01")
        axis.set_xlabel("Evaluaciones estrictas")
        axis.set_ylabel("Mejor objetivo hasta ese punto")
        axis.grid(alpha=.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(f"Convergencia ilustrativa, semilla fija {args.seed}")
    fig.savefig(output / "convergence.png", dpi=170)
    fig.savefig(output / "convergence.pdf")
    plt.close(fig)
    with (output / "convergence_trace.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(trace_rows[0]))
        writer.writeheader()
        writer.writerows(trace_rows)
    (output / "convergence_manifest.json").write_text(json.dumps({
        "illustrative_only": True,
        "seed": args.seed,
        "instances": [f"HOSP-STD-{size}-01" for size in SIZES],
        "budget": config.evaluation_budget,
        "matching_final_values_in_runs_csv_verified": True,
        "runs_sha256": hashlib.sha256((output / "runs.csv").read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Convergence figure: {output / 'convergence.png'}")


if __name__ == "__main__":
    main()
