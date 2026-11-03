"""Plot paired objective differences against uniform mixed Tabu by instance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?",
                        default=ROOT / "experiments/results/validation_40_59")
    args = parser.parse_args()
    directory = args.directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed":
        raise ValueError("the validation study must be completed")
    with (directory / "runs.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_key = {(row["instance_id"], int(row["seed"]), row["policy"]): row for row in rows}
    instances = sorted(manifest["instance_digests"],
                       key=lambda name: (int(name.split("-")[2]), int(name.split("-")[3])))
    fig, axes = plt.subplots(1, 2, figsize=(13, 7.2), sharey=True, layout="constrained")
    palette = {"dmab": "#b75f25", "ucb": "#318665"}
    for axis, policy in zip(axes, ("dmab", "ucb")):
        rng = np.random.default_rng(20260929)
        for y, instance in enumerate(instances):
            differences = np.array([
                float(by_key[instance, seed, policy]["objective"])
                - float(by_key[instance, seed, "uniform"]["objective"])
                for seed in manifest["seeds"]
            ])
            jitter = rng.uniform(-.12, .12, len(differences))
            axis.scatter(differences, y + jitter, s=13, color=palette[policy],
                         alpha=.28, linewidths=0)
            median = float(np.median(differences))
            first, third = np.quantile(differences, [.25, .75])
            axis.plot([first, third], [y, y], color=palette[policy], linewidth=3)
            axis.scatter([median], [y], marker="D", s=48, color=palette[policy],
                         edgecolors="white", linewidths=.65, zorder=3)
        axis.axvline(0, color="#202020", linewidth=1.2)
        for boundary in (2.5, 5.5, 8.5):
            axis.axhline(boundary, color="#d7d7d7", linewidth=.7)
        axis.set_yticks(range(len(instances)), instances)
        axis.invert_yaxis()
        axis.set_xlabel("Diferencia de objetivo frente a Tabu mixto (min)")
        axis.set_title("Tabu + D-MAB" if policy == "dmab" else "Tabu + UCB1")
        axis.grid(axis="x", alpha=.16)
    fig.suptitle("20 semillas emparejadas por instancia; negativo favorece al controlador\n"
                 "Punto: corrida · Diamante: mediana · Barra: rango intercuartílico")
    fig.savefig(directory / "paired_differences.png", dpi=170)
    fig.savefig(directory / "paired_differences.pdf")
    plt.close(fig)
    (directory / "paired_plot_manifest.json").write_text(json.dumps({
        "source": "runs.csv",
        "runs_sha256": hashlib.sha256((directory / "runs.csv").read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seeds": manifest["seeds"],
        "negative_difference_favors": "alternative policy",
        "same_instances_as_exploration": True,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Paired plot: {directory / 'paired_differences.png'}")


if __name__ == "__main__":
    main()
