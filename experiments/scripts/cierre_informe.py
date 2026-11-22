"""Exploratory measures added when closing the final report.

All three were computed after seeing the results. They run no search, use no
seed, test no hypothesis and change no registered decision:

1. effect size r = Z/sqrt(n) of the registered Wilcoxon of C1-C4 and E1, on the
   same instance means, with Z from the normal approximation and the sign of
   the difference in ranks (negative favours the alternative);
2. sensitivity to the start-time rule: delay each anesthesia in the archived
   congestion schedules until its surgery can be set up, moving nothing else;
3. FIFO, SPT and LPT against the archived portfolio and two Tabu in the 12
   official instances, seeds 60-79, also with the room imbalance term of the
   course objective, delta = 100, that the project omits.

The imbalance is written from the formula of the course repository's evaluator
(commit ecd30e3). No code of that repository is executed.

    python -X utf8 experiments/scripts/cierre_informe.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import rankdata, wilcoxon


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from surgery_optim.baselines import construct_baseline  # noqa: E402
from surgery_optim.instances import load_instance  # noqa: E402
from surgery_optim.objective import ALPHA, BETA, GAMMA, quality  # noqa: E402
from surgery_optim.scheduler import WAIT_TOLERANCE, schedule_instance_solution  # noqa: E402


RESULTS = ROOT / "experiments/results"
OUTPUT = RESULTS / "entrega3_cierre"
FAMILY = RESULTS / "entrega2_congestion_90_109"
CONFIRMATION = RESULTS / "entrega3_confirmacion_ucb1"
PORTFOLIOS = RESULTS / "portfolios_60_79"
OFFICIAL_RULES = RESULTS / "validation_40_59/baselines.csv"
RULES = ("fifo", "spt", "lpt")
OFFICIAL_METHODS = ("fixed_portfolio6060", "two_uniform6060")
THRESHOLD = 0.25
DELTA = 100.0


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


def saved_solutions(folder: Path):
    with (folder / "solutions.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            saved = json.loads(line)
            rooms = {int(job): {int(op): room for op, room in pair.items()}
                     for job, pair in saved["solution"]["room_assignment"].items()}
            yield saved, {"job_sequence_base": saved["solution"]["job_sequence_base"],
                          "room_assignment": rooms}


def effect_sizes() -> list[dict]:
    found = []
    for folder in (FAMILY, CONFIRMATION):
        value = {(r["instance_id"], int(r["seed"]), r["method"]): float(r["objective"])
                 for r in read(folder / "runs.csv")}
        instances = sorted({instance for instance, _, _ in value})
        seeds = sorted({seed for _, seed, _ in value})
        for saved in read(folder / "comparisons.csv"):
            means = np.array([
                np.mean([value[i, s, saved["method"]] - value[i, s, saved["reference"]]
                         for s in seeds]) for i in instances])
            registered = float(wilcoxon(means, zero_method="zsplit").pvalue)
            if not math.isclose(registered, float(saved["wilcoxon_p"]), abs_tol=1e-9):
                raise AssertionError(("registered test", saved["comparison"]))
            n = len(means)
            ranks = rankdata(np.abs(means))
            positive = ranks[means > 0].sum() + ranks[means == 0].sum() / 2
            z = abs(wilcoxon(means, zero_method="zsplit", method="approx").zstatistic)
            z = math.copysign(z, positive - n * (n + 1) / 4)
            found.append({"study": folder.name, "comparison": saved["comparison"],
                          "instances": n, "zero_differences": int((means == 0).sum()),
                          "z": z, "r": z / math.sqrt(n)})
    return found


def delay_anesthesia(context, solution) -> dict:
    """Delay only the anesthesia starts; check every constraint as intervals."""
    end, entries = schedule_instance_solution(context, solution)
    by_job = defaultdict(dict)
    for entry in entries:
        by_job[entry.job_id][entry.operation] = entry
    limits = {job.job_id: job.operations[1].max_wait for job in context.jobs}
    busy, waits, original, starts = defaultdict(list), [], [], 0.0
    for job_id, operations in by_job.items():
        first, second = operations[1], operations[2]
        begin = second.start + max(second.setup, second.transition)
        start = first.start + (second.start - first.finish)
        ready = start + (first.finish - first.start)
        if start < first.start - 1e-9 or begin - ready > limits[job_id] + WAIT_TOLERANCE:
            raise AssertionError(("delay", job_id))
        waits.append(begin - ready)
        original.append(begin - first.finish)
        starts += start + second.start
        same = first.room == second.room
        busy["room", first.room].append((start, second.finish if same else begin))
        if not same:
            busy["room", second.room].append((second.start, second.finish))
        busy["staff", first.personnel].append((start, begin))
        busy["staff", second.personnel].append((second.start, second.finish))
    for spans in busy.values():
        spans.sort()
        if any(after[0] < before[1] - 1e-9 for before, after in zip(spans, spans[1:])):
            raise AssertionError("overlap after the delay")
    return {"objective": quality(context, solution).objective, "makespan": end,
            "wait": sum(original), "delayed_wait": sum(waits),
            "delayed_objective": end + ALPHA * starts + BETA * sum(waits) + GAMMA * max(waits)}


def start_rule() -> tuple[list[dict], list[dict]]:
    contexts = {path.stem: load_instance(path)
                for path in sorted((ROOT / "instances/congestion").glob("HOSP-*.yaml"))}
    schedules = []
    for folder in (FAMILY, CONFIRMATION):
        archived = {(r["instance_id"], int(r["seed"]), r["method"]): float(r["objective"])
                    for r in read(folder / "runs.csv")}
        for saved, solution in saved_solutions(folder):
            key = (saved["instance_id"], int(saved["seed"]), saved["method"])
            measured = delay_anesthesia(contexts[key[0]], solution)
            if not math.isclose(measured["objective"], archived[key], abs_tol=1e-6):
                raise AssertionError(("archived objective", key))
            schedules.append({"study": folder.name, "instance_id": key[0], "seed": key[1],
                              "method": key[2], **measured})
    rules = [{"instance_id": name, "rule": rule,
              **delay_anesthesia(context, construct_baseline(context, rule))}
             for name, context in contexts.items() for rule in RULES]
    return schedules, rules


def course_objective(context, rooms: dict, objective: float) -> float:
    used = Counter(room for pair in rooms.values() for room in pair.values())
    uses = np.array([used[room] for room in context.rooms], dtype=float)
    unused = int((uses == 0).sum())
    return objective + DELTA * float(uses.std() / uses.mean() + unused * (unused + 1))


def official() -> list[dict]:
    contexts = {path.stem: load_instance(path)
                for path in sorted((ROOT / "instances/standard").glob("HOSP-*.yaml"))}
    archived = {(r["instance_id"], r["rule"]): float(r["objective"]) for r in read(OFFICIAL_RULES)}
    best = {}
    for name, context in contexts.items():
        measures = []
        for rule in RULES:
            built = construct_baseline(context, rule)
            measured = quality(context, built)
            if not math.isclose(measured.objective, archived[name, rule], abs_tol=1e-6):
                raise AssertionError(("rule", name, rule))
            measures.append((measured.objective, measured.makespan, course_objective(
                context, built["room_assignment"], measured.objective)))
        best[name] = np.min(measures, axis=0)
    saved_runs = {(r["instance_id"], int(r["seed"]), r["method"]): float(r["objective"])
                  for r in read(PORTFOLIOS / "runs.csv")}
    measured_runs = defaultdict(list)
    for saved, solution in saved_solutions(PORTFOLIOS):
        if saved["method"] not in OFFICIAL_METHODS:
            continue
        key = (saved["instance_id"], int(saved["seed"]), saved["method"])
        context = contexts[key[0]]
        measured = quality(context, solution)
        if not math.isclose(measured.objective, saved_runs[key], abs_tol=1e-6):
            raise AssertionError(("portfolio run", key))
        measured_runs[key[2], key[0]].append((measured.objective, measured.makespan, course_objective(
            context, solution["room_assignment"], measured.objective)))
    found = []
    for method in OFFICIAL_METHODS:
        for name in contexts:
            runs = np.array(measured_runs[method, name])
            if len(runs) != 20:
                raise AssertionError(("seeds", method, name))
            for k, measure in enumerate(("objective", "makespan", "course_objective")):
                found.append({
                    "method": method, "instance_id": name, "measure": measure,
                    "mean": float(runs[:, k].mean()), "best_rule": float(best[name][k]),
                    "gain_percent": float(100 * (1 - runs[:, k].mean() / best[name][k])),
                    "runs_worse": int((runs[:, k] > best[name][k] + 1e-9).sum())})
    return found


def main() -> None:
    if (OUTPUT / "manifest.json").exists():
        raise SystemExit(f"refusing to overwrite a completed analysis: {OUTPUT}")
    sizes = effect_sizes()
    schedules, rules = start_rule()
    official_rows = official()

    summary: list[dict] = []

    def add(measure: str, item: str, value: float) -> None:
        summary.append({"measure": measure, "item": item, "value": float(value)})

    for row in sizes:
        add("effect_size_r", row["comparison"], row["r"])
    add("delayed_schedules", "all", len(schedules))
    add("schedules_waiting_after_delay", "all",
        sum(row["delayed_wait"] > WAIT_TOLERANCE for row in schedules))
    best_rule = defaultdict(lambda: math.inf)
    for row in rules:
        best_rule[row["instance_id"]] = min(best_rule[row["instance_id"]], row["delayed_objective"])
    add("best_rule_delayed_objective", "all", np.mean(list(best_rule.values())))
    for study in (FAMILY.name, CONFIRMATION.name):
        current = [row for row in schedules if row["study"] == study]
        means = {}
        for method in sorted({row["method"] for row in current}):
            group = [row for row in current if row["method"] == method]
            by_instance = defaultdict(list)
            for row in group:
                by_instance[row["instance_id"]].append(row["delayed_objective"])
            means[method] = {field: np.mean([row[field] for row in group])
                             for field in ("objective", "delayed_objective")}
            add("mean_objective", f"{study}:{method}", means[method]["objective"])
            add("mean_delayed_objective", f"{study}:{method}", means[method]["delayed_objective"])
            add("instances_where_best_rule_wins", f"{study}:{method}", sum(
                best_rule[name] < np.mean(values) - THRESHOLD
                for name, values in by_instance.items()))
        for field in ("objective", "delayed_objective"):
            add(f"ucb_minus_uniform_{field}", study,
                means["ucb3030"][field] - means["uniform3030"][field])
    for method in OFFICIAL_METHODS:
        for measure in ("objective", "makespan", "course_objective"):
            current = [row for row in official_rows
                       if row["method"] == method and row["measure"] == measure]
            item = f"{method}:{measure}"
            add("official_instances_better_than_best_rule", item,
                sum(row["mean"] < row["best_rule"] - 1e-9 for row in current))
            add("official_mean_gain_percent", item, np.mean([row["gain_percent"] for row in current]))
            add("official_runs_worse_than_best_rule", item, sum(row["runs_worse"] for row in current))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write(OUTPUT / "effect_sizes.csv", sizes)
    write(OUTPUT / "delayed_schedules.csv", schedules)
    write(OUTPUT / "delayed_rules.csv", rules)
    write(OUTPUT / "official_rules.csv", official_rows)
    write(OUTPUT / "summary.csv", summary)
    lines = [
        "# Cierre del informe: tres medidas exploratorias", "",
        "**Se calcularon después de ver los resultados.** No prueban hipótesis ni cambian las "
        "decisiones registradas.", "",
        "- `effect_size_r`: r = Z/√n de la prueba de Wilcoxon registrada, sobre las mismas medias "
        "por instancia. Z usa la aproximación normal; un valor negativo favorece a la alternativa.",
        "- Retraso: solo se mueve el inicio de la anestesia, hasta que la preparación de la "
        "cirugía puede empezar. Cada calendario se comprobó sin solapamientos. No se repitió "
        "la búsqueda, así que no dice qué habría encontrado con esa regla.",
        "- `official`: instancias oficiales, semillas 60–79, media por instancia frente a la mejor "
        "de FIFO, SPT y LPT en cada medida. `course_objective` suma 100 veces el desequilibrio "
        "de salas del objetivo de clase. No usa el simulador docente ni su regla de salas.", "",
        "| Medida | Elemento | Valor |", "|---|---|---:|",
    ]
    lines += [f"| {row['measure']} | {row['item']} | {row['value']:.3f} |" for row in summary]
    (OUTPUT / "CIERRE.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    sources = [FAMILY / "runs.csv", FAMILY / "solutions.jsonl", FAMILY / "comparisons.csv",
               CONFIRMATION / "runs.csv", CONFIRMATION / "solutions.jsonl",
               CONFIRMATION / "comparisons.csv", PORTFOLIOS / "runs.csv",
               PORTFOLIOS / "solutions.jsonl", OFFICIAL_RULES]
    manifest = {
        "status": "completed", "kind": "exploratory, after seeing the results; no decision changed",
        "searches_run": 0, "delta": DELTA,
        "software": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "scipy": scipy.__version__},
        "hash_convention": "sha256 of LF-normalized bytes",
        "sources_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path) for path in sources},
        "code_sha256": {path.relative_to(ROOT).as_posix(): sha256_lf(path)
                        for path in sorted((ROOT / "src/surgery_optim").rglob("*.py"))},
        "script": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "script_sha256": sha256_lf(Path(__file__)),
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print((OUTPUT / "CIERRE.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
