"""Engine diagnostics of the Entrega 2 protocol, standard catalog, seeds 115-119.

Measures repair, reward sparsity and search drift, and checks whether the
archive of 30 solutions changes a trajectory. The variants are built in memory
from src/surgery_optim/tabu.py, which stays unchanged:

    python -m experiments.diagnose_engine --workers 12
"""

from __future__ import annotations

import argparse
import sys
import types
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from statistics import median

import numpy as np

import surgery_optim
from experiments.entrega2_common import (
    ROOT, base_manifest, instance_hashes, prepare_output, standard_paths, write_manifest,
    write_rows,
)
from surgery_optim import bandit, tabu
from surgery_optim.instances import load_instance


SEEDS = tuple(range(115, 120))
POLICIES = ("uniform", "dmab")
SOURCE = (ROOT / "src/surgery_optim/tabu.py").read_text(encoding="utf-8")
ARCHIVE_BLOCK = """        worst = int(np.argmax(fitness))
        positions[worst] = position
        solutions[worst] = local_solution
        fitness[worst] = value
        makespans[worst] = makespan
        best_in_population = int(np.argmin(fitness))
        if fitness[best_in_population] < best_value:
            best_value = float(fitness[best_in_population])
            best_makespan = float(makespans[best_in_population])
            best_solution = copy.deepcopy(solutions[best_in_population])
            local_solution = copy.deepcopy(best_solution)
            local_value = best_value
"""
WITHOUT_ARCHIVE = """        if value < best_value:
            best_value = value
            best_makespan = makespan
            best_solution = copy.deepcopy(local_solution)
"""
REWARD_LINE = "            rewards.append(reward)\n"
CHOICE_LINE = "        chosen = min(admissible or candidates, key=lambda item: (item[0], item[1]))\n"


def variant(name: str, source: str) -> types.ModuleType:
    module = types.ModuleType(f"surgery_optim.{name}")
    module.__package__ = "surgery_optim"
    sys.modules[module.__name__] = module
    exec(compile(source, module.__name__, "exec"), module.__dict__)
    return module


def build_variants() -> tuple[types.ModuleType, types.ModuleType]:
    if ARCHIVE_BLOCK not in SOURCE or REWARD_LINE not in SOURCE or CHOICE_LINE not in SOURCE:
        raise ValueError("tabu.py changed; the diagnostic transforms no longer apply")
    without_archive = variant("tabu_without_archive", SOURCE.replace(ARCHIVE_BLOCK, WITHOUT_ARCHIVE))
    logged = SOURCE.replace(REWARD_LINE, REWARD_LINE + (
        "            CANDIDATES.append((reward > 0, value < best_value))\n"
    )).replace(CHOICE_LINE, CHOICE_LINE + (
        "        BATCHES.append((chosen[0] - old_local, not admissible, old_local - best_value))\n"
    ))
    instrumented = variant("tabu_instrumented", logged)
    instrumented.CANDIDATES, instrumented.BATCHES, instrumented.REWARDS = [], [], []

    class RecordingBandit(bandit.DynamicMultiArmedBandit):
        def update(self, action: str, reward: float) -> bool:
            instrumented.REWARDS.append(reward)
            return super().update(action, reward)

    instrumented.DynamicMultiArmedBandit = RecordingBandit
    return without_archive, instrumented


def same_run(first, second) -> bool:
    return (first.final_quality == second.final_quality
            and first.best_solution == second.best_solution
            and first.trace == second.trace
            and first.repaired_candidates == second.repaired_candidates)


def work(task: tuple[str, int, str]) -> dict:
    path, seed, policy = task
    context = load_instance(path)
    without_archive, instrumented = build_variants()
    original = tabu.run_tabu(context, seed, policy)
    logged = instrumented.run_tabu(context, seed, policy)
    reduced = without_archive.run_tabu(context, seed, policy)
    differences = np.array([row[0] for row in instrumented.BATCHES])
    gaps = [row[2] for row in instrumented.BATCHES]
    improved = [row["evaluations"] for earlier, row in zip(original.trace, original.trace[1:])
                if row["best_objective"] < earlier["best_objective"]]
    return {
        "instance_id": context.instance_id, "seed": seed, "policy": policy,
        "instrumentation_is_neutral": same_run(original, logged),
        "identical_without_archive": same_run(original, reduced),
        "evaluated_candidates": original.evaluations - TABU_POPULATION,
        "repaired_candidates": original.repaired_candidates,
        "proposals_rewarded": len(instrumented.REWARDS),
        "proposals_positive": sum(reward > 0 for reward in instrumented.REWARDS),
        "candidates_locally_better": sum(row[0] for row in instrumented.CANDIDATES),
        "candidates_better_than_best": sum(row[0] and row[1] for row in instrumented.CANDIDATES),
        "batches": len(differences),
        "batches_accepting_worse": int((differences > 1e-9).sum()),
        "batches_without_admissible": sum(row[1] for row in instrumented.BATCHES),
        "gap_first_20_batches": float(np.mean(gaps[:20])),
        "gap_last_50_batches": float(np.mean(gaps[-50:])),
        "last_improvement": improved[-1] if improved else TABU_POPULATION,
    }


