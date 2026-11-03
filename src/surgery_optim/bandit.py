"""UCB1 operator selection with optional Page–Hinkley restart."""

from __future__ import annotations

import math


MOVES = ("swap", "insert", "room_1", "room_2", "room_pair")


class DynamicMultiArmedBandit:
    """Non-contextual D-MAB adapted from Da Costa et al. (GECCO 2008).

    The score of an arm is ``mean + C * sqrt(2 ln(total) / count)``. The
    scaling factor ``C`` (``exploration``) is part of the original D-MAB: the
    rewards observed by Tabu are small (median well below 0.1), so with the
    unscaled UCB1 term (``C = 1``) exploration dominates and the controller
    behaves almost like a round-robin over the moves.

    Page–Hinkley resets only the reward estimates, never the Tabu search.
    Each arm starts with one observation before UCB1 scores are compared.
    """

    def __init__(self, *, delta: float = 0.01, threshold: float = 0.35,
                 exploration: float = 1.0, dynamic: bool = True) -> None:
        if delta < 0 or threshold <= 0 or exploration < 0:
            raise ValueError("invalid D-MAB parameters")
        self.delta = delta
        self.threshold = threshold
        self.exploration = exploration
        self.dynamic = dynamic
        self.counts = {action: 0 for action in MOVES}
        self.means = {action: 0.0 for action in MOVES}
        self.cumulative = {action: 0.0 for action in MOVES}
        self.maximum = {action: 0.0 for action in MOVES}
        self.total_choices = {action: 0 for action in MOVES}
        self.restarts = 0

    def score(self, action: str) -> float:
        total = sum(self.counts.values())
        return self.means[action] + self.exploration * math.sqrt(
            2.0 * math.log(total) / self.counts[action]
        )

    def select(self) -> str:
        for action in MOVES:
            if self.counts[action] == 0:
                return action
        return max(MOVES, key=lambda action: (self.score(action), -MOVES.index(action)))

    def update(self, action: str, reward: float) -> bool:
        """Record a reward; return True if Page–Hinkley restarted the bandit.

        The Page–Hinkley statistic accumulates ``reward - mean + delta`` and
        signals a drop in the arm's reward when it falls more than
        ``threshold`` below its running maximum.
        """
        if action not in MOVES or not 0.0 <= reward <= 1.0:
            raise ValueError("unknown action or reward outside [0,1]")
        previous_count = self.counts[action]
        self.counts[action] = previous_count + 1
        self.total_choices[action] += 1
        self.means[action] = (
            previous_count * self.means[action] + reward
        ) / self.counts[action]
        self.cumulative[action] += reward - self.means[action] + self.delta
        self.maximum[action] = max(self.maximum[action], self.cumulative[action])
        if not self.dynamic or self.maximum[action] - self.cumulative[action] <= self.threshold:
            return False
        self.restarts += 1
        for arm in MOVES:
            self.counts[arm] = 0
            self.means[arm] = 0.0
            self.cumulative[arm] = 0.0
            self.maximum[arm] = 0.0
        return True
