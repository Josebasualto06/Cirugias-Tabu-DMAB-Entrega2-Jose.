"""Export the equal-budget scientific comparison as PNG and SVG."""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/hospital-portfolios-matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experiments.compare_portfolios import COMPARABLE, LABELS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments/results/portfolios_60_79"


def main():
    with (OUTPUT / "summary.csv").open(newline="", encoding="utf-8") as stream:
        indexed = {r["method"]: r for r in csv.DictReader(stream)}
    rows = [indexed[key] for key in COMPARABLE]
    labels = [LABELS[key] for key in COMPARABLE]
    positions = np.arange(len(rows))
    estimates = np.array([-float(r["mean_difference_vs_uniform6060"]) for r in rows])
    low = np.array([-float(r["clustered_ci_high"]) for r in rows])
    high = np.array([-float(r["clustered_ci_low"]) for r in rows])
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": "#26313d", "text.color": "#26313d"})
    fig, (left, right) = plt.subplots(1, 2, figsize=(14.8, 5.6),
                                     gridspec_kw={"width_ratios": [1.05, 1.0]})
    for y, estimate, lower, upper in zip(positions, estimates, low, high):
        left.errorbar(estimate, y, xerr=[[estimate - lower], [upper - estimate]],
                      fmt="o", color="#245f9a", markersize=8, capsize=5,
                      linewidth=2)
        left.annotate(f"{estimate:+.2f}", (estimate, y), xytext=(0, 11),
                      textcoords="offset points", ha="center", fontsize=11)
    left.axvline(0, color="#28313b", linestyle="--", linewidth=1.2)
    left.set_yticks(positions, labels)
    left.set_ylim(-0.6, len(rows) - 0.35)
    left.invert_yaxis()
    left.set_xlabel("Reducción media del objetivo\nPositivo = mejor que Tabu de 6.060")
    left.set_title("Calidad e incertidumbre", loc="left", fontsize=14, pad=18)
    left.grid(axis="x", color="#dde3e8", alpha=.8)
    left.set_axisbelow(True)

    starts = np.zeros(len(rows))
    for column, color, name in (("wins", "#245f9a", "Mejora"),
                                ("similar", "#c9d1d9", "Similar"),
                                ("losses", "#c88c28", "Empeora")):
        values = np.array([int(r[column]) for r in rows])
        right.barh(positions, values, left=starts, height=.55,
                   color=color, label=name)
        for y, start, count in zip(positions, starts, values):
            if count:
                right.text(start + count / 2, y, str(count), ha="center", va="center",
                           color="white" if column == "wins" else "#26313d", fontsize=11)
        starts += values
    right.set_yticks(positions, [""] * len(rows))
    right.set_ylim(left.get_ylim())
    right.set_xlim(0, int(starts.max()))
    right.set_xticks(np.linspace(0, starts.max(), 5))
    right.set_xlabel("Pares instancia-semilla\nDiferencias de hasta 0,25 se consideran similares")
    right.set_title("Frecuencia de resultados", loc="left", fontsize=14, pad=18)
    right.legend(loc="upper center", bbox_to_anchor=(.5, -.24), ncol=3, frameon=False)
    fig.suptitle("Comparación con el mismo presupuesto: 6.060 evaluaciones",
                 x=.02, ha="left", fontsize=17, fontweight="bold")
    fig.text(.02, .9, "12 instancias oficiales de 15–30 cirugías · semillas nuevas 60–79 · 240 pares por método",
             fontsize=11, color="#586575")
    fig.text(.02, .02, "Intervalos del 95 %: bootstrap agrupado por instancia y semilla. "
             "El objetivo combina makespan y espera; no es solo el tiempo de cirugía.",
             fontsize=10, color="#586575")
    fig.subplots_adjust(left=.24, right=.98, top=.79, bottom=.25, wspace=.22)
    fig.savefig(OUTPUT / "comparison.png", dpi=180, facecolor="white")
    fig.savefig(OUTPUT / "comparison.svg", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
