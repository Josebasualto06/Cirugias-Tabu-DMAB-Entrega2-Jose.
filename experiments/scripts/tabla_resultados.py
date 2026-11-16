"""Build the LaTeX table of the pre-registered comparisons C1-C4.

Reads experiments/results/entrega2_congestion_90_109/comparisons.csv and writes
informe/tablas/tabla_comparaciones.tex, so no figure is typed by hand:

    python experiments/scripts/tabla_resultados.py

The reading column applies the three criteria of the pre-registered C1 rule to
every row: Holm p below 0.05, interval excluding zero and a mean of at least the
practical threshold. The rule was binding for C1 only.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/results/entrega2_congestion_90_109/comparisons.csv"
OUTPUT = ROOT / "informe/tablas/tabla_comparaciones.tex"
ALPHA = 0.05
THRESHOLD = 0.25
# Order by budget so that each block compares methods with equal evaluations.
ROWS = (
    ("C1", "D-MAB $-$ Tabu uniforme", "La mejora proviene de Tabu y no de aprender",
     "D-MAB", "Tabu uniforme"),
    ("C4", "D-MAB $-$ UCB1 sin reinicio", "El efecto proviene de UCB1 y no del reinicio",
     "D-MAB", "UCB1 sin reinicio"),
    ("C2", "Cartera $-$ Tabu prolongado", "La cartera mejora solo por consumir más evaluaciones",
     "la cartera", "Tabu prolongado"),
    ("C3", "Cartera $-$ dos Tabu", "La cartera mejora por repetir la búsqueda",
     "la cartera", "dos Tabu"),
)
BLOCKS = {3030: "3.030 evaluaciones por método", 6060: "6.060 evaluaciones por método"}


def number(value: float, digits: int = 3, signed: bool = False) -> str:
    """Spanish decimal comma and a typographic minus sign."""
    text = f"{abs(value):.{digits}f}".replace(".", "{,}")
    sign = "-" if value < 0 else ("+" if signed else "")
    return f"${sign}{text}$"


def reading(row: dict, alternative: str, reference: str) -> str:
    mean = float(row["mean_difference"])
    low, high = float(row["ci_low"]), float(row["ci_high"])
    decisive = (float(row["holm_p"]) < ALPHA and (high < 0 or low > 0)
                and abs(mean) >= THRESHOLD)
    if not decisive:
        return "No concluyente"
    return f"Favorece a {alternative if mean < 0 else reference}"


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        saved = {row["comparison"]: row for row in csv.DictReader(stream)}
    lines = [
        "% Generado por experiments/scripts/tabla_resultados.py. No editar a mano.",
        f"% fuente: {SOURCE.relative_to(ROOT).as_posix()}",
        r"\begin{tabular}{@{}l>{\raggedright\arraybackslash}p{0.20\textwidth}"
        r">{\raggedright\arraybackslash}p{0.24\textwidth}rcr"
        r">{\raggedright\arraybackslash}p{0.14\textwidth}@{}}",
        r" \toprule",
        r" Id & Alternativa $-$ referencia & Explicación alternativa que evalúa & Media & "
        r"IC 95~\% & $p$ Holm & Lectura\\",
    ]
    budget = None
    for code, label, explanation, alternative, reference in ROWS:
        row = saved[code]
        if int(row["budget"]) != budget:
            budget = int(row["budget"])
            lines += [r" \midrule", rf" \multicolumn{{7}}{{@{{}}l}}{{\emph{{{BLOCKS[budget]}}}}}\\"]
        interval = (f"[{number(float(row['ci_low']), signed=True)}; "
                    f"{number(float(row['ci_high']), signed=True)}]")
        lines.append(
            f" {code} & {label} & {explanation} & {number(float(row['mean_difference']), signed=True)}"
            f" & {interval} & {number(float(row['holm_p']))} & "
            f"{reading(row, alternative, reference)}\\\\")
    lines += [r" \bottomrule", r"\end{tabular}", ""]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUTPUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
