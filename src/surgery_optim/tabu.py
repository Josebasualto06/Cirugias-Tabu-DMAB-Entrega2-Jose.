"""Matched-budget mixed-neighborhood Tabu Search with online operator choice."""

from __future__ import annotations

import copy
import math
import random
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from .bandit import MOVES, DynamicMultiArmedBandit
from .baselines import construct_baseline
from .encoding import LOWER_BOUND, UPPER_BOUND, decode_feasible, encode_solution
from .model import InstanceContext
from .objective import Quality, quality
from .scheduler import schedule_instance_solution


Policy = Literal["uniform", "dmab", "ucb"]


TabuMemory = Literal["solution", "attribute"]


@dataclass(frozen=True, slots=True)
class TabuConfig:
    """Search parameters.

    ``exploration`` is the D-MAB/UCB1 scaling factor C. ``tabu_memory``
    selects what the tabu list stores: complete solution signatures
    (``"solution"``, default) or the job moved by the accepted candidate
    (``"attribute"``, which performed worse in the calibration). With ``common_random_numbers`` every policy draws the
    same random numbers for the target job and the uniform move, so that
    bandit policies only differ from uniform Tabu in the move they apply.
    ``TabuConfig.entrega1()`` reproduces the configuration of Entrega 1.
    """

    population_size: int = 30
    evaluation_budget: int = 3030
    candidates_per_batch: int = 15
    tabu_tenure: int = 7
    ph_delta: float = 0.01
    ph_lambda: float = 1.0
    exploration: float = 0.1
    tabu_memory: TabuMemory = "solution"
    common_random_numbers: bool = True

    def __post_init__(self) -> None:
        if self.population_size < 3 or self.evaluation_budget < self.population_size:
            raise ValueError("budget must cover at least three initial solutions")
        if self.candidates_per_batch < 1 or self.tabu_tenure < 1:
            raise ValueError("batch size and tabu tenure must be positive")
        if self.exploration < 0 or self.ph_lambda <= 0 or self.ph_delta < 0:
            raise ValueError("invalid bandit parameters")
        if self.tabu_memory not in ("solution", "attribute"):
            raise ValueError(f"unknown tabu memory: {self.tabu_memory}")

    @classmethod
    def entrega1(cls, **overrides: Any) -> "TabuConfig":
        """Configuration used for the Entrega 1 results (seeds 0–39)."""
        settings: dict[str, Any] = {
            "exploration": 1.0, "ph_lambda": 0.35, "tabu_memory": "solution",
            "common_random_numbers": False,
        }
        settings.update(overrides)
        return cls(**settings)

    @classmethod
    def from_manifest(cls, settings: dict[str, Any]) -> "TabuConfig":
        """Rebuild a config stored in a results manifest.

        Manifests written before ``tabu_memory`` existed (Entrega 1) are read
        with the Entrega 1 defaults, so their runs can still be replayed.
        """
        if "tabu_memory" not in settings:
            return cls.entrega1(**settings)
        return cls(**settings)


@dataclass(frozen=True, slots=True)
class TabuResult:
    policy: Policy
    seed: int
    instance_id: str
    instance_digest: str
    initial_objective: float
    final_quality: Quality
    evaluations: int
    feasible_evaluations: int
    runtime_seconds: float
    attempted_choices: dict[str, int]
    evaluated_choices: dict[str, int]
    repaired_candidates: int
    dmab_restarts: int
    best_solution: dict[str, Any]
    trace: tuple[dict[str, Any], ...]


def signature(solution: dict[str, Any], context: InstanceContext) -> tuple:
    return (
        tuple(solution["job_sequence_base"]),
        tuple(
            (job.job_id, operation.operation_id,
             solution["room_assignment"][job.job_id][operation.operation_id])
            for job in context.jobs for operation in job.operations
        ),
    )


def blocked_priority(context: InstanceContext, solution: dict[str, Any]) -> list[int]:
    """At most three patients with the longest anesthesia-to-surgery waits."""
    _, schedule = schedule_instance_solution(context, solution)
    by_job: dict[int, dict[int, Any]] = {}
    for entry in schedule:
        by_job.setdefault(entry.job_id, {})[entry.operation] = entry
    waits = []
    for job_id, operations in by_job.items():
        first, second = operations[1], operations[2]
        surgery_start = second.start + max(second.transition, second.setup)
        waits.append((max(0.0, surgery_start - first.finish), job_id))
    waits.sort(reverse=True)
    return [job_id for wait, job_id in waits[:3] if wait > 0]


