"""Forest plot of the paired differences and their clustered 95 % intervals.

Reads the archived comparison files and writes a vector figure. Three groups are
kept apart and labelled, because they are different studies:

* the pre-registered family C1-C4 (seeds 90-109);
* the exploratory contrast UCB1 - uniform Tabu (seeds 90-109, not pre-registered);
* the pre-registered confirmation E1 (seeds 120-139), if that study is complete.

    python experiments/scripts/forest_comparaciones.py
    python experiments/scripts/forest_comparaciones.py --salida presentacion_final/figuras/forest_comparaciones.pdf \
        --ancho 24 --alto 9.6 --cuerpo 13 --fuente sans-serif --valores

Group identity never depends on colour alone: each group has its own marker and
a header above its rows. The palette is the first three slots of a validated
colour-blind-safe set.
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
        "header": "Familia pre-registrada C1–C4 · semillas 90–109",
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
    parser.add_argument("--alto", type=float, default=7.6, help="height in cm")
    parser.add_argument("--cuerpo", type=float, default=9.0, help="font size in points")
    parser.add_argument("--fuente", default="serif")
    parser.add_argument("--valores", action="store_true",
                        help="print mean and interval at the right of each row")
    args = parser.parse_args()

    plt.rcParams.update({
        "font.family": args.fuente,
        "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
        "font.sans-serif": ["Latin Modern Sans", "Arial", "DejaVu Sans"],
        "font.size": args.cuerpo, "pdf.fonttype": 42, "axes.unicode_minus": False,
        "mathtext.fontset": "stix" if args.fuente == "serif" else "dejavusans",
    })
    figure, axis = plt.subplots(figsize=(args.ancho / 2.54, args.alto / 2.54))
    figure.patch.set_facecolor("white")

    position, ticks, labels, handles = 0.0, [], [], []
    for index, group in enumerate(groups()):
        if index:
            position -= 0.55
        axis.text(0.0, position, group["header"], transform=axis.get_yaxis_transform(),
                  ha="left", va="center", color=INK_SECONDARY, style="italic",
                  fontsize=args.cuerpo * 0.94)
        position -= 1.0
        face = group["color"] if group["filled"] else "white"
        for label, row in group["rows"]:
            mean = float(row.get("mean_difference"))
            low, high = float(row["ci_low"]), float(row["ci_high"])
            axis.plot([low, high], [position, position], color=group["color"], linewidth=1.6,
                      solid_capstyle="round", zorder=3)
            axis.plot([mean], [position], marker=group["marker"], markersize=6.5,
                      markerfacecolor=face, markeredgecolor=group["color"],
                      markeredgewidth=1.4, linestyle="none", zorder=4)
            if args.valores:
                axis.text(1.015, position,
                          f"{spanish(mean)}  [{spanish(low)}; {spanish(high)}]",
                          transform=axis.get_yaxis_transform(), ha="left", va="center",
                          color=INK, fontsize=args.cuerpo * 0.94)
            ticks.append(position)
            labels.append(label)
            position -= 1.0
        handles.append(Line2D([0], [0], color=group["color"], linewidth=1.6,
                              marker=group["marker"], markersize=6.5, markerfacecolor=face,
                              markeredgecolor=group["color"], markeredgewidth=1.4,
                              label=group["legend"]))

    axis.axvline(0, color=INK_SECONDARY, linewidth=0.9, zorder=2)
    axis.axvline(THRESHOLD, color=INK_SECONDARY, linewidth=0.9, linestyle=(0, (3, 2.5)), zorder=2)
    # Keep a free band under the last row for the threshold label.
    axis.set_ylim(position - 0.1, 0.75)
    axis.text(THRESHOLD - 0.06, position + 0.02, "umbral práctico −0,25", ha="right",
              va="bottom", color=INK_SECONDARY, fontsize=args.cuerpo * 0.9)
    axis.set_yticks(ticks)
    axis.set_yticklabels(labels, color=INK)
    axis.tick_params(axis="y", length=0, pad=6)
    axis.tick_params(axis="x", colors=INK_SECONDARY, length=3)
    axis.xaxis.set_major_locator(MultipleLocator(1))
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: spanish(value, 0)))
    axis.grid(axis="x", color=GRID, linewidth=0.7, zorder=1)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)
    axis.set_xlabel("Diferencia media de $f$ (alternativa − referencia) e IC 95 %.  "
                    "Negativo favorece a la alternativa", color=INK_SECONDARY)
    axis.legend(handles=handles, loc="lower right", frameon=False, handlelength=2.2,
                labelcolor=INK, borderaxespad=0.2)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.salida, bbox_inches="tight", pad_inches=0.03)
    print(args.salida)


if __name__ == "__main__":
    main()
