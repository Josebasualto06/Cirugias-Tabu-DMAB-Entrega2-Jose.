"""Descriptive reading of the archived congestion study for the final report.

Nothing here was pre-registered and no search is executed. It only summarizes
columns that experiments/results/entrega2_congestion_90_109/runs.csv already
stores, so that every figure quoted in the report has a file behind it:

    python experiments/scripts/descriptivos_entrega3.py

These values are descriptive. They stay out of the confirmatory family C1-C4.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/results/entrega2_congestion_90_109/runs.csv"
OUTPUT = ROOT / "experiments/results/entrega3_descriptivos"
INITIAL = 30
HALF_BUDGET = 3030
LABELS = {
    "uniform3030": "Tabu uniforme (3.030)", "dmab3030": "Tabu + D-MAB (3.030)",
    "ucb3030": "Tabu + UCB1 (3.030)", "uniform6060": "Tabu prolongado (6.060)",
    "fixed_portfolio6060": "Cartera fija (6.060)",
}


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_method: dict[str, list[dict]] = {}
    for row in rows:
        by_method.setdefault(row["method"], []).append(row)

    results = []

    def add(measure: str, method: str, value: float, unit: str) -> None:
        results.append({"measure": measure, "method": method, "value": value, "unit": unit,
                        "runs": len(by_method[method])})

    # Share of evaluated candidates that the decoder repaired, averaged per run.
    # The 30 initial solutions count as evaluations but are not candidates.
    for method in ("uniform3030", "dmab3030", "ucb3030"):
        shares = [int(r["repaired_candidates"]) / (int(r["evaluations"]) - INITIAL)
                  for r in by_method[method]]
        add("mean_repaired_share", method, mean(shares), "share")

    # Page-Hinkley restarts of the bandit in each D-MAB trajectory.
    restarts = [int(r["dmab_restarts"]) for r in by_method["dmab3030"]]
    add("median_restarts", "dmab3030", median(restarts), "restarts per run")
    add("mean_restarts", "dmab3030", mean(restarts), "restarts per run")
    add("min_restarts", "dmab3030", min(restarts), "restarts per run")
    add("max_restarts", "dmab3030", max(restarts), "restarts per run")
    add("evaluations_per_median_restart", "dmab3030", HALF_BUDGET / median(restarts),
        "evaluations")
    add("max_restarts", "ucb3030", max(int(r["dmab_restarts"]) for r in by_method["ucb3030"]),
        "restarts per run")

    # Long Tabu runs whose last improvement happened in the first half of the budget.
    long_runs = by_method["uniform6060"]
    stalled = sum(int(r["last_improvement"]) <= HALF_BUDGET for r in long_runs)
    add("runs_without_improvement_after_3030", "uniform6060", stalled, "runs")
    add("share_without_improvement_after_3030", "uniform6060", stalled / len(long_runs), "share")

    # Component kept by the fixed portfolio (a full tie keeps uniform Tabu).
    portfolio = by_method["fixed_portfolio6060"]
    kept_dmab = sum(r["selected_path"] == "dmab" for r in portfolio)
    add("pairs_keeping_dmab_path", "fixed_portfolio6060", kept_dmab, "pairs")
    add("pairs_keeping_uniform_path", "fixed_portfolio6060", len(portfolio) - kept_dmab, "pairs")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "descriptivos.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(results[0]))
        writer.writeheader()
        writer.writerows(results)

    value = {(r["measure"], r["method"]): r["value"] for r in results}
    lines = [
        "# Descriptivos del estudio de congestión para el informe final", "",
        "**No estaban pre-registrados.** No ejecutan búsquedas ni usan semillas nuevas: "
        "resumen columnas de `entrega2_congestion_90_109/runs.csv` (semillas 90–109). "
        "Son descriptivos y no integran la familia C1–C4.", "",
        "## Reparación media por corrida", "",
        "Candidatos evaluados que el decodificador reparó, sobre 3.000 candidatos por corrida.", "",
        "| Método | Reparación media |", "|---|---:|",
    ]
    for method in ("uniform3030", "dmab3030", "ucb3030"):
        lines.append(f"| {LABELS[method]} | {value['mean_repaired_share', method]:.1%} |")
    lines += [
        "", "## Reinicios Page–Hinkley de D-MAB", "",
        f"Mediana {value['median_restarts', 'dmab3030']:.0f} reinicios por corrida de 3.030 "
        f"evaluaciones (media {value['mean_restarts', 'dmab3030']:.1f}; rango "
        f"{value['min_restarts', 'dmab3030']:.0f}–{value['max_restarts', 'dmab3030']:.0f}). "
        f"Equivale a un reinicio cada {value['evaluations_per_median_restart', 'dmab3030']:.0f} "
        "evaluaciones. UCB1 no reinicia por construcción "
        f"(máximo {value['max_restarts', 'ucb3030']:.0f}).", "",
        "## Tabu prolongado sin mejoras en su segunda mitad", "",
        f"En {value['runs_without_improvement_after_3030', 'uniform6060']:.0f} de "
        f"{len(long_runs)} corridas "
        f"({value['share_without_improvement_after_3030', 'uniform6060']:.1%}), la última mejora "
        "del Tabu prolongado ocurrió dentro de sus primeras 3.030 evaluaciones. La última mejora "
        "se registra por bloques de 150 evaluaciones.", "",
        "## Camino conservado por la cartera", "",
        f"La cartera conservó el camino D-MAB en "
        f"{value['pairs_keeping_dmab_path', 'fixed_portfolio6060']:.0f} de {len(portfolio)} pares "
        f"y el camino uniforme en "
        f"{value['pairs_keeping_uniform_path', 'fixed_portfolio6060']:.0f}. Un empate completo "
        "conserva Tabu uniforme.", "",
    ]
    (OUTPUT / "DESCRIPTIVOS.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "status": "completed", "kind": "descriptive, not pre-registered, no search executed",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print((OUTPUT / "DESCRIPTIVOS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
