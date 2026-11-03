from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import pytest

from surgery_optim import TabuConfig, load_instance, run_tabu
from surgery_optim.baselines import construct_baseline
from surgery_optim.bandit import DynamicMultiArmedBandit
from surgery_optim.model import InstanceContext, Job, Operation
from surgery_optim.objective import quality
from surgery_optim.scheduler import IneligibleAssignmentError, schedule_instance_solution


ROOT = Path(__file__).resolve().parents[1]


def test_strict_scheduler_rejects_max_wait_violation() -> None:
    rooms = ("A", "B")
    first = Job(1, "", (
        Operation(1, 1, 0, 0, 0, 100, rooms, ("anesthetist",)),
        Operation(2, 100, 0, 0, 0, 1, rooms, ("surgeon",)),
    ))
    second = Job(2, "", (
        Operation(1, 1, 0, 0, 0, 100, rooms, ("anesthetist",)),
        Operation(2, 1, 0, 0, 0, 1, rooms, ("surgeon",)),
    ))
    context = InstanceContext(1, "toy", "test", "fully synthetic instance", 0,
                              rooms, ((1, ("anesthetist",)), (2, ("surgeon",))),
                              (first, second), "0" * 64)
    solution = {"job_sequence_base": [1, 2],
                "room_assignment": {1: {1: "A", 2: "A"}, 2: {1: "B", 2: "A"}}}
    with pytest.raises(ValueError, match="exceeds"):
        schedule_instance_solution(context, solution)


def test_matched_initialization_feasibility_and_reproducibility() -> None:
    context = load_instance(ROOT / "instances/standard/HOSP-STD-20-01.yaml")
    config = TabuConfig(population_size=12, evaluation_budget=72,
                        candidates_per_batch=6)
    results = {policy: run_tabu(context, 20, policy, config)
               for policy in ("uniform", "dmab", "ucb")}
    assert len({result.initial_objective for result in results.values()}) == 1
    for result in results.values():
        assert result.evaluations == result.feasible_evaluations == 72
        measured = quality(context, result.best_solution)
        assert math.isclose(measured.objective, result.final_quality.objective)
        assert all(result.trace[i]["best_objective"] <= result.trace[i - 1]["best_objective"]
                   for i in range(1, len(result.trace)))
    assert results["ucb"].dmab_restarts == 0
    repeat = run_tabu(context, 20, "dmab", config)
    assert repeat.best_solution == results["dmab"].best_solution
    assert repeat.final_quality == results["dmab"].final_quality
    assert repeat.evaluated_choices == results["dmab"].evaluated_choices


def test_constructive_rules_are_feasible_and_distinct_rooms_allowed() -> None:
    context = load_instance(ROOT / "instances/standard/HOSP-STD-15-01.yaml")
    for rule in ("fifo", "spt", "lpt"):
        solution = construct_baseline(context, rule)
        assert len(schedule_instance_solution(context, solution)[1]) == 30
        assert quality(context, solution).cross_room_jobs > 0


def test_historical_parity_for_known_seed_zero() -> None:
    """Regression values from the exploratory 20-seed study, not its files.

    ``TabuConfig.entrega1()`` must keep reproducing the Entrega 1 search.
    """
    context = load_instance(ROOT / "instances/standard/HOSP-STD-15-01.yaml")
    expected = {"uniform": 145.5015295, "dmab": 140.5015795}
    for policy, target in expected.items():
        result = run_tabu(context, 0, policy, TabuConfig.entrega1())
        assert result.initial_objective == 147.5017585
        assert math.isclose(result.final_quality.objective, target, abs_tol=1e-9)


def test_page_hinkley_restarts_after_reward_drop_but_ucb_does_not() -> None:
    dynamic = DynamicMultiArmedBandit(delta=0.01, threshold=0.35)
    static = DynamicMultiArmedBandit(delta=0.01, threshold=0.35, dynamic=False)
    for reward in [1.0] * 20 + [0.0] * 20:
        dynamic.update("swap", reward)
        static.update("swap", reward)
    assert dynamic.restarts >= 1
    assert static.restarts == 0


