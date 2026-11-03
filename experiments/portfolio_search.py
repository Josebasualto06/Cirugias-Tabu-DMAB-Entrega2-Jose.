"""Resumable trajectories and contextual allocation for controlled experiments.

The search mechanics reproduce surgery_optim.tabu. A trajectory preserves its
local solution, archive, tabu list, operator bandit and random stream while it
is paused. This module does not change the production search defaults.
"""

from __future__ import annotations

import copy
import math
import random
from collections import deque
from dataclasses import dataclass
from typing import Any

import numpy as np

from surgery_optim.bandit import DynamicMultiArmedBandit
from surgery_optim.baselines import construct_baseline
from surgery_optim.encoding import LOWER_BOUND, UPPER_BOUND, decode_feasible, encode_solution
from surgery_optim.model import InstanceContext
from surgery_optim.objective import quality
from surgery_optim.tabu import TabuConfig, blocked_priority, neighbor, signature


FEATURE_NAMES = (
    "intercept", "jobs_scaled", "budget_used", "arm_budget_share",
    "global_progress", "arm_gap", "local_gap", "stagnation",
    "recent_progress", "blocked_scaled",
)


class SearchTrajectory:
    """Pause a complete Tabu trajectory only at candidate-batch boundaries."""

    def __init__(self, context: InstanceContext, seed: int, policy: str,
                 config: TabuConfig) -> None:
        if policy not in ("uniform", "dmab") or config.tabu_memory != "solution":
            raise ValueError("these experiments use uniform/dmab and solution memory")
        self.context, self.seed, self.policy, self.config = context, seed, policy, config
        self.rng = random.Random(seed)
        n = len(context.jobs)
        dimension = n + sum(len(job.operations) for job in context.jobs)
        positions = np.random.default_rng(seed).uniform(
            LOWER_BOUND, UPPER_BOUND, (config.population_size, dimension)
        )
        for i, rule in enumerate(("fifo", "spt", "lpt")):
            positions[i] = encode_solution(construct_baseline(context, rule), context)
        self.solutions = [decode_feasible(p, context) for p in positions]
        evaluated = [self.evaluate(s) for s in self.solutions]
        self.fitness = np.array([v for v, _ in evaluated])
        self.makespans = np.array([m for _, m in evaluated])
        self.spent = config.population_size
        self.feasible = int(np.isfinite(self.fitness).sum())
        i = int(np.argmin(self.fitness))
        self.initial = self.best = float(self.fitness[i])
        self.best_solution = copy.deepcopy(self.solutions[i])
        self.local_solution = copy.deepcopy(self.best_solution)
        self.local = self.best
        self.tabu: deque[tuple] = deque(maxlen=config.tabu_tenure)
        self.tabu.append(signature(self.local_solution, context))
        self.bandit = (DynamicMultiArmedBandit(
            delta=config.ph_delta, threshold=config.ph_lambda,
            exploration=config.exploration,
        ) if policy == "dmab" else None)
        self.stagnation = 0
        self.recent: deque[float] = deque(maxlen=5)
        self.repaired = 0

    def evaluate(self, solution: dict) -> tuple[float, float]:
        try:
            q = quality(self.context, solution)
            return q.objective, q.makespan
        except (IndexError, KeyError, TypeError, ValueError):
            return float("inf"), float("inf")

    def advance(self, evaluations: int) -> None:
        """Spend exactly the requested evaluations without resetting a search."""
        if evaluations < 0:
            raise ValueError("negative evaluation allocation")
        target = self.spent + evaluations
        before = self.best
        while self.spent < target:
            priority = blocked_priority(self.context, self.local_solution)
            count = min(self.config.candidates_per_batch, target - self.spent)
            attempts, seen, candidates = 0, set(), []
            old_local = self.local
            while len(candidates) < count and attempts < 10 * count:
                attempts += 1
                requested = self.bandit.select() if self.bandit else None
                proposal, _, move = neighbor(
                    self.local_solution, self.context, self.rng, priority, requested,
                    draw_uniform_move=self.bandit is None or self.config.common_random_numbers,
                )
                decoded = decode_feasible(encode_solution(proposal, self.context), self.context)
                key = signature(decoded, self.context)
                if key in seen:
                    if self.bandit:
                        self.bandit.update(move, 0.0)
                    continue
                seen.add(key)
                value, makespan = self.evaluate(decoded)
                self.spent += 1
                self.feasible += int(math.isfinite(value))
                self.repaired += int(key != signature(proposal, self.context))
                candidates.append((value, makespan, decoded, key))
                if self.bandit:
                    reward = min(1.0, max(0.0, old_local - value)
                                 / max(1.0, 0.02 * self.initial))
                    self.bandit.update(move, reward)
            if not candidates:
                raise RuntimeError("empty neighborhood")
            admissible = [c for c in candidates if c[3] not in self.tabu or c[0] < self.best]
            value, makespan, self.local_solution, key = min(
                admissible or candidates, key=lambda c: (c[0], c[1])
            )
            self.local = value
            self.tabu.append(key)
            worst = int(np.argmax(self.fitness))
            self.solutions[worst] = self.local_solution
            self.fitness[worst], self.makespans[worst] = value, makespan
            i = int(np.argmin(self.fitness))
            if self.fitness[i] < self.best:
                self.best = float(self.fitness[i])
                self.best_solution = copy.deepcopy(self.solutions[i])
                self.local_solution = copy.deepcopy(self.best_solution)
                self.local = self.best
        gain = max(0.0, before - self.best)
        self.recent.append(gain)
        self.stagnation = 0 if gain > 1e-9 else self.stagnation + 1

    def features(self, global_best: float, total_spent: int, budget: int) -> np.ndarray:
        scale = max(1.0, 0.02 * self.initial)
        q = quality(self.context, self.best_solution)
        return np.array([
            1.0, len(self.context.jobs) / 30.0, total_spent / budget,
            self.spent / max(1, total_spent),
            min(1.0, max(0.0, self.initial - global_best) / self.initial),
            min(1.0, max(0.0, self.best - global_best) / scale),
            min(1.0, max(0.0, self.local - self.best) / scale),
            min(1.0, self.stagnation / 10.0),
            min(1.0, sum(self.recent) / scale),
            min(1.0, q.blocked_minutes / scale),
        ])