TABU_POPULATION = tabu.TabuConfig().population_size


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_diagnostico_115_119")
    args = parser.parse_args()
    output = prepare_output(args.output)
    paths = standard_paths()
    manifest = base_manifest("entrega2-diagnostico-v1", Path(__file__))
    manifest.update({"instance_sha256": instance_hashes(paths), "seeds": SEEDS,
                     "policies": POLICIES, "package_version": surgery_optim.__name__})
    write_manifest(output, manifest)
    tasks = [(str(path), seed, policy) for path in paths for seed in SEEDS for policy in POLICIES]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        rows = [future.result() for future in as_completed(
            [pool.submit(work, task) for task in tasks])]
    rows.sort(key=lambda row: (row["instance_id"], row["seed"], row["policy"]))
    write_rows(output / "runs.csv", rows)

    summary = []
    for policy in POLICIES:
        current = [row for row in rows if row["policy"] == policy]
        total = lambda field: sum(row[field] for row in current)
        summary.append({
            "policy": policy, "runs": len(current),
            "repaired_share": total("repaired_candidates") / total("evaluated_candidates"),
            "proposals": total("proposals_rewarded"),
            "positive_reward_share": (total("proposals_positive") / total("proposals_rewarded")
                                      if total("proposals_rewarded") else float("nan")),
            "locally_better_candidates": total("candidates_locally_better"),
            "better_than_best_candidates": total("candidates_better_than_best"),
            "accepting_worse_share": total("batches_accepting_worse") / total("batches"),
            "batches_without_admissible": total("batches_without_admissible"),
            "mean_gap_first_20": float(np.mean([row["gap_first_20_batches"] for row in current])),
            "mean_gap_last_50": float(np.mean([row["gap_last_50_batches"] for row in current])),
            "median_last_improvement": median(row["last_improvement"] for row in current),
            "identical_without_archive": sum(row["identical_without_archive"] for row in current),
            "neutral_instrumentation": sum(row["instrumentation_is_neutral"] for row in current),
        })
    write_rows(output / "summary.csv", summary)
    lines = ["# Diagnóstico del motor", "",
             "Doce instancias estándar, semillas 115–119, 3.030 evaluaciones. Describe mecanismos "
             "y no compara calidad entre políticas.", "",
             "| Medida | Tabu uniforme | Tabu + D-MAB |", "|---|---:|---:|"]
    uniform, dynamic = summary
    formats = (("Corridas", "runs", "{}"), ("Candidatos reparados", "repaired_share", "{:.1%}"),
               ("Propuestas actualizadas en el bandido", "proposals", "{}"),
               ("Propuestas con recompensa positiva", "positive_reward_share", "{:.1%}"),
               ("Candidatos mejores que el estado local", "locally_better_candidates", "{}"),
               ("De ellos, mejores que el mejor global", "better_than_best_candidates", "{}"),
               ("Lotes que aceptan un empeoramiento", "accepting_worse_share", "{:.1%}"),
               ("Lotes sin candidato admisible", "batches_without_admissible", "{}"),
               ("Distancia local–mejor, primeros 20 lotes", "mean_gap_first_20", "{:.1f}"),
               ("Distancia local–mejor, últimos 50 lotes", "mean_gap_last_50", "{:.1f}"),
               ("Última mejora, evaluación mediana", "median_last_improvement", "{:.0f}"),
               ("Corridas idénticas sin archivo", "identical_without_archive", "{}"),
               ("Corridas idénticas con instrumentación", "neutral_instrumentation", "{}"))
    for label, field, pattern in formats:
        lines.append(f"| {label} | {pattern.format(uniform[field])} | {pattern.format(dynamic[field])} |")
    lines.append("")
    (output / "DIAGNOSTICO.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
