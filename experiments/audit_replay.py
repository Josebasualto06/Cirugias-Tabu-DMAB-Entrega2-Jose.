"""Replay one paired seed across all instances and verify strict schedules."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from surgery_optim import TabuConfig, load_instance, run_tabu
from surgery_optim.scheduler import schedule_instance_solution


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=40)
    parser.add_argument("--directory", type=Path,
                        default=ROOT / "experiments/results/validation_40_59")
    args = parser.parse_args()
    directory = args.directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "completed" or args.seed not in manifest["seeds"]:
        raise ValueError("seed must belong to completed validation")
    with (directory / "runs.csv").open(newline="", encoding="utf-8") as stream:
        reference = {(row["instance_id"], int(row["seed"]), row["policy"]): row
                     for row in csv.DictReader(stream)}
    config = TabuConfig.from_manifest(manifest["config"])
    evidence = []
    for path_text in manifest["instance_paths"]:
        context = load_instance(ROOT / path_text)
        for policy in manifest["policies"]:
            result = run_tabu(context, args.seed, policy, config)
            old = reference[context.instance_id, args.seed, policy]
            measured = result.final_quality
            for field, actual in (("initial_objective", result.initial_objective),
                                  ("objective", measured.objective),
                                  ("makespan_minutes", measured.makespan),
                                  ("blocked_minutes", measured.blocked_minutes),
                                  ("max_wait_minutes", measured.max_wait_minutes)):
                if not math.isclose(actual, float(old[field]), abs_tol=1e-9):
                    raise AssertionError((context.instance_id, args.seed, policy, field))
            if result.evaluations != config.evaluation_budget or result.feasible_evaluations != config.evaluation_budget:
                raise AssertionError("budget or feasibility mismatch")
            _, schedule = schedule_instance_solution(context, result.best_solution)
            by_job = {(entry.job_id, entry.operation): entry for entry in schedule}
            slacks = []
            for job in context.jobs:
                first = by_job[job.job_id, 1]
                second = by_job[job.job_id, 2]
                wait = second.start + max(second.transition, second.setup) - first.finish
                slack = job.operations[1].max_wait - wait
                if slack < -1e-9:
                    raise AssertionError("max_wait violated in replay")
                slacks.append(slack)
            evidence.append({
                "instance_id": context.instance_id, "seed": args.seed, "policy": policy,
                "objective_csv": old["objective"],
                "objective_replay": measured.objective,
                "makespan_csv": old["makespan_minutes"],
                "makespan_replay": measured.makespan,
                "blocked_csv": old["blocked_minutes"],
                "blocked_replay": measured.blocked_minutes,
                "evaluations": result.evaluations,
                "schedule_entries": len(schedule),
                "minimum_max_wait_slack_minutes": min(slacks),
                "strict_schedule_validated": True,
            })
        print(f"Replayed {context.instance_id}", flush=True)
    destination = directory / f"replay_seed_{args.seed}.csv"
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(evidence[0]))
        writer.writeheader()
        writer.writerows(evidence)
    (directory / f"replay_seed_{args.seed}_manifest.json").write_text(json.dumps({
        "sample_seed": args.seed,
        "all_instances": True,
        "all_policies": True,
        "replayed_runs": len(evidence),
        "runs_sha256": hashlib.sha256((directory / "runs.csv").read_bytes()).hexdigest(),
        "audit_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "strict_schedule_and_max_wait_recomputed": True,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Replay passed: {len(evidence)} runs; evidence in {destination}")


if __name__ == "__main__":
    main()
