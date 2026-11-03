"""Independently audit saved schedules, budget accounting and learned decisions."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean

import numpy as np

from experiments.portfolio_search import ContextualAllocator
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments/results/portfolios_60_79"


def read(name):
    with (OUTPUT / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def close(first, second):
    assert math.isclose(float(first), float(second), abs_tol=1e-9), (first, second)


def main():
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    assert manifest["status"] == "completed"
    for field in ("code_sha256", "instance_sha256"):
        for name, digest in manifest[field].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    contexts = {name[:-5]: load_instance(ROOT / "instances/standard" / name)
                for name in manifest["instances"]}
    rows = read("runs.csv")
    by_key = {(r["instance_id"], int(r["seed"]), r["method"]): r for r in rows}
    expected = len(contexts) * len(manifest["seeds"]) * len(manifest["methods"])
    assert len(rows) == len(by_key) == expected == manifest["rows"]
    for instance in contexts:
        for seed in manifest["seeds"]:
            for method in manifest["methods"]:
                row = by_key[instance, seed, method]
                budget = 3030 if method in ("uniform3030", "dmab3030") else 6060
                assert int(row["evaluations"]) == int(row["feasible_evaluations"]) == budget
                assert int(row["uniform_evaluations"]) + int(row["dmab_evaluations"]) == budget
            uniform = float(by_key[instance, seed, "uniform3030"]["objective"])
            dynamic = float(by_key[instance, seed, "dmab3030"]["objective"])
            fixed = by_key[instance, seed, "fixed_portfolio6060"]
            close(fixed["objective"], min(uniform, dynamic))
            for method in ("uniform6060", "two_uniform6060", "fixed_portfolio6060", "learned_protected6060"):
                assert float(by_key[instance, seed, method]["objective"]) <= uniform + 1e-9
            close(by_key[instance, seed, "learned_protected6060"]["floor_objective"], uniform)

    verified = set()
    with (OUTPUT / "solutions.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            saved = json.loads(line)
            key = saved["instance_id"], saved["seed"], saved["method"]
            assert key not in verified
            solution = saved["solution"]
            solution["room_assignment"] = {
                int(job): {int(op): room for op, room in rooms.items()}
                for job, rooms in solution["room_assignment"].items()
            }
            q = quality(contexts[saved["instance_id"]], solution)
            row = by_key[key]
            for metric, value in (("objective", q.objective), ("makespan", q.makespan),
                                  ("blocked", q.blocked_minutes), ("max_wait", q.max_wait_minutes)):
                close(row[metric], value)
            verified.add(key)
    assert verified == set(by_key)

    grouped = defaultdict(list)
    for decision in read("decisions.csv"):
        grouped[decision["instance_id"], int(decision["seed"]), decision["method"]].append(decision)
    assert len(grouped) == len(contexts) * len(manifest["seeds"]) * 2
    for key, decisions in grouped.items():
        result = by_key[key]
        model = ContextualAllocator(manifest["linucb_alpha"])
        used = 3060 if key[2] == "learned_protected6060" else 60
        allocation = [3030, 30] if used == 3060 else [30, 30]
        for step, decision in enumerate(decisions):
            assert int(decision["block"]) == step
            contexts_at_step = [np.array(json.loads(decision[name + "_context"]))
                                for name in ("uniform", "dmab")]
            means, scores = model.scores(contexts_at_step)
            for arm, name in enumerate(("uniform", "dmab")):
                close(decision[name + "_mean"], means[arm])
                close(decision[name + "_score"], scores[arm])
                close(contexts_at_step[arm][2], used / 6060)
            chosen = 0 if decision["arm"] == "uniform" else 1
            assert chosen == (step if step < 2 else int(np.argmax(scores)))
            count = int(decision["block_evaluations"])
            used += count
            allocation[chosen] += count
            assert used == int(decision["evaluations"])
            assert float(decision["after"]) <= float(decision["before"]) + 1e-9
            model.update(chosen, contexts_at_step[chosen], float(decision["reward"]))
        assert used == 6060
        assert allocation == [int(result["uniform_evaluations"]), int(result["dmab_evaluations"])]
        close(decisions[-1]["after"], result["objective"])

    for summary in read("summary.csv"):
        diffs = [float(row["objective"]) - float(by_key[instance, seed, "uniform6060"]["objective"])
                 for (instance, seed, method), row in by_key.items() if method == summary["method"]]
        close(summary["mean_difference_vs_uniform6060"], fmean(diffs))
        assert int(summary["wins"]) == sum(d < -.25 for d in diffs)
        assert int(summary["similar"]) == sum(abs(d) <= .25 for d in diffs)
        assert int(summary["losses"]) == sum(d > .25 for d in diffs)

    report = {
        "status": "passed", "schedules_replayed": len(verified),
        "allocator_runs_replayed": len(grouped),
        "decisions_replayed": sum(len(d) for d in grouped.values()),
        "all_budgets_and_protected_floors_verified": True,
        "source_hashes_match": True,
    }
    (OUTPUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
