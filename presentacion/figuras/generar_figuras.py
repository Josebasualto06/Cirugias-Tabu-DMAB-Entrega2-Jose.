"""Build the presentation figures from archived results.

Run from any directory:

    python presentacion/figuras/generar_figuras.py

Reads the congestion calibration and the institutional header. It changes
nothing outside this folder.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CELLS = ROOT / "experiments/results/entrega2_calibracion_congestion_85_89/celdas.csv"
HEADER = ROOT / "informe/Portadas/imagenes/encabezado.png"
LOGO_BOX = (295, 140, 895, 305)
SERIES = "#4472C4"
INK = "#1F2933"
MUTED = "#5B6673"
GRID = "#E3E6EA"
LEVELS = ((1.0, "100 %"), (0.6, "60 %"), (0.4, "40 %"))
CHOSEN = (0.4, 1.0, 1.0)
OFFSETS = (-0.27, -0.16, -0.05, 0.05, 0.16, 0.27)


def calibration_figure() -> None:
    with CELLS.open(newline="", encoding="utf-8") as stream:
        cells = list(csv.DictReader(stream))
    plt.rcParams.update({"font.size": 9, "font.family": "DejaVu Sans", "pdf.fonttype": 42})
    figure, axis = plt.subplots(figsize=(3.45, 2.65), layout="constrained")
    axis.set_axisbelow(True)
    axis.yaxis.grid(True, color=GRID, linewidth=0.75)
    axis.axhline(50, color=MUTED, linewidth=1, zorder=2)
    chosen_point = None
    for position, (level, _) in enumerate(LEVELS):
        group = sorted((cell for cell in cells if float(cell["rho_surgeons"]) == level),
                       key=lambda cell: (-float(cell["rho_rooms"]), float(cell["rho_wait"])))
        for offset, cell in zip(OFFSETS, group):
            key = (float(cell["rho_surgeons"]), float(cell["rho_rooms"]), float(cell["rho_wait"]))
            share = 100 * float(cell["waiting_share"])
            if key == CHOSEN:
                chosen_point = (position + offset, share)
                continue
            axis.scatter(position + offset, share, s=46, color=SERIES, edgecolor="white",
                         linewidth=1.1, zorder=3, clip_on=False)
    axis.scatter(*chosen_point, s=86, marker="D", color=SERIES, edgecolor=INK, linewidth=1.1,
                 zorder=4)
    axis.annotate(f"Celda elegida: {chosen_point[1]:.0f} %", xy=chosen_point,
                  xytext=(0.82, 64), color=INK, fontsize=8.5, ha="center",
                  arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8,
                              "shrinkB": 5})
    axis.text(-0.46, 51.6, "Criterio: más de 50 %", color=MUTED, fontsize=8, ha="left")
    axis.text(0, 15, "Máximo 10 %", color=INK, fontsize=8.5, ha="center")
    axis.set_xlim(-0.5, 2.5)
    axis.set_ylim(0, 72)
    axis.set_yticks((0, 20, 40, 60), labels=("0 %", "20 %", "40 %", "60 %"))
    axis.set_xticks(range(len(LEVELS)), labels=[label for _, label in LEVELS])
    axis.set_xlabel("Cirujanos frente al catálogo estándar", color=MUTED)
    axis.set_ylabel("Soluciones finales con espera", color=MUTED)
    axis.tick_params(colors=MUTED, length=0)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)
    figure.savefig(HERE / "calibracion_espera.pdf")
    figure.savefig(HERE / "calibracion_espera.png", dpi=220)
    plt.close(figure)


def institutional_images() -> None:
    shutil.copyfile(HEADER, HERE / "encabezado.png")
    Image.open(HEADER).convert("RGB").crop(LOGO_BOX).save(HERE / "logo_pucv.png")


if __name__ == "__main__":
    calibration_figure()
    institutional_images()
    print(f"Figuras escritas en {HERE}")
