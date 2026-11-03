"""Equal-budget comparison of fixed and learned search portfolios.

Protocol: twelve published YAML instances, twenty fresh seeds (60--79),
3030-evaluation reference and 6060-evaluation comparison. All initialization,
warmup and trial evaluations are charged. LinUCB learns only from executed
blocks within a run; no policy is fitted to the held-out final results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from experiments.portfolio_search import FEATURE_NAMES, SearchTrajectory, run_allocation
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality
from surgery_optim.tabu import TabuConfig


ROOT = Path(__file__).resolve().parents[1]
TOTAL_BUDGET = 6060
HALF_BUDGET = 3030
BLOCK = 150
ALPHA = 0.25
SECOND_SEED_OFFSET = 1_000_000
PRACTICAL_THRESHOLD = 0.25
METHODS = (
    "uniform3030", "dmab3030", "uniform6060", "two_uniform6060",
    "fixed_portfolio6060", "learned_free6060", "learned_protected6060",
)
COMPARABLE = METHODS[3:]
LABELS = {
    "uniform3030": "Tabu (3.030)", "dmab3030": "D-MAB (3.030)",
    "uniform6060": "Tabu (6.060)", "two_uniform6060": "Dos reinicios de Tabu",
    "fixed_portfolio6060": "Mejor de Tabu y D-MAB",
    "learned_free6060": "Asignación aprendida",
    "learned_protected6060": "Asignación con respaldo",
}
FIELDS = (
    "instance_id", "size", "seed", "method", "objective", "makespan",
    "blocked", "max_wait", "evaluations", "feasible_evaluations", "runtime_seconds",
    "uniform_evaluations", "dmab_evaluations", "dmab_restarts", "floor_objective",
    "uniform_component_objective", "dmab_component_objective", "second_uniform_objective",
)


def write_csv(path: Path, rows: list[dict], fields=None) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def evaluate_pair(task: tuple[str, int]) -> dict:
    path, seed = task
    context = load_instance(path)
    config = TabuConfig(evaluation_budget=TOTAL_BUDGET)
    rows, solutions, decisions = [], [], []

    def record(method, solution, evaluations, feasible, runtime, u_eval=0, d_eval=0,
               restarts=0, floor=float("nan"), u_component=float("nan"),
               d_component=float("nan"), u_second=float("nan")):
        measured = quality(context, solution)
        rows.append(dict(zip(FIELDS, (
            context.instance_id, len(context.jobs), seed, method, measured.objective,
            measured.makespan, measured.blocked_minutes, measured.max_wait_minutes,
            evaluations, feasible, runtime, u_eval, d_eval, restarts, floor,
            u_component, d_component, u_second,
        ))))
        solutions.append({"instance_id": context.instance_id, "seed": seed,
                          "method": method, "solution": solution})

    started = time.perf_counter()
    uniform = SearchTrajectory(context, seed, "uniform", config)
    uniform.advance(HALF_BUDGET - uniform.spent)
    u_time = time.perf_counter() - started
    u_solution = uniform.best_solution
    u_value = uniform.best
    u_feasible = uniform.feasible
    record("uniform3030", u_solution, HALF_BUDGET, u_feasible, u_time,
           HALF_BUDGET, floor=u_value)
    started_continue = time.perf_counter()
    uniform.advance(TOTAL_BUDGET - uniform.spent)
    record("uniform6060", uniform.best_solution, uniform.spent, uniform.feasible,
           u_time + time.perf_counter() - started_continue, TOTAL_BUDGET, floor=u_value)

    started = time.perf_counter()
    dynamic = SearchTrajectory(context, seed, "dmab", config)
    dynamic.advance(HALF_BUDGET - dynamic.spent)
    d_time = time.perf_counter() - started
    record("dmab3030", dynamic.best_solution, dynamic.spent, dynamic.feasible,
           d_time, 0, HALF_BUDGET, dynamic.bandit.restarts)
    selected = u_solution if u_value <= dynamic.best else dynamic.best_solution
    record("fixed_portfolio6060", selected, TOTAL_BUDGET, u_feasible + dynamic.feasible,
           u_time + d_time, HALF_BUDGET, HALF_BUDGET, dynamic.bandit.restarts,
           u_value, u_value, dynamic.best)

    started = time.perf_counter()
    restart = SearchTrajectory(context, seed + SECOND_SEED_OFFSET, "uniform", config)
    restart.advance(HALF_BUDGET - restart.spent)
    r_time = time.perf_counter() - started
    selected = u_solution if u_value <= restart.best else restart.best_solution
    record("two_uniform6060", selected, TOTAL_BUDGET, u_feasible + restart.feasible,
           u_time + r_time, TOTAL_BUDGET, floor=u_value,
           u_component=u_value, u_second=restart.best)

    for protected in (False, True):
        started = time.perf_counter()
        result = run_allocation(context, seed, TOTAL_BUDGET, protected, BLOCK, ALPHA)
        method = "learned_protected6060" if protected else "learned_free6060"
        record(method, result.best_solution, result.evaluations, result.feasible_evaluations,
               time.perf_counter() - started, result.uniform_evaluations,
               result.dmab_evaluations, result.dmab_restarts, result.floor_objective)
        decisions.extend({"instance_id": context.instance_id, "seed": seed,
                          "method": method, **d} for d in result.decisions)
        if protected:
            assert math.isclose(result.floor_objective, u_value, abs_tol=1e-9)

    for row in rows:
        assert row["evaluations"] == (HALF_BUDGET if row["method"] in METHODS[:2] else TOTAL_BUDGET)
        assert row["uniform_evaluations"] + row["dmab_evaluations"] == row["evaluations"]
        assert row["feasible_evaluations"] == row["evaluations"]
    return {"rows": rows, "solutions": solutions, "decisions": decisions}


def clustered_interval(diffs: dict[str, list[float]]) -> tuple[float, float]:
    """Hierarchical bootstrap: instances, then paired seeds within instance."""
    rng = np.random.default_rng(20261002)
    groups = [np.asarray(diffs[key]) for key in sorted(diffs)]
    means = []
    for _ in range(5000):
        sampled = rng.integers(len(groups), size=len(groups))
        means.append(np.mean([
            np.mean(g[rng.integers(len(g), size=len(g))]) for g in (groups[i] for i in sampled)
        ]))
    return tuple(float(v) for v in np.quantile(means, [.025, .975]))


def summarize(output: Path) -> list[dict]:
    rows = read_csv(output / "runs.csv")
    indexed = {(r["instance_id"], int(r["seed"]), r["method"]): r for r in rows}
    keys = sorted({(r["instance_id"], int(r["seed"])) for r in rows})
    assert len(indexed) == len(rows) == len(keys) * len(METHODS)
    records, instance_records = [], []
    for method in METHODS:
        current = [indexed[i, s, method] for i, s in keys]
        grouped = {}
        differences = []
        for instance, seed in keys:
            delta = float(indexed[instance, seed, method]["objective"]) - float(indexed[instance, seed, "uniform6060"]["objective"])
            grouped.setdefault(instance, []).append(delta)
            differences.append(delta)
        low, high = clustered_interval(grouped)
        instance_means = [np.mean(g) for g in grouped.values()]
        p = (1.0 if np.all(np.abs(instance_means) <= 1e-9) else
             float(wilcoxon(instance_means, zero_method="zsplit").pvalue))
        records.append({
            "method": method, "evaluations": int(current[0]["evaluations"]),
            "mean_difference_vs_uniform6060": float(np.mean(differences)),
            "clustered_ci_low": low, "clustered_ci_high": high,
            "wins": sum(d < -PRACTICAL_THRESHOLD for d in differences),
            "similar": sum(abs(d) <= PRACTICAL_THRESHOLD for d in differences),
            "losses": sum(d > PRACTICAL_THRESHOLD for d in differences),
            "wilcoxon_instance_means_p": p, "holm_p": float("nan"),
            "median_runtime_seconds": float(np.median([float(r["runtime_seconds"]) for r in current])),
            "mean_dmab_budget_fraction": float(np.mean([float(r["dmab_evaluations"]) / float(r["evaluations"]) for r in current])),
        })
        for instance in sorted(grouped):
            group = [r for r in current if r["instance_id"] == instance]
            instance_records.append({
                "instance_id": instance, "method": method,
                "mean_objective": float(np.mean([float(r["objective"]) for r in group])),
                "median_objective": float(np.median([float(r["objective"]) for r in group])),
                "mean_difference_vs_uniform6060": float(np.mean(grouped[instance])),
                "mean_makespan": float(np.mean([float(r["makespan"]) for r in group])),
                "mean_blocked": float(np.mean([float(r["blocked"]) for r in group])),
            })
    chosen = [r for r in records if r["method"] in COMPARABLE]
    ordered = sorted(chosen, key=lambda r: r["wilcoxon_instance_means_p"])
    running = 0.0
    for rank, row in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * row["wilcoxon_instance_means_p"]))
        row["holm_p"] = running
    write_csv(output / "summary.csv", records)
    write_csv(output / "instances_summary.csv", instance_records)

    retrospective = read_csv(ROOT / "experiments/results/validation_40_59/runs.csv")
    old = {(r["instance_id"], int(r["seed"]), r["policy"]): float(r["objective"]) for r in retrospective}
    old_keys = sorted({(r["instance_id"], int(r["seed"])) for r in retrospective})
    gains = [old[i, s, "uniform"] - min(old[i, s, "uniform"], old[i, s, "dmab"]) for i, s in old_keys]
    retrospect = {"pairs": len(gains), "mean_gain_vs_uniform3030": float(np.mean(gains)),
                  "material_improvements": sum(g > PRACTICAL_THRESHOLD for g in gains),
                  "total_evaluations": TOTAL_BUDGET}
    (output / "retrospective.json").write_text(json.dumps(retrospect, indent=2) + "\n")

    # Evaluate the protected guarantees and the added value beyond two restarts.
    supplemental = []
    for method, reference in (("fixed_portfolio6060", "uniform3030"),
                              ("learned_protected6060", "uniform3030"),
                              ("fixed_portfolio6060", "two_uniform6060"),
                              ("learned_free6060", "fixed_portfolio6060"),
                              ("learned_protected6060", "fixed_portfolio6060")):
        delta = [float(indexed[i, s, method]["objective"]) - float(indexed[i, s, reference]["objective"]) for i, s in keys]
        if reference == "uniform3030":
            assert max(delta) <= 1e-9
        supplemental.append({"method": method, "reference": reference,
                             "mean_difference": float(np.mean(delta)),
                             "wins": sum(d < -PRACTICAL_THRESHOLD for d in delta),
                             "similar": sum(abs(d) <= PRACTICAL_THRESHOLD for d in delta),
                             "losses": sum(d > PRACTICAL_THRESHOLD for d in delta)})
    write_csv(output / "supplemental.csv", supplemental)

    lines = ["# Comparación de carteras y asignación aprendida", "",
             "Doce instancias YAML oficiales, veinte semillas nuevas 60–79 y siete resultados por pareja. "
             "El objetivo conserva makespan y espera. Menor es mejor; la diferencia es método menos Tabu con 6.060 evaluaciones.", "",
             "## Presupuesto comparable", "",
             "| Método | Evaluaciones | Diferencia media | IC 95 % agrupado | Mejora / similar / empeora | p Holm |",
             "|---|---:|---:|---|---|---:|"]
    for r in records:
        if r["method"] in METHODS[:2]:
            continue
        adjusted = "—" if math.isnan(r["holm_p"]) else f"{r['holm_p']:.3f}"
        lines.append(f"| {LABELS[r['method']]} | {r['evaluations']} | {r['mean_difference_vs_uniform6060']:+.3f} | "
                     f"[{r['clustered_ci_low']:+.3f}, {r['clustered_ci_high']:+.3f}] | "
                     f"{r['wins']} / {r['similar']} / {r['losses']} | {adjusted} |")
    lines += ["", "Los intervalos remuestrean instancias y semillas emparejadas dentro de instancia. "
              "Wilcoxon usa doce diferencias medias por instancia; Holm corrige las cuatro comparaciones "
              "de igual presupuesto. Los conteos usan un umbral práctico de 0,25 del objetivo.", "",
              "## Respaldo y comparaciones adicionales", "",
              "| Método | Referencia | Diferencia media | Mejora / similar / empeora |",
              "|---|---|---:|---|"]
    for r in supplemental:
        lines.append(f"| {LABELS[r['method']]} | {LABELS[r['reference']]} | {r['mean_difference']:+.3f} | "
                     f"{r['wins']} / {r['similar']} / {r['losses']} |")
    lines += ["", "## Qué aprende el controlador", "",
              "LinUCB elige qué trayectoria recibe el próximo bloque de 150 evaluaciones. "
              "Cada trayectoria conserva solución local, archivo, memoria tabú y su propio generador aleatorio. "
              "Sus diez entradas describen presupuesto, progreso, distancia al mejor, estancamiento y espera. "
              "La recompensa es la mejora del mejor global por bloque, normalizada al 2 % del objetivo inicial "
              "y limitada a [0,1]. Se observa únicamente el bloque realmente ejecutado.", "",
              "La variante con respaldo termina primero 3.030 evaluaciones de Tabu uniforme. "
              "Conserva ese resultado y emplea el resto del presupuesto en los dos caminos. "
              "La garantía es frente a esa ejecución de 3.030, no frente a Tabu de 6.060. "
              "Las dos inicializaciones y los bloques de prueba se cuentan en las 6.060 evaluaciones.", "",
              "## Límites", "",
              "Las doce instancias ya se conocían al decidir la arquitectura: nuevas semillas no son nuevas instancias. "
              "No se seleccionaron parámetros con las semillas 60–79. El presupuesto protege la comparación "
              "de calidad, pero no iguala tiempo; los tiempos son descriptivos, medidos con tareas concurrentes. "
              "Dos reinicios de Tabu usan semillas independientes; Tabu+D-MAB comparte la inicialización de su primer camino. "
              "La función objetivo, la reparación y la disponibilidad de personal son las de la versión 2; "
              "la limpieza y las esperas máximas se mantienen. No se demuestra optimalidad.", "",
              "## Reproducibilidad", "",
              "Ejecutar `python -m experiments.compare_portfolios --workers 4`. "
              "`runs.csv` conserva resultados, `solutions.jsonl` conserva soluciones verificables y "
              "`decisions.csv` registra las decisiones online. El manifiesto fija parámetros, hashes y presupuesto.", ""]
    (output / "ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed-start", type=int, default=60)
    parser.add_argument("--seed-count", type=int, default=20)
    parser.add_argument("--sizes", nargs="+", type=int, default=[15, 20, 25, 30])
    parser.add_argument("--replicas", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/results/portfolios_60_79")
    args = parser.parse_args()
    if args.seed_start < 60 or args.seed_count <= 0:
        parser.error("new validation seeds must be at least 60")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    paths = [ROOT / f"instances/standard/HOSP-STD-{size}-{replica:02d}.yaml"
             for size in args.sizes for replica in args.replicas]
    seeds = list(range(args.seed_start, args.seed_start + args.seed_count))
    tracked = list((ROOT / "src/surgery_optim").glob("*.py")) + [Path(__file__), ROOT / "experiments/portfolio_search.py"]
    manifest = {
        "protocol": "portfolio-comparison-v1", "status": "running",
        "source_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "instances": [p.name for p in paths], "seeds": seeds,
        "instance_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "code_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked},
        "search_config": asdict(TabuConfig(evaluation_budget=TOTAL_BUDGET)),
        "methods": METHODS, "budget": TOTAL_BUDGET, "reference_budget": HALF_BUDGET,
        "block_size": BLOCK, "linucb_alpha": ALPHA, "features": FEATURE_NAMES,
        "reward": "clipped improvement of portfolio global best / max(1, 0.02 * initial objective)",
        "learning": "online within each run; no final counterfactual outcomes used by allocator",
        "second_uniform_seed_offset": SECOND_SEED_OFFSET,
        "pairing": "same original seed, shared initial solution for uniform and dmab; no claim of synchronized future random draws",
        "protected_floor": "complete 3030-evaluation uniform trajectory retained",
        "counting": "all objective evaluations, both initializations and every trial block charged",
        "statistics": "hierarchical bootstrap (12 instances, paired seeds), Wilcoxon on per-instance means, Holm across four equal-budget comparisons",
        "practical_threshold": PRACTICAL_THRESHOLD,
        "runtime_environment": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()},
    }
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        for key in ("code_sha256", "instance_sha256", "seeds", "search_config", "methods"):
            if json.loads(json.dumps(previous[key])) != json.loads(json.dumps(manifest[key])):
                raise ValueError(f"cannot resume changed protocol: {key}")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    existing = read_csv(output / "runs.csv")
    counts = {}
    for row in existing:
        key = row["instance_id"], int(row["seed"])
        counts[key] = counts.get(key, 0) + 1
    if any(count != len(METHODS) for count in counts.values()):
        raise ValueError("incomplete saved pair; start a new output directory")
    tasks = [(str(p), seed) for p in paths for seed in seeds if (p.stem, seed) not in counts]
    with (output / "runs.csv").open("a", newline="", encoding="utf-8") as runs, \
         (output / "solutions.jsonl").open("a", encoding="utf-8") as solutions, \
         (output / "decisions.csv").open("a", newline="", encoding="utf-8") as decisions:
        writer = csv.DictWriter(runs, fieldnames=FIELDS)
        if not existing:
            writer.writeheader()
        decision_writer = None
        decision_has_header = (output / "decisions.csv").stat().st_size > 0
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(evaluate_pair, t) for t in tasks]
            for done, future in enumerate(as_completed(futures), 1):
                result = future.result()
                writer.writerows(result["rows"])
                for row in result["solutions"]:
                    solutions.write(json.dumps(row, ensure_ascii=False) + "\n")
                for row in result["decisions"]:
                    if decision_writer is None:
                        decision_writer = csv.DictWriter(decisions, fieldnames=tuple(row))
                        if not decision_has_header:
                            decision_writer.writeheader()
                    decision_writer.writerow(row)
                runs.flush(); solutions.flush(); decisions.flush()
                if done % 5 == 0 or done == len(futures):
                    print(f"{done}/{len(futures)} pares completados", flush=True)
    summary = summarize(output)
    manifest["status"] = "completed"
    manifest["pairs"] = len(paths) * len(seeds)
    manifest["rows"] = len(paths) * len(seeds) * len(METHODS)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
