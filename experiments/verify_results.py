"""Audit a completed study without rerunning the optimization algorithms."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def audit(directory: Path) -> dict[str, int]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    for name, expected in manifest["instance_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    for name, expected in manifest["code_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name

    runs = rows(directory / "runs.csv")
    baselines = rows(directory / "baselines.csv")
    summary = rows(directory / "summary.csv")
    paired = rows(directory / "paired.csv")
    instances = set(manifest["instance_digests"])
    seeds = manifest["seeds"]
    policies = set(manifest["policies"])
    budget = int(manifest["config"]["evaluation_budget"])
    expected_keys = {(instance, seed, policy)
                     for instance in instances for seed in seeds for policy in policies}
    actual_keys = {(row["instance_id"], int(row["seed"]), row["policy"]) for row in runs}
    assert actual_keys == expected_keys
    assert len(runs) == len(expected_keys)
    assert len(baselines) == len(instances) * 3
    assert len(summary) == len(instances) * len(policies)
    assert len(paired) == len(instances) * 2 * 3

    initial = defaultdict(list)
    grouped = defaultdict(list)
    for row in runs:
        instance, seed, policy = row["instance_id"], int(row["seed"]), row["policy"]
        assert row["instance_digest"] == manifest["instance_digests"][instance]
        assert int(row["evaluations"]) == int(row["feasible_evaluations"]) == budget
        for field in ("objective", "makespan_minutes", "blocked_minutes",
                      "max_wait_minutes", "runtime_seconds", "initial_objective"):
            assert math.isfinite(float(row[field])), (instance, seed, policy, field)
        assert float(row["objective"]) >= float(row["makespan_minutes"])
        assert float(row["blocked_minutes"]) >= float(row["max_wait_minutes"]) >= 0
        if policy != "dmab":
            assert int(row["dmab_restarts"]) == 0
        initial[instance, seed].append(float(row["initial_objective"]))
        grouped[instance, policy].append(row)
    assert all(max(values) - min(values) <= 1e-9 and len(values) == len(policies)
               for values in initial.values())
    assert len(initial) == len(instances) * len(seeds)

    for row in summary:
        values = grouped[row["instance_id"], row["policy"]]
        for field, source in (("median_objective", "objective"),
                              ("median_makespan_minutes", "makespan_minutes"),
                              ("median_blocked_minutes", "blocked_minutes"),
                              ("median_runtime_seconds", "runtime_seconds")):
            assert math.isclose(float(row[field]),
                                float(np.median([float(item[source]) for item in values])),
                                abs_tol=1e-9)
    return {"instances": len(instances), "seeds": len(seeds),
            "runs": len(runs), "baselines": len(baselines),
            "summary_rows": len(summary), "paired_rows": len(paired)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?",
                        default=ROOT / "experiments/results/validation_40_59")
    args = parser.parse_args()
    print(json.dumps(audit(args.directory.resolve()), indent=2))


if __name__ == "__main__":
    main()
