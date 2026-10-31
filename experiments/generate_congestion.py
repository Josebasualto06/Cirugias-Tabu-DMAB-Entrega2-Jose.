"""Generate the declared synthetic congestion catalog of Entrega 2.

Each instance resamples patients from a standard instance of the same size,
perturbs their times, and scales rooms, surgeons and max_wait:

    python -m experiments.generate_congestion --rho-surgeons 0.6 --per-size 12

Anesthetists are unchanged. Surgery setup and transition stay at zero, because a
positive value would create a constant wait that does not measure congestion.
Instances that fail a constructive rule are rejected and redrawn; the count of
rejections is stored with the catalog.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from experiments.entrega2_common import (
    REPLICAS, ROOT, SIZES, base_manifest, instance_hashes, prepare_output, sha256,
    write_manifest,
)
from surgery_optim.baselines import construct_baseline
from surgery_optim.instances import validate_document
from surgery_optim.model import InstanceContext, canonical_digest
from surgery_optim.objective import quality


VERSION = "congestion-v1"
NOISE_SIGMA = 0.10
ELIGIBLE_PEOPLE = 3
RULES = ("fifo", "spt", "lpt")
DEVELOPMENT_SEED = 700_000
CATALOG_SEED = 800_000
RETRY_STRIDE = 1_000


def scaled(count: int, rho: float, minimum: int) -> int:
    return max(minimum, math.ceil(count * rho - 1e-9))


def half_minutes(value: float) -> float:
    return round(value * 2) / 2


def perturb(value: float, rng: np.random.Generator) -> float:
    """Apply multiplicative noise on the 0.5-minute grid; zero stays zero."""
    if value == 0:
        return 0.0
    return max(0.5, half_minutes(value * float(rng.lognormal(0.0, NOISE_SIGMA))))


def base_document(size: int, replica: int) -> dict[str, Any]:
    path = ROOT / f"instances/standard/HOSP-STD-{size}-{replica:02d}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_document(size: int, replica: int, seed: int, instance_id: str, family: str,
                   rho_rooms: float, rho_surgeons: float, rho_wait: float) -> dict[str, Any]:
    """Create one schema-valid document, still without constructive evidence."""
    base = base_document(size, replica)
    rng = np.random.default_rng(seed)
    room_count = scaled(len(base["resources"]["rooms"]), rho_rooms, 2)
    rooms = [f"OR-{index}" for index in range(1, room_count + 1)]
    anesthetists = list(base["resources"]["personnel"]["1"])
    surgeon_count = scaled(len(base["resources"]["personnel"]["2"]), rho_surgeons, ELIGIBLE_PEOPLE)
    surgeons = [f"SU-{index}" for index in range(1, surgeon_count + 1)]

    def people(pool: list[str]) -> list[str]:
        return [str(item) for item in rng.choice(pool, size=ELIGIBLE_PEOPLE, replace=False)]

    jobs = []
    for job_id, row in enumerate(rng.integers(size, size=size).tolist(), 1):
        first, second = base["jobs"][row]["operations"]
        operations = [
            {"id": 1, "duration": perturb(first["duration"], rng),
             "setup": perturb(first["setup"], rng),
             "transition": perturb(first["transition"], rng),
             "cleanup": perturb(first["cleanup"], rng), "max_wait": 0.0,
             "eligible_rooms": list(rooms), "eligible_personnel": people(anesthetists)},
            {"id": 2, "duration": perturb(second["duration"], rng), "setup": 0.0,
             "transition": 0.0, "cleanup": perturb(second["cleanup"], rng),
             "max_wait": perturb(second["max_wait"] * rho_wait, rng),
             "eligible_rooms": list(rooms), "eligible_personnel": people(surgeons)},
        ]
        jobs.append({"id": job_id, "label": f"Congestion case {job_id}", "operations": operations})

    document: dict[str, Any] = {
        "schema_version": 1, "instance_id": instance_id, "family": family,
        "classification": "fully synthetic instance",
        "provenance": {"kind": "public synthetic",
                       "source": f"resampled from HOSP-STD-{size}-{replica:02d}; no patient data"},
        "generation": {
            "method": "patient resampling with resource scaling", "version": VERSION,
            "seed": seed,
            "profile": {
                "duration_distributions": f"standard times times lognormal noise, sigma {NOISE_SIGMA}",
                "dependence": "patient rows resampled whole, preserving stage correlation",
                "assignment": f"{ELIGIBLE_PEOPLE} qualified people drawn per operation",
                "room_eligibility": "all declared rooms",
                "congestion_bands": f"rho_rooms {rho_rooms}, rho_surgeons {rho_surgeons}, "
                                    f"rho_wait {rho_wait}",
                "replica_policy": "independent generation seed per instance",
            },
        },
        "dimensions": {"jobs": size, "operations_per_job": 2},
        "resources": {"rooms": rooms, "personnel": {"1": anesthetists, "2": surgeons}},
        "jobs": jobs,
        "bounds": {"status": "pending", "method_version": "none"},
        "validation": {"method": "schema and constructive feasibility check",
                       "version": VERSION, "outcome": "passed", "evidence": {}},
    }
    document["digest"] = canonical_digest(document)
    return document


def rule_objectives(context: InstanceContext) -> dict[str, float | None]:
    """Objective of each constructive rule; None marks an infeasible rule."""
    results: dict[str, float | None] = {}
    for rule in RULES:
        try:
            results[rule] = quality(context, construct_baseline(context, rule)).objective
        except ValueError:
            results[rule] = None
    return results


def seal(document: dict[str, Any], objectives: dict[str, float | None]) -> dict[str, Any]:
    document["validation"]["evidence"] = {"rule_objectives": objectives}
    document["digest"] = canonical_digest(document)
    return document


def development_document(size: int, rho_rooms: float, rho_surgeons: float,
                         rho_wait: float) -> dict[str, Any]:
    """Tuning instance of one size; these never enter the catalog."""
    replica = REPLICAS[SIZES.index(size) % len(REPLICAS)]
    instance_id = f"HOSP-CONG-DEV-{size}"
    document = build_document(size, replica, DEVELOPMENT_SEED + size, instance_id, "development",
                              rho_rooms, rho_surgeons, rho_wait)
    return seal(document, rule_objectives(validate_document(document)))


def catalog_document(size: int, index: int, rho_rooms: float, rho_surgeons: float,
                     rho_wait: float) -> tuple[dict[str, Any], int]:
    """Draw one catalog instance; return it with its rejected attempts."""
    replica = REPLICAS[(index - 1) % len(REPLICAS)]
    instance_id = f"HOSP-CONG-{size}-{index:02d}"
    base_seed = CATALOG_SEED + 100 * size + index
    for attempt in range(100):
        document = build_document(size, replica, base_seed + RETRY_STRIDE * attempt, instance_id,
                                  "congestion", rho_rooms, rho_surgeons, rho_wait)
        objectives = rule_objectives(validate_document(document))
        if all(value is not None for value in objectives.values()):
            return seal(document, objectives), attempt
    raise RuntimeError(f"{instance_id}: no feasible draw in 100 attempts")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rho-rooms", type=float, required=True)
    parser.add_argument("--rho-surgeons", type=float, required=True)
    parser.add_argument("--rho-wait", type=float, required=True)
    parser.add_argument("--per-size", type=int, required=True)
    parser.add_argument("--directory", type=Path, default=ROOT / "instances/congestion")
    parser.add_argument("--record", type=Path,
                        default=ROOT / "experiments/results/entrega2_catalogo_congestion")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"catalog must not be replaced: {directory}")
    directory.mkdir(parents=True, exist_ok=True)
    record = prepare_output(args.record)

    entries, details = [], []
    for size in SIZES:
        for index in range(1, args.per_size + 1):
            document, rejected = catalog_document(size, index, args.rho_rooms,
                                                  args.rho_surgeons, args.rho_wait)
            path = directory / f"{document['instance_id']}.yaml"
            path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
                            encoding="utf-8")
            entries.append({"file": path.name})
            details.append({
                "instance_id": document["instance_id"], "generation_seed": document["generation"]["seed"],
                "rejected_draws": rejected, "digest": document["digest"], "sha256": sha256(path),
                "rooms": len(document["resources"]["rooms"]),
                "anesthetists": len(document["resources"]["personnel"]["1"]),
                "surgeons": len(document["resources"]["personnel"]["2"]),
            })
    (directory / "metadata.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "instance_count": len(entries), "instances": entries},
                       sort_keys=False), encoding="utf-8")

    manifest = base_manifest("entrega2-catalogo-v1", Path(__file__))
    manifest.update({
        "generator_version": VERSION, "noise_sigma": NOISE_SIGMA,
        "eligible_people": ELIGIBLE_PEOPLE,
        "levers": {"rho_rooms": args.rho_rooms, "rho_surgeons": args.rho_surgeons,
                   "rho_wait": args.rho_wait},
        "per_size": args.per_size, "instances": details,
        "rejected_draws_total": sum(item["rejected_draws"] for item in details),
        "instance_sha256": instance_hashes(directory / f"{item['instance_id']}.yaml"
                                           for item in details),
        "status": "completed",
    })
    write_manifest(record, manifest)
    print(f"{len(details)} instancias en {directory}; "
          f"sorteos rechazados: {manifest['rejected_draws_total']}")


if __name__ == "__main__":
    main()
