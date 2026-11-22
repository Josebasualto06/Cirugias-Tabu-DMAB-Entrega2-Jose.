"""Exploratory sensitivity of C1-C4 and E1 to the base instance of each scenario.

The 48 congestion instances were resampled from the 12 standard ones, four from
each. The registered analyses treat them as independent. This repeats those
analyses changing one thing only, the unit: base instead of instance. Test,
Holm family, bootstrap (function, replicates and seed) and the three criteria
stay the same. It was chosen after seeing the results, so it confirms nothing
and replaces no registered decision. All five contrasts are reported, whatever
their sign.

Before the sensitivity, the script repeats the registered analysis and stops
unless it reproduces the archived mean, interval and p values.

    python -X utf8 experiments/scripts/sensibilidad_bases.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import wilcoxon


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from experiments.run_study import holm  # noqa: E402
from experiments.study_congestion import (  # noqa: E402
    BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED, COMPARISONS, PRACTICAL_THRESHOLD, clustered_interval,
)


RESULTS = ROOT / "experiments/results"
OUTPUT = RESULTS / "entrega3_sensibilidad_bases"
CATALOG = ROOT / "instances/congestion"
ALPHA = 0.05
# Each study is its own family and restarts the registered bootstrap generator.
STUDIES = (
    ("90-109", "entrega2_congestion_90_109", COMPARISONS),
    ("120-139", "entrega3_confirmacion_ucb1", (("E1", "ucb3030", "uniform3030", 3030),)),
)


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def bases() -> dict[str, str]:
    """Base instance of each congestion scenario, read from its provenance."""
    found = {}
    for path in sorted(CATALOG.glob("HOSP-*.yaml")):
        match = re.search(r"resampled from (HOSP-STD-\d+-\d+)", path.read_text(encoding="utf-8"))
        assert match, path
        found[path.stem] = match.group(1)
    assert len(found) == 48 and set(Counter(found.values()).values()) == {4}
    return found


def analyze(runs: list[dict], comparisons: tuple, unit: dict[str, str]) -> list[dict]:
    """The registered analysis, with `unit` mapping each instance to its unit."""
    value = {(r["instance_id"], int(r["seed"]), r["method"]): float(r["objective"]) for r in runs}
    pairs = sorted({(instance, seed) for instance, seed, _ in value})
    units = sorted({unit[instance] for instance, _ in pairs})
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    found = []
    for code, method, reference, budget in comparisons:
        groups = {name: [] for name in units}
        for instance, seed in pairs:
            groups[unit[instance]].append(
                value[instance, seed, method] - value[instance, seed, reference])
        arrays = [np.asarray(groups[name]) for name in units]
        means = [float(array.mean()) for array in arrays]
        low, high = clustered_interval(arrays, rng)
        found.append({
            "comparison": code, "method": method, "reference": reference, "budget": budget,
            "units": len(units), "pairs": sum(map(len, arrays)),
            "mean_difference": float(np.concatenate(arrays).mean()),
            "ci_low": low, "ci_high": high,
            "units_negative": sum(mean < -1e-9 for mean in means),
            "standard_error": float(np.std(means, ddof=1) / math.sqrt(len(means))),
            "wilcoxon_p": float(wilcoxon(means, zero_method="zsplit").pvalue),
            "means": dict(zip(units, means)),
        })
    for row, adjusted in zip(found, holm([row["wilcoxon_p"] for row in found])):
        row["holm_p"] = adjusted
    return found


def criteria(row: dict) -> bool:
    """The three criteria in the direction of the mean, as in the report table."""
    return (row["holm_p"] < ALPHA and (row["ci_high"] < 0 or row["ci_low"] > 0)
            and abs(row["mean_difference"]) >= PRACTICAL_THRESHOLD)


def number(value: float, signed: bool = True) -> str:
    return (f"{value:+.3f}" if signed else f"{value:.3f}").replace(".", ",")


def main() -> None:
    if (OUTPUT / "manifest.json").exists():
        raise SystemExit(f"refusing to overwrite a completed analysis: {OUTPUT}")
    base = bases()
    same = {instance: instance for instance in base}
    summary, detail, sources = [], [], []
    for seeds, folder, comparisons in STUDIES:
        runs_path = RESULTS / folder / "runs.csv"
        archived_path = RESULTS / folder / "comparisons.csv"
        sources += [runs_path, archived_path]
        runs = read(runs_path)
        registered = analyze(runs, comparisons, same)
        archived = {row["comparison"]: row for row in read(archived_path)}
        for row in registered:
            for field in ("mean_difference", "ci_low", "ci_high", "wilcoxon_p", "holm_p"):
                if not math.isclose(row[field], float(archived[row["comparison"]][field]),
                                    abs_tol=1e-9):
                    raise AssertionError((row["comparison"], field))
        for before, after in zip(registered, analyze(runs, comparisons, base)):
            detail += [{"seeds": seeds, "comparison": after["comparison"], "base": name,
                        "mean_difference": mean} for name, mean in after.pop("means").items()]
            summary.append({
                "seeds": seeds, **after,
                "standard_error_ratio": after["standard_error"] / before["standard_error"],
                "criteria_by_instance": int(criteria(before)),
                "criteria_by_base": int(criteria(after)),
            })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write(OUTPUT / "comparisons.csv", summary)
    write(OUTPUT / "base_means.csv", detail)
    lines = [
        "# Sensibilidad exploratoria por instancia base", "",
        "**No estaba pre-registrada y se eligió después de ver los resultados.** No confirma "
        "hipótesis ni reemplaza las decisiones de C1–C4 o E1.", "",
        "- Único cambio: la unidad. Son 12 bases, cada una con sus 4 instancias y 80 pares, en "
        "lugar de 48 instancias con 20 pares.",
        "- Wilcoxon, la familia de Holm, el bootstrap (función, réplicas y semilla) y los tres "
        "criterios son los registrados. Antes se reprodujo el análisis registrado.",
        "- Con 12 unidades la prueba tiene menos potencia: perder significación no prueba "
        "ausencia de efecto.",
        "- C1–C4 y E1 son estudios distintos; por eso van en tablas separadas.",
        "- Razón de EE: error estándar de las medias por base sobre el de las medias por "
        "instancia. Sobre 1, la unidad registrada daba más precisión que esta.",
    ]
    for seeds, _, _ in STUDIES:
        lines += ["", f"## Semillas {seeds.replace('-', '–')}", "",
                  "| Id | Media | IC 95 % | p | p Holm | Bases con media negativa | Razón de EE "
                  "| Criterios por instancia | Criterios por base |",
                  "|---|---:|---|---:|---:|---:|---:|---|---|"]
        for row in summary:
            if row["seeds"] != seeds:
                continue
            lines.append(
                f"| {row['comparison']} | {number(row['mean_difference'])} | "
                f"[{number(row['ci_low'])}; {number(row['ci_high'])}] | "
                f"{number(row['wilcoxon_p'], False)} | {number(row['holm_p'], False)} | "
                f"{row['units_negative']} de {row['units']} | "
                f"{number(row['standard_error_ratio'], False)} | "
                f"{'cumple' if row['criteria_by_instance'] else 'no cumple'} | "
                f"{'cumple' if row['criteria_by_base'] else 'no cumple'} |")
    (OUTPUT / "SENSIBILIDAD.md").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                            newline="\n")
    code = [ROOT / "experiments/study_congestion.py", ROOT / "experiments/run_study.py"]
    manifest = {
        "status": "completed",
        "kind": "exploratory sensitivity, chosen after seeing the results; no decision changed",
        "only_change": "unit of analysis: base instance (12) instead of instance (48)",
        "bootstrap_replicates": BOOTSTRAP_REPLICATES, "bootstrap_seed": BOOTSTRAP_SEED,
        "registered_analysis_reproduced": True, "searches_run": 0,
        "software": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "scipy": scipy.__version__},
        "hash_convention": "sha256 of LF-normalized bytes",
        "sources_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path) for path in
                           sources + sorted(CATALOG.glob("HOSP-*.yaml"))},
        "code_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path) for path in code},
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "script_sha256": sha256_lf(Path(__file__)),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print((OUTPUT / "SENSIBILIDAD.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
