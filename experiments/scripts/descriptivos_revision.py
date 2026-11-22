"""Descriptive measures added by the final revision of the report.

No hypothesis is tested here and no decision of the protocols changes. The
script reads archived runs and the audited replay, and writes one row per
figure quoted in the report:

    python -X utf8 experiments/scripts/reejecutar_corridas.py   # once
    python -X utf8 experiments/scripts/descriptivos_revision.py

It covers dispersion and RPD, components, cost, size, constructive rules, the
width of the hierarchical bootstrap, and every study on the standard catalog
that compared these methods, whether it favors the conclusion or not.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments/results"
OUTPUT = RESULTS / "entrega3_revision"
REPLAY = RESULTS / "entrega3_revision_reejecucion"
FAMILY = RESULTS / "entrega2_congestion_90_109/runs.csv"
CONFIRMATION = RESULTS / "entrega3_confirmacion_ucb1/runs.csv"
RULES = RESULTS / "entrega2_congestion_90_109/baselines.csv"
OLD = RESULTS / "validation_20_39/runs.csv"
CURRENT = RESULTS / "validation_40_59/runs.csv"
PORTFOLIOS = RESULTS / "portfolios_60_79/runs.csv"
CALIBRATION = RESULTS / "calibration_0_5/runs.csv"
PILOT = RESULTS / "entrega2_tiempo_110_114/summary.csv"
PILOT_RUNS = RESULTS / "entrega2_tiempo_110_114/runs.csv"
SOURCES = (FAMILY, CONFIRMATION, RULES, OLD, CURRENT, PORTFOLIOS, CALIBRATION, PILOT, PILOT_RUNS,
           REPLAY / "runs.csv")

SIZES = (15, 20, 25, 30)
MOVES = ("swap", "insert", "room_1", "room_2", "room_pair")
CONTRASTS = {
    "C1": ("90-109", "dmab3030", "uniform3030"),
    "C2": ("90-109", "fixed_portfolio6060", "uniform6060"),
    "C3": ("90-109", "fixed_portfolio6060", "two_uniform6060"),
    "C4": ("90-109", "dmab3030", "ucb3030"),
    "E1": ("120-139", "ucb3030", "uniform3030"),
}


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def column(rows: list[dict], name: str) -> np.ndarray:
    return np.array([float(row[name]) for row in rows])


def paired(rows: list[dict], key: str, alternative: str, reference: str,
           field: str = "objective") -> dict[str, np.ndarray]:
    """Return alternative minus reference, grouped by instance."""
    saved = {(r["instance_id"], r["seed"], r[key]): float(r[field]) for r in rows}
    groups = defaultdict(list)
    for (instance, seed, name), value in saved.items():
        if name == alternative:
            groups[instance].append(value - saved[instance, seed, reference])
    return {instance: np.array(values) for instance, values in sorted(groups.items())}


def main() -> None:
    replay = json.loads((REPLAY / "manifest.json").read_text(encoding="utf-8"))
    assert replay["status"] == "completed" and replay["mismatches"] == 0

    found: list[dict] = []

    def add(study: str, measure: str, item: str, value: float) -> None:
        found.append({"study": study, "measure": measure, "item": item, "value": float(value)})

    studies = {"90-109": read(FAMILY), "120-139": read(CONFIRMATION)}

    # RPD reference: best value of each instance over both congestion studies.
    best_known: dict[str, float] = {}
    for row in studies["90-109"] + studies["120-139"]:
        instance, value = row["instance_id"], float(row["objective"])
        best_known[instance] = min(value, best_known.get(instance, value))

    def rpd(rows: list[dict]) -> np.ndarray:
        reference = np.array([best_known[row["instance_id"]] for row in rows])
        return 100 * (column(rows, "objective") - reference) / reference

    rules = read(RULES)
    best_rule: dict[str, float] = {}
    for row in rules:
        instance, value = row["instance_id"], float(row["objective"])
        best_rule[instance] = min(value, best_rule.get(instance, value))
    for rule in ("fifo", "spt", "lpt"):
        current = [row for row in rules if row["rule"] == rule]
        for measure in ("objective", "makespan", "blocked", "max_wait"):
            add("90-109", measure, rule, column(current, measure).mean())
        add("90-109", "rpd", rule, rpd(current).mean())

    for study, rows in studies.items():
        for method in sorted({row["method"] for row in rows}):
            current = [row for row in rows if row["method"] == method]
            groups = defaultdict(list)
            for row in current:
                groups[row["instance_id"]].append(float(row["objective"]))
            values = [np.array(group) for _, group in sorted(groups.items())]
            add(study, "best", method, np.mean([v.min() for v in values]))
            add(study, "objective", method, np.mean([v.mean() for v in values]))
            add(study, "worst", method, np.mean([v.max() for v in values]))
            add(study, "sd", method, np.mean([v.std(ddof=1) for v in values]))
            add(study, "rpd", method, rpd(current).mean())
            for measure in ("makespan", "blocked", "max_wait"):
                add(study, measure, method, column(current, measure).mean())
            add(study, "runtime", method, np.median(column(current, "runtime_seconds")))
            add(study, "improvement_over_best_rule", method, 100 * np.mean(
                [(best_rule[i] - np.mean(v)) / best_rule[i] for i, v in groups.items()]))
        # Median of the paired time ratios: both runs shared the load of the machine.
        for method in ("dmab3030", "ucb3030"):
            if not any(row["method"] == method for row in rows):
                continue
            saved = {(r["instance_id"], r["seed"], r["method"]): float(r["runtime_seconds"])
                     for r in rows}
            ratios = [saved[i, s, method] / saved[i, s, "uniform3030"]
                      for i, s, m in saved if m == method]
            add(study, "time_overhead", method, 100 * (np.median(ratios) - 1))

    for code, (study, alternative, reference) in CONTRASTS.items():
        rows = studies[study]
        groups = paired(rows, "method", alternative, reference)
        means = np.array([values.mean() for values in groups.values()])
        base = column([r for r in rows if r["method"] == reference], "objective").mean()
        add(study, "relative_difference", code, 100 * means.mean() / base)
        add(study, "instances_better", code, (means < -1e-9).sum())
        # The bootstrap adds seed noise to means that already contain it.
        between = means.var() / len(means)
        within = np.mean([v.var() / len(v) for v in groups.values()]) / len(groups)
        add(study, "bootstrap_se_ratio", code, np.sqrt((between + within) / between))
        for size in SIZES:
            selected = np.array([v.mean() for i, v in groups.items() if f"-{size}-" in i])
            add(study, f"difference_{size}", code, selected.mean())
            add(study, f"instances_better_{size}", code, (selected < -1e-9).sum())

    # Standard catalog. Every archived study is listed, with either sign.
    standard = (
        ("20-39", OLD, "policy", (("dmab", "uniform"), ("ucb", "uniform"), ("dmab", "ucb"))),
        ("40-59", CURRENT, "policy", (("dmab", "uniform"), ("ucb", "uniform"), ("dmab", "ucb"))),
        ("60-79", PORTFOLIOS, "method", (
            ("dmab3030", "uniform3030"), ("fixed_portfolio6060", "uniform6060"),
            ("fixed_portfolio6060", "two_uniform6060"))),
        ("110-114", PILOT_RUNS, "policy", (("dmab", "uniform"),)),
    )
    for study, path, key, pairs in standard:
        rows = read(path)
        for alternative, reference in pairs:
            means = np.array([v.mean() for v in paired(rows, key, alternative, reference).values()])
            add(study, "difference", f"{alternative}-{reference}", means.mean())
            add(study, "instances_better", f"{alternative}-{reference}", (means < -1e-9).sum())
    for row in read(PILOT):
        add("110-114", f"difference_{row['size']}", "dmab-uniform",
            float(row["mean_difference_dmab_minus_uniform"]))

    calibration = read(CALIBRATION)
    base_variant = "uniform|solution|C=1.0|lambda=0.35"
    add("0-5", "variants", "all", len({row["variant"] for row in calibration}))
    for item, variant in (("chosen", "dmab|solution|C=0.1|lambda=1.0"),
                          ("runner_up", "dmab|solution|C=1.0|lambda=0.35"),
                          ("lambda_10", "dmab|solution|C=0.1|lambda=10.0")):
        groups = paired(calibration, "variant", variant, base_variant)
        add("0-5", "difference", item, np.mean([v.mean() for v in groups.values()]))

    replayed = read(REPLAY / "runs.csv")
    for study, folder in (("90-109", FAMILY), ("120-139", CONFIRMATION)):
        rows = [row for row in replayed if row["study"] == folder.parent.name]
        uniform = [row for row in rows if row["method"] == "uniform3030"]
        base = column(uniform, "decoded_proposals").mean()
        for method in sorted({row["method"] for row in rows}):
            current = [row for row in rows if row["method"] == method]
            decoded = column(current, "decoded_proposals").mean()
            add(study, "decoded_proposals", method, decoded)
            add(study, "decoded_overhead", method, 100 * (decoded / base - 1))
            evaluated = {move: column(current, f"evaluated_{move}").sum() for move in MOVES}
            for move in MOVES:
                add(study, f"share_{move}", method, 100 * evaluated[move] / sum(evaluated.values()))
    add("90-139", "replayed_runs", "all", len(replayed))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "descriptivos.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(found[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(found)

    lines = [
        "# Descriptivos de la revisión final del informe", "",
        "**No estaban pre-registrados.** No prueban hipótesis ni cambian las decisiones de C1–C4 "
        "o E1. Cada estudio conserva su rango de semillas y tiene su propia tabla.", "",
        "- RPD: respecto del mejor valor por instancia entre las semillas 90–109 y 120–139. "
        "No es un óptimo ni una cota.",
        "- Sobrecosto de tiempo: mediana de los cocientes pareados de tiempo, con procesos concurrentes.",
        "- Propuestas decodificadas: incluyen duplicados, que no consumen evaluaciones.",
        "- `bootstrap_se_ratio`: error estándar del bootstrap jerárquico sobre el de las medias por "
        "instancia. Solo diagnostica el intervalo; no lo reemplaza.",
        "- Semillas 20–39: configuración anterior (C = 1, λ = 0,35). Semillas 40–59: la vigente. "
        "No se combinan.",
    ]
    for study in dict.fromkeys(row["study"] for row in found):
        lines += ["", f"## Semillas {study.replace('-', '–')}", "",
                  "| Medida | Elemento | Valor |", "|---|---|---:|"]
        lines += [f"| {r['measure']} | {r['item']} | {r['value']:.3f} |"
                  for r in found if r["study"] == study]
    (OUTPUT / "DESCRIPTIVOS.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    manifest = {
        "status": "completed", "kind": "descriptive, not pre-registered, no hypothesis tested",
        "sources_sha256": {path.relative_to(ROOT).as_posix():
                           hashlib.sha256(path.read_bytes()).hexdigest() for path in SOURCES},
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(found)} descriptivos en {OUTPUT}")


if __name__ == "__main__":
    main()