def test_anesthesia_room_and_personnel_remain_reserved_until_transfer() -> None:
    rooms = ("A", "B", "C")
    first = Job(1, "", (
        Operation(1, 1, 0, 0, 0, 20, rooms, ("a1", "a2")),
        Operation(2, 1, 0, 10, 0, 20, rooms, ("surgeon",)),
    ))
    second = Job(2, "", (
        Operation(1, 1, 0, 0, 0, 20, rooms, ("a1", "a2")),
        Operation(2, 1, 0, 0, 0, 20, rooms, ("surgeon",)),
    ))
    context = InstanceContext(1, "blocking-toy", "test", "fully synthetic instance", 0,
                              rooms, ((1, ("a1", "a2")), (2, ("surgeon",))),
                              (first, second), "0" * 64)
    room_case = {"job_sequence_base": [1, 2],
                 "room_assignment": {1: {1: "A", 2: "B"}, 2: {1: "A", 2: "C"}}}
    _, schedule = schedule_instance_solution(context, room_case)
    entries = {(entry.job_id, entry.operation): entry for entry in schedule}
    assert entries[1, 1].finish == 1
    assert entries[1, 2].start == 1
    assert entries[2, 1].start == 11  # A held until surgery actually begins.
    assert entries[1, 1].personnel == "a1"
    assert entries[2, 1].personnel == "a2"  # Free colleague isolates room blocking.

    only_a1 = replace(context, jobs=(
        replace(first, operations=(replace(first.operations[0],
                                           eligible_personnel=("a1",)), first.operations[1])),
        replace(second, operations=(replace(second.operations[0],
                                            eligible_personnel=("a1",)), second.operations[1])),
    ))
    personnel_case = {"job_sequence_base": [1, 2],
                      "room_assignment": {1: {1: "A", 2: "B"}, 2: {1: "C", 2: "C"}}}
    _, schedule = schedule_instance_solution(only_a1, personnel_case)
    entries = {(entry.job_id, entry.operation): entry for entry in schedule}
    assert entries[2, 1].start == 11  # C is free; a1 is held until transfer.

    bad_room = {"job_sequence_base": [1, 2],
                "room_assignment": {1: {1: "Z", 2: "B"}, 2: {1: "C", 2: "C"}}}
    with pytest.raises(IneligibleAssignmentError):
        schedule_instance_solution(context, bad_room)
    bad_person = {**room_case,
                  "personnel_assignment": {1: {1: "unqualified"}}}
    with pytest.raises(IneligibleAssignmentError):
        schedule_instance_solution(context, bad_person)


def test_exploration_scale_lets_small_rewards_drive_selection() -> None:
    """With C=1 the UCB term swamps rewards of ~0.02; a small C exploits them."""
    def pulls(exploration: float) -> int:
        bandit = DynamicMultiArmedBandit(exploration=exploration, dynamic=False)
        for _ in range(500):
            arm = bandit.select()
            bandit.update(arm, 0.04 if arm == "insert" else 0.0)
        return bandit.total_choices["insert"]
    assert pulls(1.0) < 200          # close to round-robin (100 each)
    assert pulls(0.01) > 400         # the rewarding move dominates


def test_neighbor_shares_random_stream_across_policies() -> None:
    import random
    from surgery_optim.tabu import neighbor
    context = load_instance(ROOT / "instances/standard/HOSP-STD-15-01.yaml")
    solution = construct_baseline(context, "fifo")
    targets = set()
    for move in (None, "swap", "insert", "room_1", "room_2", "room_pair"):
        rng = random.Random(7)
        _, target, applied = neighbor(solution, context, rng, [], move)
        targets.add(target)
        assert move is None or applied == move
    assert len(targets) == 1


def test_decoder_and_rules_respect_strict_scheduler_and_catalog_loads() -> None:
    import numpy as np
    from surgery_optim.encoding import decode_feasible
    from surgery_optim.instances import load_catalog
    catalog = load_catalog(ROOT / "instances/standard")
    assert len(catalog) == 12
    rng = np.random.default_rng(0)
    for context in catalog:
        dimension = len(context.jobs) * 3
        for _ in range(5):
            solution = decode_feasible(rng.uniform(-5, 5, dimension), context)
            assert math.isfinite(quality(context, solution).objective)


def test_attribute_tabu_memory_is_reproducible_and_config_round_trips() -> None:
    context = load_instance(ROOT / "instances/standard/HOSP-STD-15-02.yaml")
    config = TabuConfig(evaluation_budget=90, exploration=0.05, tabu_memory="attribute")
    first = run_tabu(context, 3, "dmab", config)
    second = run_tabu(context, 3, "dmab", config)
    assert first.final_quality == second.final_quality
    assert first.repaired_candidates == second.repaired_candidates
    legacy = TabuConfig.from_manifest({"population_size": 30, "evaluation_budget": 3030,
                                       "candidates_per_batch": 15, "tabu_tenure": 7,
                                       "ph_delta": 0.01, "ph_lambda": 0.35})
    assert legacy == TabuConfig.entrega1()
