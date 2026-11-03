"""Strict feasibility and the predeclared quality measures."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .model import InstanceContext
from .scheduler import WAIT_TOLERANCE, schedule_instance_solution


ALPHA = 1.0e-6
BETA = 0.5
GAMMA = 1.4


@dataclass(frozen=True, slots=True)
class Quality:
    objective: float
    makespan: float
    blocked_minutes: float
    max_wait_minutes: float
    cross_room_jobs: int


def quality(context: InstanceContext, solution: dict[str, Any]) -> Quality:
    """Evaluate f=Cmax+alpha Σ starts+beta Σ waits+gamma max(wait).

    Every operation is scheduled by the strict scheduler. Ineligible rooms or
    violation of a surgery's max_wait raises ValueError. There is no room
    balance penalty.
    """
    makespan, schedule = schedule_instance_solution(context, solution)
    if len(schedule) != 2 * len(context.jobs):
        raise ValueError("incomplete schedule")
    by_job: dict[int, dict[int, Any]] = defaultdict(dict)
    for entry in schedule:
        by_job[entry.job_id][entry.operation] = entry
    waits = []
    for job in context.jobs:
        first, second = by_job[job.job_id][1], by_job[job.job_id][2]
        surgery_start = second.start + max(second.transition, second.setup)
        wait = max(0.0, surgery_start - first.finish)
        if wait > job.operations[1].max_wait + WAIT_TOLERANCE:
            raise ValueError("max_wait violation")
        waits.append(wait)
    blocked = sum(waits)
    max_wait = max(waits, default=0.0)
    total_start = sum(entry.start for entry in schedule)
    objective = makespan + ALPHA * total_start + BETA * blocked + GAMMA * max_wait
    cross_room = sum(
        pair[1] != pair[2] for pair in solution["room_assignment"].values()
    )
    return Quality(objective, makespan, blocked, max_wait, cross_room)
