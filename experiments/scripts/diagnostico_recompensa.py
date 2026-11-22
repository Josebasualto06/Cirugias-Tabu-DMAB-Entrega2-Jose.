"""Exploratory check: does the reward drop, and when does Page-Hinkley restart?

Page-Hinkley watches the mean reward, while diagnostico_revision.py measured the
share of rewarded proposals by phase. This replays a sample of the archived
runs, seeds 90-93 on the 48 congestion instances, and records by batch the
reward per proposal (duplicates count as zero) and the restarts of D-MAB.

It tests no hypothesis, compares no method and uses no new seed. Every replay
must reproduce its archived objective and restarts.

    python -X utf8 experiments/scripts/diagnostico_recompensa.py --workers 14
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from surgery_optim import tabu  # noqa: E402
from surgery_optim.bandit import DynamicMultiArmedBandit  # noqa: E402
from surgery_optim.instances import load_instance  # noqa: E402


RESULTS = ROOT / "experiments/results"
SOURCE = RESULTS / "entrega2_congestion_90_109/runs.csv"
OUTPUT = RESULTS / "entrega3_diagnostico_recompensa"
SEEDS = range(90, 94)
BATCHES = 200


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def replay(saved: dict) -> tuple[str, np.ndarray]:
    """Return proposals, reward sum and restarts for each batch of one run."""
    policy = saved["method"].removesuffix("3030")
    context = load_instance(ROOT / f"instances/congestion/{saved['instance_id']}.yaml")
    updates, fired = [], []

    class Timed(DynamicMultiArmedBandit):
        def update(self, action, reward):
            restarted = super().update(action, reward)
            if restarted:
                fired.append(len(updates))
            updates.append(reward)
            return restarted

    original = tabu.DynamicMultiArmedBandit
    tabu.DynamicMultiArmedBandit = Timed
    try:
        result = tabu.run_tabu(context, int(saved["seed"]), policy)
    finally:
        tabu.DynamicMultiArmedBandit = original
    key = (saved["instance_id"], saved["seed"], policy)
    if not math.isclose(result.final_quality.objective, float(saved["objective"]), abs_tol=1e-9):
        raise AssertionError(("objective", key))
    if result.dmab_restarts != int(saved["dmab_restarts"]) or len(result.trace) != BATCHES:
        raise AssertionError(("restarts or batches", key))
    table = np.zeros((BATCHES, 3))
    for batch, step in enumerate(result.trace):
        table[batch, 0] = step["attempts"]
        table[batch, 1] = step["mean_reward"] * step["distinct_candidates"]
    if updates:
        if len(updates) != table[:, 0].sum() or not math.isclose(
                sum(updates), table[:, 1].sum(), abs_tol=1e-6):
            raise AssertionError(("reward per proposal", key))
        ends = np.cumsum(table[:, 0])
        for position in fired:
            table[np.searchsorted(ends, position, side="right"), 2] += 1
    return policy, table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    if (OUTPUT / "manifest.json").exists():
        raise SystemExit(f"refusing to overwrite a completed diagnosis: {OUTPUT}")
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        tasks = [row for row in csv.DictReader(stream)
                 if row["method"] in ("uniform3030", "dmab3030") and int(row["seed"]) in SEEDS]
    totals = {policy: np.zeros((BATCHES, 3)) for policy in ("uniform", "dmab")}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for policy, table in pool.map(replay, tasks, chunksize=2):
            totals[policy] += table

    batches, summary = [], []
    for policy, table in totals.items():
        batches += [{"policy": policy, "batch": batch + 1, "proposals": int(row[0]),
                     "reward_sum": float(row[1]), "restarts": int(row[2])}
                    for batch, row in enumerate(table)]
        for name, parts in (("third", 3), ("tenth", 10)):
            part = np.arange(BATCHES) * parts // BATCHES
            for index in range(parts):
                current = table[part == index].sum(axis=0)
                summary.append({"measure": f"mean_reward_by_{name}",
                                "item": f"{policy}:{index + 1}",
                                "value": float(current[1] / current[0])})
                if policy == "dmab":
                    summary.append({"measure": f"restarts_share_by_{name}",
                                    "item": f"{policy}:{index + 1}",
                                    "value": float(100 * current[2] / table[:, 2].sum())})
    after = totals["dmab"][np.arange(BATCHES) * 3 // BATCHES > 0, 2].sum()
    summary.append({"measure": "restarts_after_first_third", "item": "dmab",
                    "value": float(100 * after / totals["dmab"][:, 2].sum())})

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write(OUTPUT / "batches.csv", batches)
    write(OUTPUT / "summary.csv", summary)
    lines = [
        "# Recompensa media y momento de los reinicios", "",
        "**Exploratorio y posterior.** No prueba hipótesis ni cambia decisiones.", "",
        f"- Muestra: {len(tasks)} corridas archivadas (48 instancias, semillas "
        f"{SEEDS[0]}–{SEEDS[-1]}, Tabu uniforme y D-MAB), repetidas sin discrepancias.",
        "- `mean_reward`: recompensa por propuesta, que es lo que observa Page–Hinkley. Un "
        "duplicado vale cero.",
        "- Tercios y décimos se forman con los 200 lotes de cada corrida.", "",
        "| Medida | Elemento | Valor |", "|---|---|---:|",
    ]
    lines += [f"| {row['measure']} | {row['item']} | {row['value']:.4f} |" for row in summary]
    (OUTPUT / "RECOMPENSA.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "status": "completed", "kind": "exploratory post-hoc diagnosis, no hypothesis tested",
        "seeds": list(SEEDS), "replayed_runs": len(tasks), "mismatches": 0,
        "hash_convention": "sha256 of LF-normalized bytes",
        "sources_sha256": {SOURCE.relative_to(ROOT).as_posix(): sha256_lf(SOURCE)},
        "code_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path)
                        for path in sorted((ROOT / "src/surgery_optim").rglob("*.py"))},
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "script_sha256": sha256_lf(Path(__file__)),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print((OUTPUT / "RECOMPENSA.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
