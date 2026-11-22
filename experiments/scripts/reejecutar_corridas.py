"""Replay the archived 3,030-evaluation congestion runs to record what they did not store.

This is an audit, not a new experiment. It uses no new seed, method or
parameter. Every run of entrega2_congestion_90_109 and entrega3_confirmacion_ucb1
with 3,030 evaluations is executed again and must reproduce its archived
objective, components, repairs and restarts; otherwise nothing is written. The
replay only adds three descriptive measures that runs.csv does not store:

* decoded proposals, including the duplicates that consume no evaluation;
* proposals and evaluations of each move;
* the best objective along the run.

    python -X utf8 experiments/scripts/reejecutar_corridas.py --workers 14

The measures were not pre-registered and do not change any decision. Wall time
is not stored, because it depends on the load of the machine during the replay.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from surgery_optim.bandit import MOVES  # noqa: E402
from surgery_optim.instances import load_instance  # noqa: E402
from surgery_optim.tabu import run_tabu  # noqa: E402


RESULTS = ROOT / "experiments/results"
OUTPUT = RESULTS / "entrega3_revision_reejecucion"
STUDIES = {
    "entrega2_congestion_90_109": ("uniform3030", "dmab3030", "ucb3030"),
    "entrega3_confirmacion_ucb1": ("uniform3030", "ucb3030"),
}
INITIAL = 30
BUDGET = 3030
CHECKPOINTS = tuple(range(INITIAL, BUDGET + 1, 75))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(task: tuple[str, dict]) -> tuple[dict, list[float]]:
    study, saved = task
    instance, seed, method = saved["instance_id"], int(saved["seed"]), saved["method"]
    context = load_instance(ROOT / f"instances/congestion/{instance}.yaml")
    result = run_tabu(context, seed, method.removesuffix("3030"))
    measured = result.final_quality
    for field, value in (
        ("objective", measured.objective), ("makespan", measured.makespan),
        ("blocked", measured.blocked_minutes), ("max_wait", measured.max_wait_minutes),
        ("evaluations", result.evaluations), ("repaired_candidates", result.repaired_candidates),
        ("dmab_restarts", result.dmab_restarts),
    ):
        if not math.isclose(value, float(saved[field]), abs_tol=1e-9):
            raise AssertionError((study, instance, seed, method, field, value, saved[field]))

    reached = {INITIAL: result.initial_objective}
    reached.update({step["evaluations"]: step["best_objective"] for step in result.trace})
    best, last = [], result.initial_objective
    for point in range(INITIAL, BUDGET + 1):
        last = reached.get(point, last)
        if point in CHECKPOINTS:
            best.append(last)
    row = {
        "study": study, "instance_id": instance, "size": int(saved["size"]),
        "seed": seed, "method": method, "objective": measured.objective,
        "batches": len(result.trace),
        "decoded_proposals": sum(result.attempted_choices.values()),
        **{f"proposed_{move}": result.attempted_choices[move] for move in MOVES},
        **{f"evaluated_{move}": result.evaluated_choices[move] for move in MOVES},
    }
    return row, best


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--limit", type=int, help="replay only the first runs (smoke test)")
    args = parser.parse_args()
    if (args.output / "manifest.json").exists():
        raise SystemExit(f"refusing to overwrite a completed replay: {args.output}")

    tasks = []
    for study, methods in STUDIES.items():
        with (RESULTS / study / "runs.csv").open(newline="", encoding="utf-8") as stream:
            tasks += [(study, row) for row in csv.DictReader(stream) if row["method"] in methods]
    tasks = tasks[:args.limit]

    rows, curves = [], defaultdict(list)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for count, future in enumerate(
            as_completed([pool.submit(replay, task) for task in tasks]), 1
        ):
            row, best = future.result()
            rows.append(row)
            curves[row["study"], row["instance_id"], row["method"]].append(best)
            if count % 200 == 0:
                print(f"{count}/{len(tasks)}", flush=True)

    rows.sort(key=lambda r: (r["study"], r["instance_id"], r["seed"], r["method"]))
    mean_curves = [
        {"study": study, "instance_id": instance, "method": method, "evaluations": point,
         "mean_best_objective": math.fsum(run[index] for run in runs) / len(runs)}
        for (study, instance, method), runs in sorted(curves.items())
        for index, point in enumerate(CHECKPOINTS)
    ]
    args.output.mkdir(parents=True, exist_ok=True)
    write_rows(args.output / "runs.csv", rows)
    write_rows(args.output / "convergence.csv", mean_curves)
    manifest = {
        "status": "completed" if args.limit is None else "smoke test",
        "kind": "replay of archived seeds; descriptive, not pre-registered",
        "replayed_runs": len(rows), "mismatches": 0,
        "sources_sha256": {
            f"experiments/results/{study}/runs.csv": sha256(RESULTS / study / "runs.csv")
            for study in STUDIES
        },
        "code_sha256": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in sorted((ROOT / "src/surgery_optim").rglob("*.py"))
        },
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "script_sha256": sha256(Path(__file__)),
        "git_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip(),
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Replayed {len(rows)} runs without mismatches: {args.output}")


if __name__ == "__main__":
    main()
