"""Analyze the Page–Hinkley ablation from a completed validation study."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from surgery_optim.bandit import MOVES


ROOT = Path(__file__).resolve().parents[1]
METRICS = ("objective", "makespan_minutes", "blocked_minutes")


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def median(values) -> float:
    return float(np.median(list(values)))


def analyze(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed":
        raise ValueError("study must be completed before ablation analysis")
    runs = read_rows(directory / "runs.csv")
    summary = read_rows(directory / "summary.csv")
    read_rows(directory / "baselines.csv")
    by_key = {(row["instance_id"], int(row["seed"]), row["policy"]): row for row in runs}
    instances = sorted(manifest["instance_digests"])
    seeds = manifest["seeds"]
    pairs = []
    for instance in instances:
        for metric in METRICS:
            diffs = np.array([
                float(by_key[instance, seed, "dmab"][metric])
                - float(by_key[instance, seed, "ucb"][metric]) for seed in seeds
            ])
            pairs.append({
                "instance_id": instance,
                "size": int(next(row["size"] for row in runs if row["instance_id"] == instance)),
                "metric": metric,
                "median_dmab_minus_ucb": float(np.median(diffs)),
                "mean_dmab_minus_ucb": float(np.mean(diffs)),
                "dmab_wins": int(np.sum(diffs < -1e-9)),
                "ties": int(np.sum(np.abs(diffs) <= 1e-9)),
                "ucb_wins": int(np.sum(diffs > 1e-9)),
            })
    with (directory / "ablation_dmab_vs_ucb.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)

    pair_obj = [row for row in pairs if row["metric"] == "objective"]
    wins = sum(row["dmab_wins"] for row in pair_obj)
    ties = sum(row["ties"] for row in pair_obj)
    losses = sum(row["ucb_wins"] for row in pair_obj)
    instance_differences = [row["median_dmab_minus_ucb"] for row in pair_obj]
    dmab_better_instances = sum(value < -1e-9 for value in instance_differences)
    tied_instances = sum(abs(value) <= 1e-9 for value in instance_differences)
    ucb_better_instances = sum(value > 1e-9 for value in instance_differences)

    choices = {}
    for policy in ("dmab", "ucb"):
        subset = [row for row in runs if row["policy"] == policy]
        choices[policy] = {move: sum(int(row[f"evaluated_{move}"]) for row in subset)
                           for move in MOVES}
    restart_values = [int(row["dmab_restarts"]) for row in runs if row["policy"] == "dmab"]
    runtime = {policy: median(float(row["runtime_seconds"]) for row in runs
                              if row["policy"] == policy)
               for policy in ("uniform", "dmab", "ucb")}

    lines = [
        "# Ablación: D-MAB frente a UCB1 sin Page–Hinkley", "",
        "Se emparejan 20 semillas nuevas por cada una de las 12 instancias; "
        "menor objetivo es mejor. La diferencia es `D-MAB − UCB1`.", "",
        "| Instancia | Mediana D-MAB | Mediana UCB1 | Mediana diferencia pareada | "
        "D-MAB gana / empate / UCB1 gana |",
        "|---|---:|---:|---:|---:|",
    ]
    lookup = {(row["instance_id"], row["policy"]): float(row["median_objective"])
              for row in summary}
    for row in pair_obj:
        instance = row["instance_id"]
        lines.append(f"| {instance} | {lookup[instance, 'dmab']:.3f} | "
                     f"{lookup[instance, 'ucb']:.3f} | "
                     f"{row['median_dmab_minus_ucb']:+.3f} | "
                     f"{row['dmab_wins']} / {row['ties']} / {row['ucb_wins']} |")
    lines += [
        "", f"En los {len(runs)//3} pares instancia-semilla, D-MAB gana {wins}, "
        f"empata {ties} y pierde {losses} frente a UCB1 en objetivo. "
        f"A nivel de 12 instancias (mediana pareada), gana en "
        f"{dmab_better_instances}, empata en {tied_instances} y pierde en "
        f"{ucb_better_instances}; la mediana de esas 12 diferencias es "
        f"{median(instance_differences):+.3f}.",
        "", "Mediana del tiempo por corrida (segundos): "
        + ", ".join(f"{policy}={runtime[policy]:.3f}" for policy in runtime) + ".",
        f" Mediana de reinicios Page–Hinkley por corrida D-MAB: {median(restart_values):.1f}.",
        "", "Movimientos evaluados acumulados en las 240 corridas por política:", "",
        "| Política | Swap | Insert | Sala anestesia | Sala cirugía | Ambas salas |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for policy in ("dmab", "ucb"):
        counts = choices[policy]
        lines.append(f"| {policy} | " + " | ".join(str(counts[move]) for move in MOVES) + " |")
    lines += [
        "", "La selección de brazos y los reinicios muestran que el controlador "
        "sí cambió sus preferencias. Una ventaja numérica en este catálogo no "
        "demuestra un beneficio general de Page–Hinkley; para interpretar el "
        "efecto también hay que comparar las métricas y el costo de ejecución.",
        "", "La diferencia entre medianas de política puede no ser igual a la "
        "mediana de diferencias emparejadas; ambas se muestran explícitamente.", "",
    ]
    (directory / "ABLATION.md").write_text("\n".join(lines), encoding="utf-8")
    analysis_manifest = {
        "source_manifest": "manifest.json",
        "runs_sha256": hashlib.sha256((directory / "runs.csv").read_bytes()).hexdigest(),
        "analysis_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seeds": seeds,
        "comparison": "dmab minus ucb, paired by instance and seed",
    }
    (directory / "ablation_manifest.json").write_text(
        json.dumps(analysis_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"pair_wins": wins, "pair_ties": ties, "pair_losses": losses,
            "instance_wins": dmab_better_instances,
            "instance_ties": tied_instances, "instance_losses": ucb_better_instances,
            "median_instance_difference": median(instance_differences),
            "runtime_medians": runtime, "median_dmab_restarts": median(restart_values)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path,
                        default=ROOT / "experiments/results/validation_40_59")
    args = parser.parse_args()
    print(json.dumps(analyze(args.directory.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
