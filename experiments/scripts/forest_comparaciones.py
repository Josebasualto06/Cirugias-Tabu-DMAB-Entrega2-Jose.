"""Forest plot of the paired differences and their clustered 95 % intervals.

Reads the archived comparison files and writes a vector figure. Three groups are
kept apart and labelled, because they are different studies:

* the pre-registered family C1-C4 (seeds 90-109);
* the exploratory contrast UCB1 - uniform Tabu (seeds 90-109, not pre-registered);
* the pre-registered confirmation E1 (seeds 120-139), if that study is complete.

    python experiments/scripts/forest_comparaciones.py
    python experiments/scripts/forest_comparaciones.py --valores --fuente "DejaVu Sans" \
        --ancho 15 --alto 5.6 --cuerpo 7.4 \
        --salida presentacion_final/figuras/forest_comparaciones.pdf

Group identity never depends on colour alone: each group has its own marker and
a header above its rows. The palette is the first three slots of a validated
colour-blind-safe set. The file has exactly the requested size.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments/results"
FAMILY = RESULTS / "entrega2_congestion_90_109/comparisons.csv"
EXPLORATORY = RESULTS / "entrega2_exploratorio/contrastes.csv"
CONFIRMATION = RESULTS / "entrega3_confirmacion_ucb1"
THRESHOLD = -0.25

INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3de"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

FAMILY_LABELS = {
    "C1": "C1  D-MAB − Tabu uniforme (3.030)",
    "C4": "C4  D-MAB − UCB1 sin reinicio (3.030)",
    "C2": "C2  Cartera − Tabu prolongado (6.060)",
    "C3": "C3  Cartera − dos Tabu (6.060)",
}


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def spanish(value: float, digits: int = 3, signed: bool = True) -> str:
    text = f"{abs(value):.{digits}f}".replace(".", ",")
    sign = "−" if value < 0 else ("+" if signed and value > 0 else "")
    return sign + text


def groups() -> list[dict]:
    """Return the groups to draw, each with a header, a style and its rows."""
    family = {row["comparison"]: row for row in rows(FAMILY)}
    result = [{
        "header": "Familia pre-registrada · semillas 90–109",
        "legend": "Pre-registrada C1–C4", "color": BLUE, "marker": "o", "filled": True,
        "rows": [(FAMILY_LABELS[code], family[code]) for code in ("C1", "C4", "C2", "C3")],
    }]
    exploratory = rows(EXPLORATORY)[0]
    result.append({
        "header": "Exploratorio, no pre-registrado · semillas 90–109",
        "legend": "Exploratorio", "color": ORANGE, "marker": "D", "filled": False,
        "rows": [("UCB1 sin reinicio − Tabu uniforme (3.030)", exploratory)],
    })
    manifest = CONFIRMATION / "manifest.json"
    if manifest.exists() and json.loads(manifest.read_text(encoding="utf-8")).get("status") == "completed":
        confirmation = rows(CONFIRMATION / "comparisons.csv")[0]
        result.append({
            "header": "Confirmación pre-registrada · semillas 120–139",
            "legend": "Confirmación E1", "color": AQUA, "marker": "s", "filled": True,
            "rows": [("E1  UCB1 sin reinicio − Tabu uniforme (3.030)", confirmation)],
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path,
                        default=ROOT / "informe/figuras/forest_comparaciones.pdf")
    parser.add_argument("--ancho", type=float, default=16.0, help="width in cm")
    parser.add_argument("--alto", type=float, default=7.4, help="height in cm")
    parser.add_argument("--cuerpo", type=float, default=9.0, help="font size in points")
    parser.add_argument("--fuente", default="serif")
    parser.add_argument("--valores", action="store_true",
                        help="print mean and interval at the right of each row")
    args = parser.parse_args()

    plt.rcParams.update({
        "font.family": args.fuente,
        "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
        "font.size": args.cuerpo, "pdf.fonttype": 42, "axes.unicode_minus": False,
        "mathtext.fontset": "stix" if args.fuente == "serif" else "dejavusans",
    })
    # The constrained layout keeps every label inside the requested size, so the
    # file is not rescaled when it is included.
    figure, axis = plt.subplots(figsize=(args.ancho / 2.54, args.alto / 2.54),
                                layout="constrained")
    figure.patch.set_facecolor("white")

    position = 0.0
    ticks, labels, headers, value_ticks, values, handles = [], [], [], [], [], []
    for index, group in enumerate(groups()):
        if index:
            position -= 0.45
        # The header sits in the label column, above the rows of its group.
        ticks.append(position)
        labels.append(group["header"])
        headers.append(len(labels) - 1)
        position -= 1.0
        face = group["color"] if group["filled"] else "white"
        for label, row in group["rows"]:
            mean = float(row["mean_difference"])
            low, high = float(row["ci_low"]), float(row["ci_high"])
            axis.plot([low, high], [position, position], color=group["color"], linewidth=1.6,
                      solid_capstyle="round", zorder=3)
            axis.plot([mean], [position], marker=group["marker"], markersize=6.5,
                      markerfacecolor=face, markeredgecolor=group["color"],
                      markeredgewidth=1.4, linestyle="none", zorder=4)
            ticks.append(position)
            labels.append(label)
            value_ticks.append(position)
            values.append(f"{spanish(mean)}  [{spanish(low)}; {spanish(high)}]")
            position -= 1.0
        handles.append(Line2D([0], [0], color=group["color"], linewidth=1.6,
                              marker=group["marker"], markersize=6.5, markerfacecolor=face,
                              markeredgecolor=group["color"], markeredgewidth=1.4,
                              label=group["legend"]))

    axis.axvline(0, color=INK_SECONDARY, linewidth=0.9, zorder=2)
    dashes = (0, (3, 2.5))
    axis.axvline(THRESHOLD, color=INK_SECONDARY, linewidth=0.9, linestyle=dashes, zorder=2)
    handles.append(Line2D([0], [0], color=INK_SECONDARY, linewidth=0.9, linestyle=dashes,
                          label="Umbral práctico −0,25"))
    axis.set_ylim(position + 0.4, 0.55)
    axis.set_yticks(ticks)
    axis.set_yticklabels(labels, color=INK)
    for index in headers:
        tick = axis.get_yticklabels()[index]
        tick.set_color(INK_SECONDARY)
        tick.set_fontstyle("italic")
        tick.set_fontsize(args.cuerpo * 0.94)
    axis.tick_params(axis="y", length=0, pad=6)
    axis.tick_params(axis="x", colors=INK_SECONDARY, length=3)
    axis.xaxis.set_major_locator(MultipleLocator(1))
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: spanish(value, 0)))
    axis.grid(axis="x", color=GRID, linewidth=0.7, zorder=1)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)
    figure.supxlabel("Diferencia media de $f$ e IC 95 %; negativo favorece a la alternativa",
                     color=INK_SECONDARY, fontsize=args.cuerpo)
    figure.legend(handles=handles, loc="outside upper center", ncols=len(handles),
                  frameon=False, handlelength=2.2, labelcolor=INK, columnspacing=1.4)
    if args.valores:
        # Mean and interval of each row, as tick labels of a secondary axis.
        column = axis.secondary_yaxis("right")
        column.set_yticks(value_ticks, labels=values)
        column.tick_params(axis="y", length=0, pad=6, labelcolor=INK,
                           labelsize=args.cuerpo * 0.94)
        column.spines["right"].set_visible(False)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.salida)
    print(args.salida)


if __name__ == "__main__":
    main()