def neighbor(solution: dict[str, Any], context: InstanceContext, rng: random.Random,
             priority_jobs: list[int], move: str | None = None,
             draw_uniform_move: bool = True) -> tuple[dict[str, Any], int, str]:
    """Apply one move of the mixed neighborhood; return (candidate, job, move).

    The target job is drawn first (65 % from the most blocked jobs). When
    ``draw_uniform_move`` is true a uniform move is drawn next, as in the
    historical uniform Tabu; a bandit's ``move`` then replaces it, so every
    policy consumes the random stream identically. With ``move=None`` the
    uniform move is used.
    """
    if move is None and not draw_uniform_move:
        raise ValueError("a move is required when no uniform move is drawn")
    candidate = copy.deepcopy(solution)
    sequence = candidate["job_sequence_base"]
    job_ids = [job.job_id for job in context.jobs]
    target = (rng.choice(priority_jobs) if priority_jobs and rng.random() < 0.65
              else rng.choice(job_ids))
    if draw_uniform_move:
        uniform_move = rng.choice(MOVES)
        move = uniform_move if move is None else move
    assert move is not None
    if move == "swap":
        other = rng.choice([job_id for job_id in job_ids if job_id != target])
        first, second = sequence.index(target), sequence.index(other)
        sequence[first], sequence[second] = sequence[second], sequence[first]
    elif move == "insert":
        sequence.remove(target)
        sequence.insert(rng.randrange(len(sequence) + 1), target)
    elif move in ("room_1", "room_2", "room_pair"):
        job = next(job for job in context.jobs if job.job_id == target)
        operation_ids = (1, 2) if move == "room_pair" else (
            1 if move == "room_1" else 2,
        )
        for operation_id in operation_ids:
            operation = next(op for op in job.operations if op.operation_id == operation_id)
            current = candidate["room_assignment"][target][operation_id]
            alternatives = [room for room in operation.eligible_rooms if room != current]
            if alternatives:
                candidate["room_assignment"][target][operation_id] = rng.choice(alternatives)
    else:
        raise ValueError(f"unknown move: {move}")
    return candidate, target, move


