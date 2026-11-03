"""Deterministic FIFO/SPT/LPT priorities under the strict hospital scheduler."""

from __future__ import annotations

from typing import Any, Literal

from .model import InstanceContext
from .scheduler import greedy_feasible_schedule, schedule_instance_solution


Rule = Literal["fifo", "spt", "lpt"]


def construct_baseline(context: InstanceContext, rule: Rule) -> dict[str, Any]:
    """Choose the earliest feasible completion for each job in rule order.

    SPT and LPT rank by the sum of both processing durations. If the next
    preferred job cannot meet max_wait now, it is deferred until a later step.
    Room pairs are free and the strict simulator verifies the final schedule.
    """
    if rule not in ("fifo", "spt", "lpt"):
        raise ValueError(f"unknown baseline rule: {rule}")
    jobs = {job.job_id: job for job in context.jobs}
    order = [job.job_id for job in context.jobs]
    if rule != "fifo":
        order.sort(key=lambda job_id: (
            sum(op.duration for op in jobs[job_id].operations)
            * (1 if rule == "spt" else -1), job_id
        ))
    solution = greedy_feasible_schedule(context, order)
    if solution is None:
        raise ValueError(f"no feasible completion for {context.instance_id} using {rule}")
    schedule_instance_solution(context, solution)
    return solution


__all__ = ["construct_baseline"]
