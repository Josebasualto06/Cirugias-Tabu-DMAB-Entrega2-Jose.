"""Distribution of RPD by method and convergence at 3,030 evaluations.

Panel (a) reads the archived runs. Panel (b) reads the audited replay, because
runs.csv does not store the trajectory. Both use the same RPD reference: the
best value of each instance over both congestion studies.

    python experiments/scripts/figura_distribucion.py

The three searches with 3,030 evaluations keep their colour in both panels and
also differ by line style and direct label. The others are grey.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments/results"
STUDY = "entrega2_congestion_90_109"
CONFIRMATION = "entrega3_confirmacion_ucb1"
CURVES = RESULTS / "entrega3_revision_reejecucion/convergence.csv"

INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3de"
NEUTRAL = "#8a8985"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
METHODS = (
    ("uniform3030", "Uniforme", BLUE, "-"),
    ("dmab3030", "D-MAB", ORANGE, (0, (4, 2))),
    ("ucb3030", "UCB1", AQUA, (0, (1, 1))),
    ("uniform6060", "Prolongado", NEUTRAL, None),
    ("two_uniform6060", "Dos Tabu", NEUTRAL, None),
    ("fixed_portfolio6060", "Cartera", NEUTRAL, None),
)


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path,
                        default=ROOT / "informe/figuras/distribucion_convergencia.pdf")
    parser.add_argument("--ancho", type=float, default=16.0, help="width in cm")
    parser.add_argument("--alto", type=float, default=4.4, help="height in cm")
    parser.add_argument("--cuerpo", type=float, default=8.0, help="font size in points")
    args = parser.parse_args()

    runs = read(RESULTS / STUDY / "runs.csv")
    best: dict[str, float] = {}
    for row in runs + read(RESULTS / CONFIRMATION / "runs.csv"):
        instance, value = row["instance_id"], float(row["objective"])
        best[instance] = min(value, best.get(instance, value))

    def rpd(instance: str, value: str) -> float:
        return 100 * (float(value) - best[instance]) / best[instance]

    samples, curves = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for row in runs:
        samples[row["method"]].append(rpd(row["instance_id"], row["objective"]))
    for row in read(CURVES):
        if row["study"] == STUDY:
            curves[row["method"]][int(row["evaluations"])].append(
                rpd(row["instance_id"], row["mean_best_objective"]))

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
        "font.size": args.cuerpo, "pdf.fonttype": 42, "axes.unicode_minus": False,
    })
    figure, (left, right) = plt.subplots(
        1, 2, figsize=(args.ancho / 2.54, args.alto / 2.54), layout="constrained",
        gridspec_kw={"width_ratios": (1.05, 1)},
    )
    positions = [6.6, 5.6, 4.6, 3.0, 2.0, 1.0]
    boxes = left.boxplot(
        [samples[key] for key, *_ in METHODS], positions=positions, orientation="horizontal",
        widths=0.58, whis=(5, 95), showfliers=False, showmeans=True, patch_artist=True,
        medianprops={"color": INK, "linewidth": 1.1},
        meanprops={"marker": "D", "markersize": 3.6, "markerfacecolor": "white",
                   "markeredgecolor": INK, "markeredgewidth": 0.8},
        whiskerprops={"color": INK_SECONDARY, "linewidth": 0.8},
        capprops={"color": INK_SECONDARY, "linewidth": 0.8},
    )
    for box, (_, _, colour, _) in zip(boxes["boxes"], METHODS):
        box.set_facecolor(matplotlib.colors.to_rgba(colour, 0.35))
        box.set_edgecolor(colour)
    budgets = ["3.030"] * 3 + ["6.060"] * 3
    left.set_yticks(positions, labels=[f"{label} ({budget})"
                                       for (_, label, *_), budget in zip(METHODS, budgets)])
    left.set_xticks(range(0, 20, 5))
    left.set_title("(a) RPD final de cada corrida", fontsize=args.cuerpo, loc="left")
    left.set_xlabel("RPD (%)", color=INK_SECONDARY)
    left.grid(axis="x", color=GRID, linewidth=0.7)

    ends = []
    for key, label, colour, style in METHODS[:3]:
        points = sorted(curves[key])
        values = [float(np.mean(curves[key][point])) for point in points]
        right.plot(points, values, color=colour, linestyle=style, linewidth=1.5)
        ends.append((values[-1], label, colour, style))
    # Direct labels, spread vertically so that they do not collide.
    low, high = right.get_ylim()
    gap, previous = 0.085 * (high - low), -np.inf
    for value, label, colour, style in sorted(ends, key=lambda end: end[0]):
        height = max(value - gap / 2, previous + gap)
        previous = height
        right.plot([3120, 3400], [height, height], color=colour, linestyle=style, linewidth=1.5,
                   clip_on=False)
        right.text(3460, height, label, color=INK, va="center")
    right.set_xlim(0, 4050)
    right.set_xticks([30, 1000, 2000, 3030])
    right.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:,.0f}".replace(",", ".")))
    right.set_title("(b) Convergencia media", fontsize=args.cuerpo, loc="left")
    right.set_xlabel("Evaluaciones", color=INK_SECONDARY)
    right.set_ylabel("RPD medio (%)", color=INK_SECONDARY)
    right.grid(axis="y", color=GRID, linewidth=0.7)

    for axis in (left, right):
        axis.set_axisbelow(True)
        axis.tick_params(colors=INK_SECONDARY, length=2, labelcolor=INK)
        for side in ("top", "right"):
            axis.spines[side].set_visible(False)
        for side in ("bottom", "left"):
            axis.spines[side].set_color(GRID)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.salida)
    print(args.salida)


if __name__ == "__main__":
    main()
