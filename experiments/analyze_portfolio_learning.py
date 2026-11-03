"""Check whether learned allocation adds value beyond fixed portfolios/restarts.

These secondary comparisons are exploratory. They do not tune or rerun the
search policies. The primary four comparisons remain in summary.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from experiments.compare_portfolios import LABELS, clustered_interval, write_csv


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments/results/portfolios_60_79"
COMPARISONS = (
    ("fixed_portfolio6060", "two_uniform6060"),
    ("learned_free6060", "fixed_portfolio6060"),
    ("learned_free6060", "two_uniform6060"),
    ("learned_protected6060", "fixed_portfolio6060"),
    ("learned_protected6060", "two_uniform6060"),
)


def main():
    with (OUTPUT / "runs.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    indexed = {(r["instance_id"], int(r["seed"]), r["method"]): float(r["objective"]) for r in rows}
    keys = sorted({(r["instance_id"], int(r["seed"])) for r in rows})
    results = []
    for method, reference in COMPARISONS:
        grouped = defaultdict(list)
        for instance, seed in keys:
            grouped[instance].append(indexed[instance, seed, method] - indexed[instance, seed, reference])
        differences = [d for group in grouped.values() for d in group]
        instance_means = [np.mean(group) for group in grouped.values()]
        ci_low, ci_high = clustered_interval(grouped)
        p = (1.0 if np.all(np.abs(instance_means) <= 1e-9) else
             float(wilcoxon(instance_means, zero_method="zsplit").pvalue))
        results.append({
            "method": method, "reference": reference,
            "mean_difference": float(np.mean(differences)),
            "ci_low": ci_low, "ci_high": ci_high,
            "wins": sum(d < -.25 for d in differences),
            "similar": sum(abs(d) <= .25 for d in differences),
            "losses": sum(d > .25 for d in differences),
            "p_instance_means": p, "holm_p": 1.0,
        })
    running = 0.0
    for rank, row in enumerate(sorted(results, key=lambda r: r["p_instance_means"])):
        running = max(running, min(1.0, (len(results) - rank) * row["p_instance_means"]))
        row["holm_p"] = running
    write_csv(OUTPUT / "learning_added_value.csv", results)
    lines = ["# Aporte del reparto aprendido", "",
             "Comparaciones secundarias exploratorias con 6.060 evaluaciones por método. "
             "Negativo favorece al método de la primera columna. No se ajustaron parámetros "
             "ni se repitió la búsqueda a partir de estos resultados.", "",
             "| Método | Referencia | Diferencia media | IC 95 % agrupado | p Holm |",
             "|---|---|---:|---|---:|"]
    for row in results:
        lines.append(f"| {LABELS[row['method']]} | {LABELS[row['reference']]} | "
                     f"{row['mean_difference']:+.3f} | [{row['ci_low']:+.3f}, {row['ci_high']:+.3f}] | "
                     f"{row['holm_p']:.3f} |")
    lines += ["", "Los intervalos agrupan por instancia y semilla; Wilcoxon usa las doce "
              "medias por instancia. Holm corrige estas cinco comparaciones secundarias como "
              "familia separada de las cuatro comparaciones principales. Se interpretan "
              "exploratoriamente, sin convertir la falta de significación en prueba de equivalencia.", ""]
    (OUTPUT / "LEARNING.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
