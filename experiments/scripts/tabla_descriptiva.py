"""Build the LaTeX table of absolute results on the congestion catalog.

Reads experiments/results/entrega3_revision/descriptivos.csv and writes
informe/tablas/tabla_descriptiva.tex, so no figure is typed by hand:

    python experiments/scripts/tabla_descriptiva.py

Within each budget, bold marks the lowest value of each column.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/results/entrega3_revision/descriptivos.csv"
OUTPUT = ROOT / "informe/tablas/tabla_descriptiva.tex"
STUDY = "90-109"
COLUMNS = ("best", "objective", "worst", "sd", "rpd", "makespan", "blocked", "max_wait", "runtime")
RULES = (("fifo", "FIFO"), ("spt", "SPT"), ("lpt", "LPT"))
BLOCKS = (
    ("3.030 evaluaciones", (("uniform3030", "Uniforme"), ("dmab3030", "D-MAB"),
                            ("ucb3030", "UCB1"))),
    ("6.060 evaluaciones", (("uniform6060", "Prolongado"), ("two_uniform6060", "Dos Tabu"),
                            ("fixed_portfolio6060", "Cartera"))),
)


def number(value: float | None, bold: bool = False) -> str:
    if value is None:
        return "--"
    text = f"{value:.2f}".replace(".", ",")
    return rf"\textbf{{{text}}}" if bold else text


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        saved = {(row["measure"], row["item"]): float(row["value"])
                 for row in csv.DictReader(stream) if row["study"] == STUDY}
    last = len(COLUMNS) + 1
    lines = [
        "% Generado por experiments/scripts/tabla_descriptiva.py. No editar a mano.",
        f"% fuente: {SOURCE.relative_to(ROOT).as_posix()}",
        rf"\begin{{tabular}}{{@{{}}l{'r' * len(COLUMNS)}@{{}}}}",
        r" \toprule",
        r" & \multicolumn{5}{c}{Objetivo $f$ (unidades)} & "
        r"\multicolumn{3}{c}{Componentes (min)} & \\",
        rf" \cmidrule(lr){{2-6}}\cmidrule(lr){{7-9}}",
        r" Método & Mejor & Media & Peor & DE & RPD (\%) & $C_{\max}$ & $\sum W$ & $\max W$ "
        r"& $t$ (s)\\",
        r" \midrule",
    ]
    for key, label in RULES:
        values = [saved.get((column, key)) for column in COLUMNS]
        lines.append(f" {label} & " + " & ".join(number(value) for value in values) + r"\\")
    for title, methods in BLOCKS:
        lowest = {column: min(saved[column, key] for key, _ in methods) for column in COLUMNS}
        lines += [r" \midrule", rf" \multicolumn{{{last}}}{{@{{}}l}}{{\emph{{{title}}}}}\\"]
        for key, label in methods:
            cells = [number(saved[column, key],
                            f"{saved[column, key]:.2f}" == f"{lowest[column]:.2f}")
                     for column in COLUMNS]
            lines.append(f" {label} & " + " & ".join(cells) + r"\\")
    lines += [r" \bottomrule", r"\end{tabular}", ""]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
