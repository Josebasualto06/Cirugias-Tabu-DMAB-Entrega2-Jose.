"""Audit the Entrega 3 confirmation: schedules, budgets, hashes and the decision.

Recomputes every final schedule with the strict scheduler and repeats the
pre-registered test from runs.csv, without rerunning any search:

    python -m experiments.verify_confirm_ucb1
"""

from __future__ import annotations

import json
import math

import numpy as np
from scipy.stats import wilcoxon

from experiments.entrega2_common import ROOT, read_rows, sha256
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality


OUTPUT = ROOT / "experiments/results/entrega3_confirmacion_ucb1"
BUDGETS = {"uniform3030": 3030, "ucb3030": 3030}
CONSUMED_SEEDS = set(range(0, 120)) | set(range(1_000_060, 1_000_110))


def close(first, second) -> None:
    assert math.isclose(float(first), float(second), abs_tol=1e-9), (first, second)


def main() -> None:
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    for field in ("code_sha256", "instance_sha256"):
        for name, digest in manifest[field].items():
            assert sha256(ROOT / name) == digest, name
    assert sha256(ROOT / manifest["protocol_document"]) == manifest["protocol_sha256"]
    seeds = set(manifest["seeds"])
    assert seeds == set(range(120, 140)) and not seeds & CONSUMED_SEEDS

    contexts = {load_instance(ROOT / name).instance_id: load_instance(ROOT / name)
                for name in manifest["instance_sha256"]}
    rows = read_rows(OUTPUT / "runs.csv")
    by_key = {(r["instance_id"], int(r["seed"]), r["method"]): r for r in rows}
    pairs = {(r["instance_id"], int(r["seed"])) for r in rows}
    failures = read_rows(OUTPUT / "failures.csv")
    assert len(by_key) == len(rows) == len(pairs) * len(BUDGETS)
    assert len(pairs) + len(failures) == len(contexts) * len(seeds)
    assert {seed for _, seed in pairs} <= seeds

    for instance, seed in pairs:
        for method, budget in BUDGETS.items():
            row = by_key[instance, seed, method]
            assert int(row["evaluations"]) == budget
            assert 0 < int(row["feasible_evaluations"]) <= budget
        assert int(by_key[instance, seed, "ucb3030"]["dmab_restarts"]) == 0

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
            measured = quality(contexts[saved["instance_id"]], solution)
            row = by_key[key]
            for metric, value in (("objective", measured.objective), ("makespan", measured.makespan),
                                  ("blocked", measured.blocked_minutes),
                                  ("max_wait", measured.max_wait_minutes)):
                close(row[metric], value)
            verified.add(key)
    assert verified == set(by_key)

    # Repeat the pre-registered test and decision from the audited rows.
    instances = sorted({instance for instance, _ in pairs})
    means = [np.mean([float(by_key[i, s, "ucb3030"]["objective"])
                      - float(by_key[i, s, "uniform3030"]["objective"])
                      for j, s in pairs if j == i]) for i in instances]
    differences = [float(by_key[i, s, "ucb3030"]["objective"])
                   - float(by_key[i, s, "uniform3030"]["objective"]) for i, s in pairs]
    saved = read_rows(OUTPUT / "comparisons.csv")
    assert len(saved) == 1
    comparison = saved[0]
    close(comparison["mean_difference"], np.mean(differences))
    p_value = float(wilcoxon(means, zero_method="zsplit").pvalue)
    close(comparison["wilcoxon_p"], p_value)
    close(comparison["holm_p"], p_value)
    supported = (p_value < 0.05 and float(comparison["ci_high"]) < 0
                 and float(comparison["mean_difference"]) <= -0.25)
    assert supported == manifest["outcome"]["h1c_supported"]

    report = {"status": "passed", "schedules_replayed": len(verified), "pairs": len(pairs),
              "failed_pairs": len(failures), "source_hashes_match": True,
              "decision_recomputed": True, "h1c_supported": supported}
    (OUTPUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
