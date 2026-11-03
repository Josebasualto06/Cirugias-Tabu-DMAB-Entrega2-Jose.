"""Add a practical-difference reading to the generated study analysis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MARKER = "## Interpretación con umbral práctico"
PRACTICAL_THRESHOLD = 0.25  # minutes, 15 seconds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path,
                        default=ROOT / "experiments/results/validation_40_59")
    args = parser.parse_args()
    directory = args.directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed":
        raise ValueError("validation must be complete")
    with (directory / "runs.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_key = {(row["instance_id"], int(row["seed"]), row["policy"]): row for row in rows}
    instances = sorted(manifest["instance_digests"])
    seeds = manifest["seeds"]
    paragraphs = [
        MARKER, "",
        "Una diferencia de menos de **0,25 min (15 s)** se considera pequeña "
        "para esta lectura descriptiva. El conteo exacto a tolerancia `1e−9` "
        "también está arriba; incluye cambios diminutos causados por el "
        "término de desempate `10⁻⁶ × suma de inicios`.", "",
        "| Comparación con Tabu mixto | Gana >0,25 min | Diferencia ≤0,25 min | "
        "Pierde >0,25 min | Instancias gana / similar / pierde |",
        "|---|---:|---:|---:|---:|",
    ]
    for policy, label in (("dmab", "D-MAB"), ("ucb", "UCB1")):
        differences = np.array([
            float(by_key[instance, seed, policy]["objective"])
            - float(by_key[instance, seed, "uniform"]["objective"])
            for instance in instances for seed in seeds
        ])
        medians = np.array([
            np.median([float(by_key[instance, seed, policy]["objective"])
                       - float(by_key[instance, seed, "uniform"]["objective"])
                       for seed in seeds])
            for instance in instances
        ])
        threshold = PRACTICAL_THRESHOLD
        pair_counts = (int(np.sum(differences < -threshold)),
                       int(np.sum(np.abs(differences) <= threshold)),
                       int(np.sum(differences > threshold)))
        instance_counts = (int(np.sum(medians < -threshold)),
                           int(np.sum(np.abs(medians) <= threshold)),
                           int(np.sum(medians > threshold)))
        paragraphs.append(f"| {label} | {pair_counts[0]} | {pair_counts[1]} | "
                          f"{pair_counts[2]} | {instance_counts[0]} / "
                          f"{instance_counts[1]} / {instance_counts[2]} |")
    dmab_median = float(np.median([
        np.median([float(by_key[instance, seed, "dmab"]["objective"])
                   - float(by_key[instance, seed, "uniform"]["objective"])
                   for seed in seeds]) for instance in instances]))
    paragraphs += [
        "", "La mediana de las doce diferencias medianas de D-MAB frente a Tabu "
        f"mixto es **{dmab_median:+.2f} min** y el signo cambia entre instancias. "
        "La lectura inferencial está en la sección de pruebas estadísticas "
        "(Wilcoxon con corrección de Holm).", "",
        "Las 12 instancias de validación **ya se habían usado para elegir la "
        f"arquitectura**. Las semillas {seeds[0]}–{seeds[-1]} son nuevas, pero no "
        "se ensayaron instancias nuevas. La generalización fuera de este catálogo "
        "queda pendiente.", "",
        "FIFO, SPT y LPT forman parte de las 30 soluciones iniciales de Tabu. "
        "Por ello superar la mejor de esas reglas no es evidencia "
        "independiente del beneficio de Tabu o de D-MAB: Tabu comienza al "
        "menos tan bien como la mejor regla.", "",
    ]
    blocking_counts = {
        policy: sum(float(row["blocked_minutes"]) > 1e-9 for row in rows
                    if row["policy"] == policy)
        for policy in ("uniform", "dmab", "ucb")
    }
    paragraphs += [
        "Las medianas de bloqueo total son cero en todas las instancias y "
        f"políticas. Entre {len(instances) * len(seeds)} calendarios finales por política, hubo bloqueo "
        f"positivo en {blocking_counts['uniform']} de Tabu mixto, "
        f"{blocking_counts['dmab']} de D-MAB y {blocking_counts['ucb']} de UCB1. "
        "Por ello este catálogo y decodificador discriminan poco en bloqueo; "
        "la variación del objetivo proviene principalmente del makespan. "
        "No se puede afirmar que el controlador reduzca los quirófanos "
        "bloqueados de forma general.", "",
    ]
    path = directory / "ANALYSIS.md"
    original = path.read_text(encoding="utf-8")
    base = original.split(MARKER)[0].rstrip()
    base = base.replace("Mediana de las 12 diferencias medianas: -0.000.",
                        "Mediana de las 12 diferencias medianas: ≈0.000.")
    base = base.replace("Mediana de las 12 diferencias medianas: +0.000.",
                        "Mediana de las 12 diferencias medianas: ≈0.000.")
    path.write_text(base + "\n\n" + "\n".join(paragraphs), encoding="utf-8")
    (directory / "analysis_editorial_manifest.json").write_text(json.dumps({
        "source": "runs.csv and generated ANALYSIS.md",
        "runs_sha256": hashlib.sha256((directory / "runs.csv").read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "practical_threshold_minutes": PRACTICAL_THRESHOLD,
        "same_instances_as_exploration": True,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
