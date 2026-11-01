"""Paired single-process timing smoke test for local CPU and Colab CPU.

Run the identical bundle, Python and NumPy/PyYAML versions in each environment.
Installation, loading and warmup are excluded from the search totals.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from surgery_optim.instances import load_instance
from surgery_optim.tabu import TabuConfig, run_tabu

SEEDS = tuple(range(2100, 2105))
WARMUP_SEED = 2199
POLICIES = (("TS-U", "uniform"), ("TS-DMAB", "dmab"))
FIELDS = (
    "instance_id", "jobs", "seed", "method", "policy", "order_in_pair",
    "wall_seconds", "cpu_seconds", "engine_seconds", "evaluations",
    "feasible_evaluations", "initial_objective", "objective", "makespan",
    "total_wait", "max_wait", "dmab_restarts", "repaired_candidates",
    "status",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def hardware() -> dict:
    result = {
        "system": platform.system(), "release": platform.release(),
        "machine": platform.machine(), "processor": platform.processor(),
        "logical_cpus": os.cpu_count(), "ram_bytes": None,
    }
    if platform.system() == "Linux":
        cpuinfo = Path("/proc/cpuinfo")
        if cpuinfo.exists():
            for line in cpuinfo.read_text().splitlines():
                if line.startswith("model name"):
                    result["processor"] = line.split(":", 1)[1].strip()
                    break
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            for line in meminfo.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    result["ram_bytes"] = int(line.split()[1]) * 1024
                    break
    elif platform.system() == "Darwin":
        for key, target in (
            ("machdep.cpu.brand_string", "processor"), ("hw.memsize", "ram_bytes")
        ):
            try:
                value = subprocess.check_output(
                    ["sysctl", "-n", key], text=True, stderr=subprocess.DEVNULL,
                    timeout=5,
                ).strip()
                result[target] = int(value) if target == "ram_bytes" else value
            except (OSError, subprocess.SubprocessError, ValueError):
                pass
    return result


def versions() -> dict:
    result = {"python": platform.python_version()}
    for package in ("numpy", "PyYAML", "scipy", "matplotlib"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = None
    return result


def digest_files(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(paths)}


def summarize(rows: list[dict]) -> dict:
    groups = []
    for method, _ in POLICIES:
        for jobs in (15, 20, 25, 30):
            subset = [r for r in rows if r["method"] == method and r["jobs"] == jobs]
            times = [r["wall_seconds"] for r in subset]
            groups.append({
                "method": method, "jobs": jobs, "runs": len(times),
                "wall_seconds": sum(times),
                "mean_seconds": statistics.mean(times),
                "median_seconds": statistics.median(times),
                "stdev_seconds": statistics.stdev(times) if len(times) > 1 else 0,
                "min_seconds": min(times), "max_seconds": max(times),
            })
    quality_columns = (
        "instance_id", "seed", "method", "evaluations", "initial_objective",
        "objective", "makespan", "total_wait", "max_wait",
    )
    qualities = [
        {key: row[key] for key in quality_columns}
        for row in sorted(rows, key=lambda r: (r["instance_id"], r["seed"], r["method"]))
    ]
    quality_digest = hashlib.sha256(json.dumps(
        qualities, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()
    return {
        "runs": len(rows),
        "search_wall_seconds": sum(r["wall_seconds"] for r in rows),
        "search_cpu_seconds": sum(r["cpu_seconds"] for r in rows),
        "candidate_evaluations": sum(r["evaluations"] for r in rows),
        "quality_sha256": quality_digest,
        "groups": groups,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=("local", "colab"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    setup_start = time.perf_counter_ns()
    paths = [
        ROOT / "instances/standard" / f"HOSP-STD-{n}-{r:02d}.yaml"
        for n in (15, 20, 25, 30) for r in (1, 2, 3)
    ]
    contexts = [load_instance(p) for p in paths]
    config = TabuConfig(
        evaluation_budget=6060, population_size=30, candidates_per_batch=15,
        tabu_tenure=7, ph_delta=0.01, ph_lambda=1.0, exploration=0.1,
        tabu_memory="solution", common_random_numbers=True,
    )
    manifest = {
        "benchmark": "OII464-local-colab-cpu-smoke-v1",
        "label": args.label, "state": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "seeds": list(SEEDS), "warmup_seed": WARMUP_SEED,
        "runs_planned": len(contexts) * len(SEEDS) * len(POLICIES),
        "config": asdict(config), "hardware": hardware(), "versions": versions(),
        "code_sha256": digest_files(
            list((ROOT / "src/surgery_optim").rglob("*.py")) + [Path(__file__).resolve()]
        ),
        "instance_sha256": digest_files(paths),
        "execution": "one process, sequential, alternating within-pair order",
        "clock": "perf_counter_ns external around run_tabu",
        "search_includes": "initialization, search and engine final strict validation",
        "search_excludes": "installation, imports, instance loading, warmup, output writes",
        "wall_loop_includes": "searches and incremental output writes",
    }
    json_write(output / "manifest.json", manifest)
    manifest["setup_seconds"] = (time.perf_counter_ns() - setup_start) / 1e9
    warmup_start = time.perf_counter_ns()
    warmup_config = TabuConfig(
        **{**asdict(config), "evaluation_budget": 330}
    )
    for _, policy in POLICIES:
        run_tabu(contexts[0], WARMUP_SEED, policy, warmup_config)
    manifest["warmup_seconds"] = (time.perf_counter_ns() - warmup_start) / 1e9
    json_write(output / "manifest.json", manifest)

    rows = []
    solutions = []
    loop_started = time.perf_counter_ns()
    try:
        with (output / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            stream.flush()
            for index, context in enumerate(contexts):
                for repetition, seed in enumerate(SEEDS):
                    order = POLICIES if (index + repetition) % 2 == 0 else POLICIES[::-1]
                    for position, (method, policy) in enumerate(order, 1):
                        cpu_start = time.process_time_ns()
                        wall_start = time.perf_counter_ns()
                        result = run_tabu(context, seed, policy, config)
                        elapsed = (time.perf_counter_ns() - wall_start) / 1e9
                        cpu_elapsed = (time.process_time_ns() - cpu_start) / 1e9
                        q = result.final_quality
                        if (
                            result.evaluations != 6060
                            or result.feasible_evaluations != 6060
                            or not all(math.isfinite(v) for v in (
                                q.objective, q.makespan, q.blocked_minutes,
                                q.max_wait_minutes,
                            ))
                        ):
                            raise RuntimeError("invalid or incomplete benchmark search")
                        row = {
                            "instance_id": context.instance_id, "jobs": len(context.jobs),
                            "seed": seed, "method": method, "policy": policy,
                            "order_in_pair": position, "wall_seconds": elapsed,
                            "cpu_seconds": cpu_elapsed, "engine_seconds": result.runtime_seconds,
                            "evaluations": result.evaluations,
                            "feasible_evaluations": result.feasible_evaluations,
                            "initial_objective": result.initial_objective,
                            "objective": q.objective, "makespan": q.makespan,
                            "total_wait": q.blocked_minutes, "max_wait": q.max_wait_minutes,
                            "dmab_restarts": result.dmab_restarts,
                            "repaired_candidates": result.repaired_candidates, "status": "valid",
                        }
                        writer.writerow(row)
                        stream.flush()
                        rows.append(row)
                        solutions.append({
                            "instance_id": context.instance_id, "seed": seed,
                            "method": method, "best_solution": result.best_solution,
                        })
                        print(
                            f"{len(rows):03d}/{manifest['runs_planned']} "
                            f"{context.instance_id} seed={seed} {method} "
                            f"wall={elapsed:.6f}s cpu={cpu_elapsed:.6f}s "
                            f"objective={q.objective:.9f}",
                            flush=True,
                        )
        loop_elapsed = (time.perf_counter_ns() - loop_started) / 1e9
        summary = {
            "benchmark": manifest["benchmark"], "label": args.label, "state": "completed",
            **summarize(rows),
            "loop_wall_seconds": loop_elapsed,
            "setup_seconds": manifest["setup_seconds"],
            "warmup_seconds": manifest["warmup_seconds"],
            "hardware": manifest["hardware"], "versions": manifest["versions"],
            "completed_utc": datetime.now(timezone.utc).isoformat(),
        }
        json_write(output / "solutions.json", solutions)
        json_write(output / "summary.json", summary)
        manifest.update(state="completed", completed_utc=summary["completed_utc"])
        json_write(output / "manifest.json", manifest)
        print("SMOKE_SUMMARY_JSON=" + json.dumps(
            summary, separators=(",", ":"), allow_nan=False
        ), flush=True)
    except BaseException as error:
        manifest.update(
            state="failed", completed_runs=len(rows),
            error_type=type(error).__name__, error=str(error),
        )
        json_write(output / "manifest.json", manifest)
        raise


if __name__ == "__main__":
    main()
