"""Decode and validate a candidate schedule for one instance."""

from dataclasses import dataclass
from typing import Any

from .model import InstanceContext


# Numerical tolerance for the max_wait constraint, shared by the scheduler,
# the decoder, the constructive rules and the objective.
WAIT_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    job_id: int
    operation: int
    room: str
    personnel: str
    start: float
    processing_end: float
    finish: float
    setup: float
    transition: float
    cleanup: float


class IneligibleAssignmentError(ValueError):
    """Raised when a candidate names a resource outside operation eligibility."""


def schedule_instance_solution(
    context: InstanceContext, solution: Any
) -> tuple[float, tuple]:
    """Decode one candidate using only the selected instance's immutable data."""
    job_ids = [job.job_id for job in context.jobs]
    if hasattr(solution, "job_sequence_base"):
        sequence = list(solution.job_sequence_base)
        room_assignments = solution.room_assignment
        personnel_assignments = solution.personnel_assignment or {}
    else:
        sequence = list(solution.get("job_sequence_base", ()))
        room_assignments = solution.get("room_assignment", {})
        personnel_assignments = solution.get("personnel_assignment", {})
    if len(sequence) != len(job_ids) or set(sequence) != set(job_ids):
        raise ValueError("job_sequence_base must contain every instance job exactly once")

    room_release = {room: 0.0 for room in context.rooms}
    personnel_release = {
        person: 0.0
        for _, people in context.personnel_by_operation
        for person in people
    }
    jobs = {job.job_id: job for job in context.jobs}
    schedule: list[ScheduleEntry] = []

    for job_id in sequence:
        job = jobs[job_id]
        assignments = room_assignments.get(job_id, {})
        people = personnel_assignments.get(job_id, {})
        resolved: list[tuple[str, str]] = []
        for operation in job.operations:
            room = assignments.get(operation.operation_id)
            if room not in operation.eligible_rooms:
                raise IneligibleAssignmentError(
                    f"job {job_id} operation {operation.operation_id}: "
                    f"ineligible room {room!r}"
                )
            person = people.get(operation.operation_id)
            if person is None:
                person = min(
                    operation.eligible_personnel,
                    key=lambda item: (personnel_release[item], item),
                )
            if person not in operation.eligible_personnel:
                raise IneligibleAssignmentError(
                    f"job {job_id} operation {operation.operation_id}: "
                    f"ineligible personnel {person!r}"
                )
            resolved.append((room, person))

        anesthesia, surgery = job.operations
        room_1, person_1 = resolved[0]
        setup_start = max(room_release[room_1], personnel_release[person_1])
        anesthesia_start = setup_start + max(anesthesia.transition, anesthesia.setup)
        anesthesia_end = anesthesia_start + anesthesia.duration
        anesthesia_finish = anesthesia_end + anesthesia.cleanup

        room_2, person_2 = resolved[1]
        surgery_setup_start = max(
            anesthesia_finish, room_release[room_2], personnel_release[person_2]
        )
        surgery_start = surgery_setup_start + max(surgery.transition, surgery.setup)
        wait = surgery_start - anesthesia_finish
        if wait > surgery.max_wait + WAIT_TOLERANCE:
            raise ValueError(
                f"job {job_id} operation 2 wait {wait} exceeds {surgery.max_wait}"
            )
        surgery_end = surgery_start + surgery.duration
        finish = surgery_end + surgery.cleanup

        schedule.extend(
            (
                ScheduleEntry(
                    job_id,
                    1,
                    room_1,
                    person_1,
                    setup_start,
                    anesthesia_end,
                    anesthesia_finish,
                    anesthesia.setup,
                    anesthesia.transition,
                    anesthesia.cleanup,
                ),
                ScheduleEntry(
                    job_id,
                    2,
                    room_2,
                    person_2,
                    surgery_setup_start,
                    surgery_end,
                    finish,
                    surgery.setup,
                    surgery.transition,
                    surgery.cleanup,
                ),
            )
        )
        # Blocking keeps the anesthesia room occupied until transfer to the
        # surgery room. If both operations use one room, it remains occupied
        # through surgery and cleanup instead.
        room_release[room_1] = finish if room_1 == room_2 else surgery_start
        room_release[room_2] = finish
        personnel_release[person_1] = surgery_start
        personnel_release[person_2] = finish

    makespan = max((entry.finish for entry in schedule), default=0.0)
    return makespan, tuple(schedule)


def greedy_feasible_schedule(
    context: InstanceContext,
    order: list[int],
    preferred_rooms: dict[int, dict[int, str]] | None = None,
) -> dict[str, Any] | None:
    """Build a strict-feasible solution by list scheduling in ``order``.

    At each step the first pending job that admits a room pair respecting
    max_wait is scheduled; infeasible jobs are deferred. Room pairs are
    chosen with the same release rules as ``schedule_instance_solution``:

    * without ``preferred_rooms`` (constructive rules), the earliest finish,
      then the shortest wait;
    * with ``preferred_rooms`` (random-key decoder), the fewest deviations
      from the preferred rooms, then the earliest finish.

    Returns ``None`` when some job cannot be scheduled at all.
    """
    jobs = {job.job_id: job for job in context.jobs}
    room_release = {room: 0.0 for room in context.rooms}
    personnel_release = {
        person: 0.0 for _, people in context.personnel_by_operation for person in people
    }
    pending = list(order)
    sequence: list[int] = []
    assignments: dict[int, dict[int, str]] = {}
    while pending:
        selected = None
        for job_id in pending:
            anesthesia, surgery = jobs[job_id].operations
            person_1 = min(anesthesia.eligible_personnel,
                           key=lambda person: (personnel_release[person], person))
            person_2 = min(surgery.eligible_personnel,
                           key=lambda person: (personnel_release[person], person))
            options = []
            for room_1 in anesthesia.eligible_rooms:
                setup_start = max(room_release[room_1], personnel_release[person_1])
                anesthesia_finish = (
                    setup_start + max(anesthesia.transition, anesthesia.setup)
                    + anesthesia.duration + anesthesia.cleanup
                )
                for room_2 in surgery.eligible_rooms:
                    surgery_setup = max(
                        anesthesia_finish, room_release[room_2], personnel_release[person_2]
                    )
                    surgery_start = surgery_setup + max(surgery.transition, surgery.setup)
                    wait = surgery_start - anesthesia_finish
                    if wait > surgery.max_wait + WAIT_TOLERANCE:
                        continue
                    finish = surgery_start + surgery.duration + surgery.cleanup
                    if preferred_rooms is None:
                        key = (0, finish, wait)
                    else:
                        preferred = preferred_rooms[job_id]
                        deviation = (room_1 != preferred[1]) + (room_2 != preferred[2])
                        key = (deviation, finish, 0.0)
                    options.append((*key, room_1, room_2, surgery_start))
            if options:
                selected = (job_id, person_1, person_2, min(options))
                break
        if selected is None:
            return None
        job_id, person_1, person_2, (_, finish, _, room_1, room_2, surgery_start) = selected
        pending.remove(job_id)
        sequence.append(job_id)
        assignments[job_id] = {1: room_1, 2: room_2}
        room_release[room_1] = finish if room_1 == room_2 else surgery_start
        room_release[room_2] = finish
        personnel_release[person_1] = surgery_start
        personnel_release[person_2] = finish
    return {"job_sequence_base": sequence, "room_assignment": assignments}
