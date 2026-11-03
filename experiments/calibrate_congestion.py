"""Task 3a of the Entrega 2 protocol: choose the congestion levers.

Runs the pre-registered 18-cell grid on four development instances, seeds
85-89, and applies the protocol's validity and selection rules:

    python -m experiments.calibrate_congestion --workers 12

Development instances never enter the catalog.
"""

from __future__ import annotations

import argparse
import itertools
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from experiments.entrega2_common import (
    ROOT, SIZES, base_manifest, prepare_output, write_manifest, write_rows,
)
from experiments.generate_congestion import development_document
from surgery_optim.instances import validate_document
from surgery_optim.tabu import TabuConfig, run_tabu


SEEDS = tuple(range(85, 90))
POLICIES = ("uniform", "dmab")
RHO_SURGEONS = (1.0, 0.6, 0.4)
RHO_ROOMS = (1.0, 0.75)
RHO_WAIT = (0.5, 1.0, 2.0)
MINIMUM_FEASIBLE = 0.95
MINIMUM_WAITING = 0.50
FIELDS = ("rho_surgeons", "rho_rooms", "rho_wait", "size", "policy", "seed", "status",
          "error", "objective", "makespan", "blocked", "max_wait", "evaluations",
          "feasible_evaluations", "runtime_seconds", "rules_feasible")


def work(task: tuple[float, float, float, int, str, int]) -> dict:
    rho_surgeons, rho_rooms, rho_wait, size, policy, seed = task
    document = development_document(size, rho_rooms, rho_surgeons, rho_wait)
    context = validate_document(document)
    objectives = document["validation"]["evidence"]["rule_objectives"]
    row = dict.fromkeys(FIELDS, "")
    row.update(rho_surgeons=rho_surgeons, rho_rooms=rho_rooms, rho_wait=rho_wait, size=size,
               policy=policy, seed=seed,
               rules_feasible=all(value is not None for value in objectives.values()))
    try:
        result = run_tabu(context, seed, policy, TabuConfig())
    except (AssertionError, RuntimeError, ValueError) as error:
        row.update(status="failed", error=str(error)[:120])
        return row
    measured = result.final_quality
    row.update(status="ok", objective=measured.objective, makespan=measured.makespan,
               blocked=measured.blocked_minutes, max_wait=measured.max_wait_minutes,
               evaluations=result.evaluations, feasible_evaluations=result.feasible_evaluations,
               runtime_seconds=result.runtime_seconds)
    return row


def summarize_cell(cell: tuple[float, float, float], rows: list[dict]) -> dict:
    done = [row for row in rows if row["status"] == "ok"]
    evaluations = sum(row["evaluations"] for row in done)
    feasible = sum(row["feasible_evaluations"] for row in done)
    feasible_share = feasible / evaluations if evaluations else 0.0
    waiting = sum(row["blocked"] > 0 for row in done) / len(done) if done else 0.0
    rules = all(row["rules_feasible"] for row in rows)
    valid = (rules and len(done) == len(rows) and feasible_share >= MINIMUM_FEASIBLE
             and waiting > MINIMUM_WAITING)
    return {
        "rho_surgeons": cell[0], "rho_rooms": cell[1], "rho_wait": cell[2],
        "rules_feasible": rules, "failed_runs": len(rows) - len(done), "runs": len(rows),
        "feasible_share": feasible_share, "waiting_share": waiting,
        "mean_blocked": float(np.mean([row["blocked"] for row in done])) if done else float("nan"),
        "mean_max_wait": float(np.mean([row["max_wait"] for row in done])) if done else float("nan"),
        "mean_makespan": float(np.mean([row["makespan"] for row in done])) if done else float("nan"),
        "mean_runtime_seconds": float(np.mean([row["runtime_seconds"] for row in done]))
        if done else float("nan"),
        "valid": valid,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_calibracion_congestion_85_89")
    args = parser.parse_args()
    output = prepare_output(args.output)
    cells = list(itertools.product(RHO_SURGEONS, RHO_ROOMS, RHO_WAIT))
    manifest = base_manifest("entrega2-calibracion-v1", Path(__file__),
                             ROOT / "experiments/generate_congestion.py")
    manifest.update({"seeds": SEEDS, "policies": POLICIES, "cells": cells, "sizes": SIZES,
                     "search_config": "TabuConfig() defaults, 3030 evaluations"})
    write_manifest(output, manifest)

    tasks = [(*cell, size, policy, seed) for cell in cells for size in SIZES
             for policy in POLICIES for seed in SEEDS]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(work, task) for task in tasks]
        for done, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if done % 90 == 0:
                print(f"{done}/{len(tasks)}", flush=True)
    rows.sort(key=lambda row: (-row["rho_surgeons"], -row["rho_rooms"], row["rho_wait"],
                               row["size"], row["policy"], row["seed"]))
    write_rows(output / "runs.csv", rows, FIELDS)

    summaries = [summarize_cell(cell, [row for row in rows
                                       if (row["rho_surgeons"], row["rho_rooms"], row["rho_wait"]) == cell])
                 for cell in cells]
    write_rows(output / "celdas.csv", summaries)
    valid = [cell for cell in summaries if cell["valid"]]
    chosen = (min(valid, key=lambda cell: (-cell["rho_surgeons"], -cell["rho_rooms"],
                                           abs(math.log(cell["rho_wait"]))))
              if valid else None)

    lines = ["# Calibración del catálogo de congestión", "",
             "Cuatro instancias de desarrollo, Tabu uniforme y D-MAB, 3.030 evaluaciones, "
             "semillas 85–89. Estas instancias no entran al catálogo.", "",
             "| rho_S | rho_R | rho_W | Reglas factibles | Fallos | Evaluaciones factibles | "
             "Finales con espera | Espera total media | Makespan medio | Válida |",
             "|---:|---:|---:|---|---:|---:|---:|---:|---:|---|"]
    for cell in summaries:
        lines.append(
            f"| {cell['rho_surgeons']:.2f} | {cell['rho_rooms']:.2f} | {cell['rho_wait']:.2f} | "
            f"{'sí' if cell['rules_feasible'] else 'no'} | {cell['failed_runs']}/{cell['runs']} | "
            f"{cell['feasible_share']:.1%} | {cell['waiting_share']:.1%} | "
            f"{cell['mean_blocked']:.2f} | {cell['mean_makespan']:.1f} | "
            f"{'sí' if cell['valid'] else 'no'} |")
    lines += ["", "## Selección", "",
              (f"Celda elegida por la regla del protocolo: `rho_S={chosen['rho_surgeons']}`, "
               f"`rho_R={chosen['rho_rooms']}`, `rho_W={chosen['rho_wait']}`."
               if chosen else "Ninguna celda cumple los criterios del protocolo."), ""]
    (output / "CALIBRACION.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["selected_cell"] = chosen
    manifest["valid_cells"] = len(valid)
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print("\n".join(lines[6:]))


if __name__ == "__main__":
    main()
