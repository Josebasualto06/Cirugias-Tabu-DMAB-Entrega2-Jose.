"""Post-hoc diagnosis of why the Page-Hinkley restart did not help under congestion.

This is a diagnosis, not a new comparison of methods. It tests no hypothesis,
changes no decision of C1-C4 or E1 and leaves src/ untouched:

1. replays the archived uniform and D-MAB runs of seeds 90-109 with observers
   in memory; each run must reproduce its archived objective and restarts;
2. feeds the same bandit with rewards drawn from distributions that never
   change (a bandit-only bench: no schedule is built and no search seed is
   used), to count false alarms of the detector;
3. re-times the archived final schedules with the room rule of the course
   repository simulator, which keeps the anesthesia room until surgery ends;
4. summarizes the archived time overhead of UCB1 by instance size.

    python -X utf8 experiments/scripts/diagnostico_revision.py --workers 14

Source hashes are taken on LF-normalized bytes, so they also hold in a clone.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from surgery_optim import tabu  # noqa: E402
from surgery_optim.bandit import MOVES, DynamicMultiArmedBandit  # noqa: E402
from surgery_optim.instances import load_instance  # noqa: E402
from surgery_optim.scheduler import schedule_instance_solution  # noqa: E402


RESULTS = ROOT / "experiments/results"
OUTPUT = RESULTS / "entrega3_diagnostico_revision"
FAMILY = RESULTS / "entrega2_congestion_90_109"
CONFIRMATION = RESULTS / "entrega3_confirmacion_ucb1"
SOURCES = (FAMILY / "runs.csv", FAMILY / "solutions.jsonl",
           CONFIRMATION / "runs.csv", CONFIRMATION / "solutions.jsonl")
INITIAL, BUDGET, BATCH = 30, 3030, 15
PHASES = 3
BENCH_SEED = 20261122
# (name, all arms share one distribution, restart, threshold)
BENCH = (
    ("identical_arms", True, True, 1.0),
    ("different_arms", False, True, 1.0),
    ("different_arms_lambda_10", False, True, 10.0),
    ("different_arms_without_restart", False, False, 1.0),
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


def observe(saved: dict) -> dict:
    """Replay one archived run while recording proposals, values and restarts."""
    policy = saved["method"].removesuffix("3030")
    context = load_instance(ROOT / f"instances/congestion/{saved['instance_id']}.yaml")
    original = tabu.neighbor, tabu.quality, tabu.DynamicMultiArmedBandit
    proposals, evaluated, values, leader = [], [], {}, []

    def neighbor(solution, instance, *args, **kwargs):
        made = original[0](solution, instance, *args, **kwargs)
        proposals.append([made[2], tabu.signature(solution, instance), None])
        return made

    def quality(instance, solution):
        measured = original[1](instance, solution)
        values.setdefault(tabu.signature(solution, instance), measured.objective)
        evaluated.append(measured.objective)
        if proposals and proposals[-1][2] is None:
            proposals[-1][2] = len(evaluated) - 1
        return measured

    class Observed(DynamicMultiArmedBandit):
        def update(self, action, reward):
            means = dict(self.means)
            means[action] += (reward - means[action]) / (self.counts[action] + 1)
            fired = super().update(action, reward)
            if fired:
                leader.append(means[action] >= max(means.values()) - 1e-12)
            return fired

    tabu.neighbor, tabu.quality, tabu.DynamicMultiArmedBandit = neighbor, quality, Observed
    try:
        result = tabu.run_tabu(context, int(saved["seed"]), policy)
    finally:
        tabu.neighbor, tabu.quality, tabu.DynamicMultiArmedBandit = original
    key = (saved["instance_id"], saved["seed"], policy)
    if not math.isclose(result.final_quality.objective, float(saved["objective"]), abs_tol=1e-9):
        raise AssertionError(("objective", key))
    if result.dmab_restarts != int(saved["dmab_restarts"]) or len(evaluated) != BUDGET + 1:
        raise AssertionError(("restarts or evaluations", key))
    evaluated.pop()  # final revalidation

    initial = incumbent = min(evaluated[:INITIAL])
    best_before = []
    for start in range(INITIAL, BUDGET, BATCH):
        batch = evaluated[start:start + BATCH]
        best_before += [incumbent] * len(batch)
        incumbent = min(incumbent, *batch)

    # proposals, positive rewards, improvements of the global best
    table = np.zeros((PHASES, len(MOVES), 3), dtype=np.int64)
    rewards = [[] for _ in MOVES]
    done = 0
    for move, local_key, index in proposals:
        arm = MOVES.index(move)
        phase = min(PHASES - 1, done * PHASES // (BUDGET - INITIAL))
        table[phase, arm, 0] += 1
        reward = 0.0  # a duplicate of the batch
        if index is not None:
            value = evaluated[index]
            reward = min(1.0, max(0.0, values[local_key] - value) / max(1.0, 0.02 * initial))
            table[phase, arm, 1] += reward > 0
            table[phase, arm, 2] += reward > 0 and value < best_before[index - INITIAL]
            done += 1
        if policy == "uniform":
            rewards[arm].append(reward)
    return {
        "instance_id": saved["instance_id"], "seed": int(saved["seed"]), "policy": policy,
        "table": table, "rewards": [np.array(values_) for values_ in rewards],
        "proposals": len(proposals), "restarts": result.dmab_restarts,
        "restarts_by_leader": int(sum(leader)),
    }


def bench(task: tuple) -> list[dict]:
    """Run the bandit alone on stationary rewards of one instance."""
    number, instance, pools, horizons = task
    common = np.concatenate(pools)
    found = []
    for config, (name, identical, dynamic, threshold) in enumerate(BENCH):
        sources = [common] * len(MOVES) if identical else pools
        expected = [float(source.mean()) for source in sources]
        for run, steps in enumerate(horizons):
            rng = np.random.default_rng([BENCH_SEED, number, config, run])
            draws = rng.random(steps)
            bandit = DynamicMultiArmedBandit(
                delta=0.01, threshold=threshold, exploration=0.1, dynamic=dynamic)
            obtained = 0.0
            for draw in draws:
                move = bandit.select()
                arm = MOVES.index(move)
                source = sources[arm]
                bandit.update(move, float(source[int(draw * len(source))]))
                obtained += expected[arm]
            found.append({"instance_id": instance, "configuration": name, "run": run,
                          "steps": steps, "restarts": bandit.restarts,
                          "expected_reward": obtained / steps,
                          "best_arm_reward": max(expected),
                          "uniform_reward": float(np.mean(expected))})
    return found


def room_rule() -> list[dict]:
    """Re-time final schedules holding the anesthesia room until surgery ends."""
    contexts, found = {}, []
    for folder in (FAMILY, CONFIRMATION):
        with (folder / "solutions.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                saved = json.loads(line)
                name = saved["instance_id"]
                if name not in contexts:
                    contexts[name] = load_instance(ROOT / f"instances/congestion/{name}.yaml")
                context = contexts[name]
                rooms = {int(job): {int(op): room for op, room in pair.items()}
                         for job, pair in saved["solution"]["room_assignment"].items()}
                order = saved["solution"]["job_sequence_base"]
                # The project rule must accept every archived schedule.
                schedule_instance_solution(
                    context, {"job_sequence_base": order, "room_assignment": rooms})
                room_free = dict.fromkeys(context.rooms, 0.0)
                staff_free = defaultdict(float)
                jobs = {job.job_id: job for job in context.jobs}
                feasible = True
                for job_id in order:
                    first, second = jobs[job_id].operations
                    room_1, room_2 = rooms[job_id][1], rooms[job_id][2]
                    anesthetist = min(first.eligible_personnel, key=lambda p: (staff_free[p], p))
                    surgeon = min(second.eligible_personnel, key=lambda p: (staff_free[p], p))
                    start = max(room_free[room_1], staff_free[anesthetist])
                    ready = (start + max(first.setup, first.transition) + first.duration
                             + first.cleanup)
                    surgery = (max(ready, room_free[room_2], staff_free[surgeon])
                               + max(second.setup, second.transition))
                    if surgery - ready > second.max_wait + 1e-9:
                        feasible = False
                        break
                    finish = surgery + second.duration + second.cleanup
                    room_free[room_1] = room_free[room_2] = finish  # repository rule
                    staff_free[anesthetist], staff_free[surgeon] = surgery, finish
                found.append({"study": folder.name, "instance_id": name, "seed": saved["seed"],
                              "method": saved["method"],
                              "cross_room_share": float(np.mean(
                                  [pair[1] != pair[2] for pair in rooms.values()])),
                              "feasible_with_repository_rule": int(feasible)})
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if (args.output / "manifest.json").exists():
        raise SystemExit(f"refusing to overwrite a completed diagnosis: {args.output}")

    archived = read(FAMILY / "runs.csv")
    tasks = [row for row in archived if row["method"] in ("uniform3030", "dmab3030")]
    observed = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for count, item in enumerate(pool.map(observe, tasks, chunksize=2), 1):
            observed.append(item)
            if count % 200 == 0:
                print(f"{count}/{len(tasks)} corridas", flush=True)

        instances = sorted({item["instance_id"] for item in observed})
        bench_tasks = []
        for number, instance in enumerate(instances):
            mine = [item for item in observed if item["instance_id"] == instance]
            uniform = [item for item in mine if item["policy"] == "uniform"]
            pools = [np.concatenate([item["rewards"][arm] for item in uniform])
                     for arm in range(len(MOVES))]
            horizons = [item["proposals"] for item in sorted(mine, key=lambda item: item["seed"])
                        if item["policy"] == "dmab"]
            bench_tasks.append((number, instance, pools, horizons))
        simulated = [row for rows in pool.map(bench, bench_tasks) for row in rows]

    operators = []
    for instance in instances:
        for policy in ("uniform", "dmab"):
            total = sum(item["table"] for item in observed
                        if item["instance_id"] == instance and item["policy"] == policy)
            for phase in range(PHASES):
                for arm, move in enumerate(MOVES):
                    proposed, rewarded, improved = (int(x) for x in total[phase, arm])
                    operators.append({"instance_id": instance, "policy": policy,
                                      "phase": phase + 1, "move": move, "proposals": proposed,
                                      "rewarded": rewarded, "rewarded_global_best": improved})
    detector = [{key: item[key] for key in
                 ("instance_id", "seed", "proposals", "restarts", "restarts_by_leader")}
                for item in observed if item["policy"] == "dmab"]
    detector.sort(key=lambda row: (row["instance_id"], row["seed"]))
    rules = room_rule()

    summary: list[dict] = []

    def add(measure: str, item: str, value: float) -> None:
        summary.append({"measure": measure, "item": item, "value": float(value)})

    def total(policy: str, field: str, **match) -> int:
        return sum(row[field] for row in operators if row["policy"] == policy
                   and all(row[key] == value for key, value in match.items()))

    for policy in ("uniform", "dmab"):
        add("rewarded_share", policy, 100 * total(policy, "rewarded") / total(policy, "proposals"))
        add("rewarded_that_improve_best", policy,
            100 * total(policy, "rewarded_global_best") / total(policy, "rewarded"))
        for phase in range(1, PHASES + 1):
            proposed = total(policy, "proposals", phase=phase)
            add("rewarded_share_by_phase", f"{policy}:{phase}",
                100 * total(policy, "rewarded", phase=phase) / proposed)
            add("global_improvements_per_1000_by_phase", f"{policy}:{phase}",
                1000 * total(policy, "rewarded_global_best", phase=phase) / proposed)
            for move in MOVES:
                proposed = total(policy, "proposals", phase=phase, move=move)
                add("rewarded_share_by_phase_and_move", f"{policy}:{phase}:{move}",
                    100 * total(policy, "rewarded", phase=phase, move=move) / proposed)

    leaders = defaultdict(list)
    for instance in instances:
        for phase in range(1, PHASES + 1):
            current = [row for row in operators if row["instance_id"] == instance
                       and row["policy"] == "uniform" and row["phase"] == phase]
            leaders[instance].append(
                max(current, key=lambda row: row["rewarded"] / row["proposals"])["move"])
    add("instances_with_same_best_move_in_all_phases", "uniform",
        sum(len(set(found)) == 1 for found in leaders.values()))
    add("instances_with_room_1_best_in_all_phases", "uniform",
        sum(set(found) == {"room_1"} for found in leaders.values()))

    add("median_restarts", "dmab", np.median([row["restarts"] for row in detector]))
    add("restarts_by_leader_share", "dmab", 100 * sum(row["restarts_by_leader"] for row in detector)
        / sum(row["restarts"] for row in detector))
    for name, *_ in BENCH:
        current = [row for row in simulated if row["configuration"] == name]
        add("stationary_median_restarts", name, np.median([row["restarts"] for row in current]))
        obtained, uniform, best = (np.mean([row[key] for row in current]) for key in
                                   ("expected_reward", "uniform_reward", "best_arm_reward"))
        if best - uniform > 1e-12:
            add("stationary_share_of_possible_gain", name,
                100 * (obtained - uniform) / (best - uniform))

    add("final_schedules", "all", len(rules))
    add("infeasible_with_repository_rule", "all",
        100 * np.mean([1 - row["feasible_with_repository_rule"] for row in rules]))
    add("cross_room_share", "all", 100 * np.mean([row["cross_room_share"] for row in rules]))

    seconds = {(row["instance_id"], row["seed"], row["method"]): float(row["runtime_seconds"])
               for row in archived}
    for size in (15, 20, 25, 30):
        ratios = [seconds[i, s, m] / seconds[i, s, "uniform3030"] for i, s, m in seconds
                  if m == "ucb3030" and f"-{size}-" in i]
        add("ucb_time_overhead_by_size", str(size), 100 * (np.median(ratios) - 1))

    args.output.mkdir(parents=True, exist_ok=True)
    write(args.output / "operators.csv", operators)
    write(args.output / "detector.csv", detector)
    write(args.output / "stationary_bench.csv", simulated)
    write(args.output / "room_rule.csv", rules)
    write(args.output / "summary.csv", summary)
    lines = [
        "# Diagnóstico posterior del reinicio y del modelo", "",
        "**No estaba pre-registrado.** No prueba hipótesis ni cambia las decisiones de C1–C4 o E1.",
        "",
        "- Las corridas de Tabu uniforme y D-MAB de las semillas 90–109 se repitieron con "
        "observadores; todas reprodujeron su valor archivado.",
        "- El banco estacionario solo alimenta el bandido. Sortea recompensas de la misma "
        "instancia, observadas bajo selección uniforme, que no cambian durante la corrida. "
        "`identical_arms` da además la misma distribución a los cinco brazos.",
        "- `rewarded_that_improve_best`: recompensadas que mejoran el mejor global previo al lote.",
        "- La regla del simulador docente retiene la sala de anestesia hasta el final de la "
        "cirugía. La del proyecto sigue la formulación de clase: hasta que empieza la cirugía.",
        "- Recalcular calendarios con otra regla no dice qué habría encontrado una búsqueda con "
        "esa regla.", "",
        "| Medida | Elemento | Valor |", "|---|---|---:|",
    ]
    lines += [f"| {row['measure']} | {row['item']} | {row['value']:.3f} |" for row in summary]
    (args.output / "DIAGNOSTICO.md").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                                newline="\n")
    manifest = {
        "status": "completed", "kind": "post-hoc diagnosis, no hypothesis tested",
        "replayed_runs": len(observed), "mismatches": 0, "bench_seed": BENCH_SEED,
        "bench": [dict(zip(("name", "identical", "restart", "lambda"), item)) for item in BENCH],
        "hash_convention": "sha256 of LF-normalized bytes",
        "sources_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path) for path in SOURCES},
        "code_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path)
                        for path in sorted((ROOT / "src/surgery_optim").rglob("*.py"))},
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "script_sha256": sha256_lf(Path(__file__)),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Diagnóstico completo: {args.output}")


if __name__ == "__main__":
    main()
