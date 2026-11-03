"""Calibrate tabu memory, UCB scaling C and Page–Hinkley lambda.

Uses only the exploratory seeds 0–5, never the validation seeds, so the
validation study (seeds 40–59) stays independent of the tuning:

    python -m experiments.calibrate --workers 2

Writes ``runs.csv`` (resumable) and ``CALIBRATION.md`` to
``experiments/results/calibration_0_5/``.
"""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from surgery_optim.instances import load_instance
from surgery_optim.tabu import TabuConfig, run_tabu


ROOT = Path(__file__).resolve().parents[1]
SIZES = (15, 20, 25, 30)
EXPLORATION = (0.1, 0.02)
PH_LAMBDA = (1.0, 10.0)
FIELDS = ("variant", "policy", "memory", "exploration", "ph_lambda", "instance_id",
          "seed", "objective", "makespan_minutes", "dmab_restarts", "repaired_candidates",
          *(f"evaluated_{move}" for move in ("swap", "insert", "room_1", "room_2", "room_pair")))


def variants() -> list[dict]:
    """Tabu memory first (uniform policy), then C and lambda for the bandits.

    A first pass ran the bandits with attribute memory; attribute memory
    made uniform Tabu clearly worse, so the bandit grid was rerun with the
    Entrega 1 solution memory. The completed attribute variants stay in
    ``runs.csv`` as evidence.
    """
    rows = [{"policy": "uniform", "memory": memory, "exploration": 1.0, "ph_lambda": 0.35}
            for memory in ("solution", "attribute")]
    rows.append({"policy": "dmab", "memory": "solution", "exploration": 1.0,
                 "ph_lambda": 0.35})
    rows += [{"policy": "dmab", "memory": "solution", "exploration": c, "ph_lambda": lam}
             for c in EXPLORATION for lam in PH_LAMBDA]
    rows += [{"policy": "ucb", "memory": "solution", "exploration": c, "ph_lambda": 0.35}
             for c in EXPLORATION]
    for row in rows:
        row["variant"] = (f"{row['policy']}|{row['memory']}|C={row['exploration']}"
                          f"|lambda={row['ph_lambda']}")
    return rows


def work(task: tuple[dict, str, int]) -> dict:
    variant, path, seed = task
    context = load_instance(path)
    config = TabuConfig(exploration=variant["exploration"], ph_lambda=variant["ph_lambda"],
                        tabu_memory=variant["memory"])
    result = run_tabu(context, seed, variant["policy"], config)
    return {**variant, "instance_id": context.instance_id, "seed": seed,
            "objective": result.final_quality.objective,
            "makespan_minutes": result.final_quality.makespan,
            "dmab_restarts": result.dmab_restarts,
            "repaired_candidates": result.repaired_candidates,
            **{f"evaluated_{move}": count for move, count in result.evaluated_choices.items()}}


def report(output: Path) -> None:
    with (output / "runs.csv").open(newline="", encoding="utf-8") as stream:
        runs = list(csv.DictReader(stream))
    reference = {(row["instance_id"], row["seed"]): float(row["objective"]) for row in runs
                 if row["variant"].startswith("uniform|solution")}
    lines = ["# Calibración en semillas exploratorias 0–5", "",
             "Diferencia emparejada contra Tabu uniforme con memoria de soluciones "
             "(configuración de la Entrega 1); negativo es mejor. 12 instancias × 6 semillas.",
             "", "| Variante | Media dif. | Mediana de medianas por instancia | Gana / empata / "
             "pierde | Reinicios PH (mediana) | Reparados (mediana) |",
             "|---|---:|---:|---:|---:|---:|"]
    for variant in dict.fromkeys(row["variant"] for row in runs):
        rows = [row for row in runs if row["variant"] == variant]
        diffs = np.array([float(row["objective"]) - reference[row["instance_id"], row["seed"]]
                          for row in rows])
        per_instance = [np.median([float(row["objective"])
                                   - reference[row["instance_id"], row["seed"]]
                                   for row in rows if row["instance_id"] == instance])
                        for instance in dict.fromkeys(row["instance_id"] for row in rows)]
        lines.append(
            f"| `{variant}` | {diffs.mean():+.3f} | {np.median(per_instance):+.3f} | "
            f"{int((diffs < -0.25).sum())} / {int((abs(diffs) <= 0.25).sum())} / "
            f"{int((diffs > 0.25).sum())} | "
            f"{np.median([float(row['dmab_restarts']) for row in rows]):.0f} | "
            f"{np.median([float(row['repaired_candidates']) for row in rows]):.0f} |")
    lines += ["", "Gana/pierde usan el umbral práctico de 0,25 min de la Entrega 1.", "",
              "## Decisión", "",
              "Regla fijada antes de validar: se usa la memoria tabú y los parámetros "
              "(C, λ) de la variante D-MAB con menor diferencia media; UCB1 usa el mismo C "
              "para que la ablación solo quite Page–Hinkley.", "",
              "* **Memoria tabú:** la memoria por atributo empeora a Tabu uniforme "
              "(+3,5 min de media) y a todas las variantes D-MAB; se mantiene la memoria "
              "de soluciones.",
              "* **Escala C:** reducir C para que el bandit explote las recompensas "
              "**empeora** el resultado (C = 0,02: +2,0 a +2,4 min). Con C = 1 el "
              "controlador elige casi por turnos, pero esa diversidad de movimientos es "
              "valiosa: la recompensa de mejora inmediata no predice bien qué movimiento "
              "conviene seguir usando.",
              "* **Page–Hinkley:** con C = 0,1, los reinicios (λ = 1, mediana 12 por "
              "corrida) ayudan frente a no reiniciar (λ = 10 o UCB1), porque devuelven "
              "exploración al controlador.",
              "* **Elegida:** C = 0,1 y λ = 1,0 (media −0,22 min frente a −0,14 min de "
              "C = 1, λ = 0,35). La diferencia entre ambas es menor que la variación entre "
              "semillas, así que la calibración no anticipa una ventaja clara de D-MAB.",
              "* **Movimientos reparados:** cerca de 900 de 3.000 candidatos (≈30 %) "
              "salen del decodificador distintos de la propuesta, en todas las políticas.",
              ""]
    (output / "CALIBRATION.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seeds", type=int, default=6)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/calibration_0_5")
    args = parser.parse_args()
    if args.seeds > 20:
        parser.error("calibration must stay within exploratory seeds 0–19")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run_path = output / "runs.csv"
    done = set()
    if run_path.exists():
        with run_path.open(newline="", encoding="utf-8") as stream:
            done = {(r["variant"], r["instance_id"], r["seed"]) for r in csv.DictReader(stream)}
    else:
        with run_path.open("w", newline="", encoding="utf-8") as stream:
            csv.DictWriter(stream, fieldnames=FIELDS).writeheader()
    paths = [ROOT / "instances/standard" / f"HOSP-STD-{size}-{replica:02d}.yaml"
             for size in SIZES for replica in (1, 2, 3)]
    tasks = [(variant, str(path), seed) for variant in variants() for path in paths
             for seed in range(args.seeds)
             if (variant["variant"], path.stem, str(seed)) not in done]
    with ProcessPoolExecutor(args.workers) as pool, \
            run_path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        for index, row in enumerate(pool.map(work, tasks, chunksize=4), 1):
            writer.writerow(row)
            stream.flush()
            if index % 100 == 0:
                print(f"{index}/{len(tasks)}", flush=True)
    report(output)
    print(f"Calibration written to {output / 'CALIBRATION.md'}")


if __name__ == "__main__":
    main()