class ContextualAllocator:
    """Disjoint LinUCB over two search modes, learned within each execution."""

    def __init__(self, alpha: float = 0.25) -> None:
        self.alpha = alpha
        self.inverse = [np.eye(len(FEATURE_NAMES)) for _ in range(2)]
        self.target = [np.zeros(len(FEATURE_NAMES)) for _ in range(2)]

    def scores(self, contexts: list[np.ndarray]) -> tuple[list[float], list[float]]:
        means, scores = [], []
        for arm, x in enumerate(contexts):
            inv = self.inverse[arm]
            mean = float(x @ inv @ self.target[arm])
            uncertainty = math.sqrt(max(0.0, float(x @ inv @ x)))
            means.append(mean)
            scores.append(mean + self.alpha * uncertainty)
        return means, scores

    def update(self, arm: int, x: np.ndarray, reward: float) -> None:
        # Sherman-Morrison updates the regularized linear model after one block.
        inv = self.inverse[arm]
        direction = inv @ x
        self.inverse[arm] = inv - np.outer(direction, direction) / (1.0 + float(x @ direction))
        self.target[arm] += reward * x


@dataclass
class AllocationResult:
    objective: float
    best_solution: dict[str, Any]
    evaluations: int
    feasible_evaluations: int
    uniform_evaluations: int
    dmab_evaluations: int
    dmab_restarts: int
    floor_objective: float
    decisions: list[dict[str, Any]]


def run_allocation(context: InstanceContext, seed: int, budget: int = 6060,
                   protected: bool = False, block_size: int = 150,
                   alpha: float = 0.25) -> AllocationResult:
    """Allocate a charged budget between two independent, resumable searches.

    Both arms use the same initialization seed; their Tabu and D-MAB memories
    remain separate. No arm reads the future outcome of the other arm. The
    protected variant completes uniform Tabu's 3030-evaluation prefix first.
    That full result is retained even if later experiments fail to improve it.
    """
    config = TabuConfig(evaluation_budget=budget)
    if block_size % config.candidates_per_batch:
        raise ValueError("blocks must end at complete candidate-batch boundaries")
    if budget < 2 * config.population_size + 2 * block_size:
        raise ValueError("budget must cover both initializations and warmup blocks")
    arms = [SearchTrajectory(context, seed, mode, config) for mode in ("uniform", "dmab")]
    model = ContextualAllocator(alpha)
    floor = arms[0].best
    if protected:
        arms[0].advance(3030 - arms[0].spent)
        floor = arms[0].best
        if budget < sum(a.spent for a in arms) + 2 * block_size:
            raise ValueError("protected budget must cover the baseline and two warmups")
    decisions: list[dict[str, Any]] = []
    while (total := sum(a.spent for a in arms)) < budget:
        before = min(a.best for a in arms)
        contexts = [a.features(before, total, budget) for a in arms]
        means, scores = model.scores(contexts)
        # Observe each mode once before applying contextual selection.
        arm = len(decisions) if len(decisions) < 2 else int(np.argmax(scores))
        count = min(block_size, budget - total)
        arms[arm].advance(count)
        after = min(a.best for a in arms)
        reward = min(1.0, max(0.0, before - after) / max(1.0, 0.02 * arms[0].initial))
        model.update(arm, contexts[arm], reward)
        decisions.append({
            "block": len(decisions), "arm": ("uniform", "dmab")[arm],
            "evaluations": sum(a.spent for a in arms), "block_evaluations": count,
            "before": before, "after": after, "reward": reward,
            "uniform_mean": means[0], "dmab_mean": means[1],
            "uniform_score": scores[0], "dmab_score": scores[1],
            "uniform_context": contexts[0].tolist(), "dmab_context": contexts[1].tolist(),
        })
    winner = min(arms, key=lambda a: a.best)
    measured = quality(context, winner.best_solution)
    assert math.isclose(measured.objective, winner.best, abs_tol=1e-9)
    if protected:
        assert winner.best <= floor + 1e-9
    return AllocationResult(
        winner.best, copy.deepcopy(winner.best_solution), sum(a.spent for a in arms),
        sum(a.feasible for a in arms), arms[0].spent, arms[1].spent,
        arms[1].bandit.restarts if arms[1].bandit else 0, floor, decisions,
    )