def run_tabu(context: InstanceContext, seed: int, policy: Policy,
             config: TabuConfig = TabuConfig()) -> TabuResult:
    """Tabu Search with a population archive and a fixed evaluation budget.

    The search keeps the 30 initial solutions (FIFO, SPT, LPT and random
    keys) as an archive: each accepted candidate replaces the worst archived
    solution, and the local solution jumps to the archive's best whenever it
    improves the incumbent. Strictly this is a population-assisted Tabu.
    """
    if policy not in ("uniform", "dmab", "ucb"):
        raise ValueError(f"unknown policy: {policy}")
    started = time.perf_counter()
    np_rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    n = len(context.jobs)
    dimension = n + sum(len(job.operations) for job in context.jobs)
    positions = np_rng.uniform(
        LOWER_BOUND, UPPER_BOUND, (config.population_size, dimension)
    )
    for index, rule in enumerate(("fifo", "spt", "lpt")):
        positions[index] = encode_solution(construct_baseline(context, rule), context)

    def evaluate(solution: dict[str, Any]) -> tuple[float, float]:
        try:
            measured = quality(context, solution)
            return measured.objective, measured.makespan
        except (IndexError, KeyError, TypeError, ValueError):
            return float("inf"), float("inf")

    solutions = [decode_feasible(position, context) for position in positions]
    evaluated = [evaluate(solution) for solution in solutions]
    fitness = np.array([item[0] for item in evaluated], dtype=float)
    makespans = np.array([item[1] for item in evaluated], dtype=float)
    spent = config.population_size
    feasible = int(np.isfinite(fitness).sum())
    best_index = int(np.argmin(fitness))
    best_value = float(fitness[best_index])
    initial_value = best_value
    best_makespan = float(makespans[best_index])
    best_solution = copy.deepcopy(solutions[best_index])
    local_solution = copy.deepcopy(best_solution)
    local_value = best_value
    tabu: deque[tuple] = deque(maxlen=config.tabu_tenure)
    attribute_memory = config.tabu_memory == "attribute"
    if not attribute_memory:
        tabu.append(signature(local_solution, context))
    bandit = (DynamicMultiArmedBandit(
        delta=config.ph_delta, threshold=config.ph_lambda,
        exploration=config.exploration, dynamic=policy == "dmab",
    ) if policy != "uniform" else None)
    attempted = Counter({move: 0 for move in MOVES})
    evaluated_choices = Counter({move: 0 for move in MOVES})
    repaired = 0
    trace = []

    while spent < config.evaluation_budget:
        priority = blocked_priority(context, local_solution)
        count = min(config.candidates_per_batch, config.evaluation_budget - spent)
        attempts = 0
        seen: set[tuple] = set()
        candidates = []
        rewards = []
        old_local = local_value
        batch_choices = Counter({move: 0 for move in MOVES})
        while len(candidates) < count and attempts < 10 * count:
            attempts += 1
            requested = bandit.select() if bandit is not None else None
            proposal, moved_job, move = neighbor(
                local_solution, context, py_rng, priority, requested,
                draw_uniform_move=bandit is None or config.common_random_numbers,
            )
            attempted[move] += 1
            position = encode_solution(proposal, context)
            decoded = decode_feasible(position, context)
            proposed_signature = signature(decoded, context)
            # The decoder may undo part of the move to keep max_wait feasible.
            was_repaired = proposed_signature != signature(proposal, context)
            if proposed_signature in seen:
                if bandit is not None:
                    bandit.update(move, 0.0)
                continue
            seen.add(proposed_signature)
            value, makespan = evaluate(decoded)
            spent += 1
            feasible += int(math.isfinite(value))
            repaired += int(was_repaired)
            tabu_key = moved_job if attribute_memory else proposed_signature
            candidates.append((value, makespan, position, decoded, tabu_key))
            evaluated_choices[move] += 1
            batch_choices[move] += 1
            reward = min(1.0, max(0.0, old_local - value)
                         / max(1.0, 0.02 * initial_value))
            rewards.append(reward)
            if bandit is not None:
                bandit.update(move, reward)
        if not candidates:
            raise RuntimeError("Tabu neighborhood produced no candidate")
        admissible = [item for item in candidates
                      if item[4] not in tabu or item[0] < best_value]
        chosen = min(admissible or candidates, key=lambda item: (item[0], item[1]))
        value, makespan, position, local_solution, tabu_key = chosen
        local_value = value
        tabu.append(tabu_key)
        worst = int(np.argmax(fitness))
        positions[worst] = position
        solutions[worst] = local_solution
        fitness[worst] = value
        makespans[worst] = makespan
        best_in_population = int(np.argmin(fitness))
        if fitness[best_in_population] < best_value:
            best_value = float(fitness[best_in_population])
            best_makespan = float(makespans[best_in_population])
            best_solution = copy.deepcopy(solutions[best_in_population])
            local_solution = copy.deepcopy(best_solution)
            local_value = best_value
        trace.append({
            "evaluations": spent, "best_objective": best_value,
            "best_makespan": best_makespan,
            "attempts": attempts, "distinct_candidates": len(candidates),
            "mean_reward": float(np.mean(rewards)) if rewards else 0.0,
            "repaired_candidates": repaired,
            **{f"choices_{move}": batch_choices[move] for move in MOVES},
        })

    strict_quality = quality(context, best_solution)
    assert len(schedule_instance_solution(context, best_solution)[1]) == 2 * n
    assert math.isclose(strict_quality.makespan, best_makespan, abs_tol=1e-9)
    assert math.isclose(strict_quality.objective, best_value, abs_tol=1e-9)
    return TabuResult(
        policy=policy, seed=seed, instance_id=context.instance_id,
        instance_digest=context.digest, initial_objective=initial_value,
        final_quality=strict_quality, evaluations=spent,
        feasible_evaluations=feasible, runtime_seconds=time.perf_counter() - started,
        attempted_choices=dict(attempted), evaluated_choices=dict(evaluated_choices),
        repaired_candidates=repaired,
        dmab_restarts=bandit.restarts if bandit is not None else 0,
        best_solution=best_solution, trace=tuple(trace),
    )
