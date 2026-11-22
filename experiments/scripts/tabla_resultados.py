"""Build the LaTeX table of the pre-registered comparisons C1-C4.

Reads experiments/results/entrega2_congestion_90_109/comparisons.csv, the
exploratory reanalysis by base instance in entrega3_sensibilidad_bases and the
differences by size in entrega3_revision, and writes
informe/tablas/tabla_comparaciones.tex, so no figure is typed by hand:

    python experiments/scripts/tabla_resultados.py

A bold mean meets the three criteria of the pre-registered C1 rule: Holm p below
0.05, interval excluding zero and a mean of at least the practical threshold.
The rule was binding for C1 only. The columns by base and by size are exploratory.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/results/entrega2_congestion_90_109/comparisons.csv"
BY_SIZE = ROOT / "experiments/results/entrega3_revision/descriptivos.csv"
BY_BASE = ROOT / "experiments/results/entrega3_sensibilidad_bases/comparisons.csv"
OUTPUT = ROOT / "informe/tablas/tabla_comparaciones.tex"
ALPHA = 0.05
THRESHOLD = 0.25
SIZES = (15, 20, 25, 30)
# Order by budget so that each block compares methods with equal evaluations.
ROWS = (
    ("C1", "D-MAB $-$ uniforme"),
    ("C4", "D-MAB $-$ UCB1"),
    ("C2", "Cartera $-$ prolongado"),
    ("C3", "Cartera $-$ dos Tabu"),
)
BLOCKS = {3030: "3.030 evaluaciones por método", 6060: "6.060 evaluaciones por método"}


def number(value: float, digits: int = 3, signed: bool = False) -> str:
    """Spanish decimal comma and a typographic minus sign."""
    text = f"{abs(value):.{digits}f}".replace(".", "{,}")
    sign = "-" if value < 0 else ("+" if signed else "")
    return f"${sign}{text}$"


def decisive(row: dict) -> bool:
    mean = float(row["mean_difference"])
    low, high = float(row["ci_low"]), float(row["ci_high"])
    return (float(row["holm_p"]) < ALPHA and (high < 0 or low > 0)
            and abs(mean) >= THRESHOLD)


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        saved = {row["comparison"]: row for row in csv.DictReader(stream)}
    with BY_SIZE.open(newline="", encoding="utf-8") as stream:
        described = {(row["measure"], row["item"]): float(row["value"])
                     for row in csv.DictReader(stream) if row["study"] == "90-109"}
    with BY_BASE.open(newline="", encoding="utf-8") as stream:
        nested = {row["comparison"]: row for row in csv.DictReader(stream)}
    lines = [
        "% Generado por experiments/scripts/tabla_resultados.py. No editar a mano.",
        f"% fuente: {SOURCE.relative_to(ROOT).as_posix()}",
        f"% fuente de las columnas por tamaño: {BY_SIZE.relative_to(ROOT).as_posix()}",
        f"% fuente de las columnas por base: {BY_BASE.relative_to(ROOT).as_posix()}",
        r"\begin{tabular}{@{}llrcrcrrrrr@{}}",
        r" \toprule",
        r" & & \multicolumn{3}{c}{Registrado: 48 instancias} & "
        r"\multicolumn{2}{c}{Por base: 12 bases} & "
        r"\multicolumn{4}{c}{Media por n.º de cirugías}\\",
        r" \cmidrule(lr){3-5}\cmidrule(lr){6-7}\cmidrule(l){8-11}",
        r" Id & Alternativa $-$ referencia & Media & IC 95~\% & $p$ Holm & "
        r"IC 95~\% & $p$ Holm & "
        + " & ".join(str(size) for size in SIZES) + r"\\",
    ]
    budget = None
    for code, label in ROWS:
        row = saved[code]
        if int(row["budget"]) != budget:
            budget = int(row["budget"])
            lines += [r" \midrule",
                      rf" \multicolumn{{11}}{{@{{}}l}}{{\emph{{{BLOCKS[budget]}}}}}\\"]
        mean = number(float(row["mean_difference"]), signed=True)
        if decisive(row):
            mean = rf"$\mathbf{{{mean.strip('$')}}}$"
        interval = (f"[{number(float(row['ci_low']), signed=True)}; "
                    f"{number(float(row['ci_high']), signed=True)}]")
        other = nested[code]
        by_base = (f"[{number(float(other['ci_low']), signed=True)}; "
                   f"{number(float(other['ci_high']), signed=True)}] & "
                   f"{number(float(other['holm_p']))}")
        sizes = " & ".join(number(described[f"difference_{size}", code], 2, signed=True)
                           for size in SIZES)
        lines.append(f" {code} & {label} & {mean} & {interval} & "
                     f"{number(float(row['holm_p']))} & {by_base} & {sizes}\\\\")
    lines += [r" \bottomrule", r"\end{tabular}", ""]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
