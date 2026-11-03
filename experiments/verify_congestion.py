"""Audit the congestion study: schedules, budgets, hashes and portfolio rules."""

from __future__ import annotations

import json
import math

from experiments.entrega2_common import ROOT, read_rows, sha256
from surgery_optim.instances import load_instance
from surgery_optim.objective import quality


OUTPUT = ROOT / "experiments/results/entrega2_congestion_90_109"
BUDGETS = {"uniform3030": 3030, "dmab3030": 3030, "ucb3030": 3030, "uniform6060": 6060,
           "two_uniform6060": 6060, "fixed_portfolio6060": 6060}


def close(first, second) -> None:
    assert math.isclose(float(first), float(second), abs_tol=1e-9), (first, second)


def main() -> None:
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    for field in ("code_sha256", "instance_sha256"):
        for name, digest in manifest[field].items():
            assert sha256(ROOT / name) == digest, name
    contexts = {load_instance(ROOT / name).instance_id: load_instance(ROOT / name)
                for name in manifest["instance_sha256"]}
    rows = read_rows(OUTPUT / "runs.csv")
    by_key = {(r["instance_id"], int(r["seed"]), r["method"]): r for r in rows}
    pairs = {(r["instance_id"], int(r["seed"])) for r in rows}
    failures = read_rows(OUTPUT / "failures.csv")
    assert len(by_key) == len(rows) == len(pairs) * len(BUDGETS)
    assert len(pairs) + len(failures) == len(contexts) * len(manifest["seeds"])

    for instance, seed in pairs:
        objective = {m: float(by_key[instance, seed, m]["objective"]) for m in BUDGETS}
        for method, budget in BUDGETS.items():
            assert int(by_key[instance, seed, method]["evaluations"]) == budget
        close(objective["fixed_portfolio6060"], min(objective["uniform3030"], objective["dmab3030"]))
        assert objective["two_uniform6060"] <= objective["uniform3030"] + 1e-9
        assert objective["uniform6060"] <= objective["uniform3030"] + 1e-9

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
    report = {"status": "passed", "schedules_replayed": len(verified), "pairs": len(pairs),
              "failed_pairs": len(failures), "source_hashes_match": True}
    (OUTPUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
