"""Task 1 of the Entrega 2 protocol: hardware, software and wall-clock timings.

Runs the fixed portfolio with 6,060 evaluations on the twelve standard
instances, seeds 80-84, one run at a time in a single process:

    python -m experiments.characterize_environment

Quality is deliberately not recorded: this study only measures cost.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from statistics import median

from experiments.entrega2_common import (
    ROOT, SIZES, base_manifest, instance_hashes, prepare_output, standard_paths,
    write_manifest, write_rows,
)
from surgery_optim.instances import load_instance
from surgery_optim.portfolio import run_portfolio


SEEDS = tuple(range(80, 85))
BUDGET = 6060


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_entorno_80_84")
    args = parser.parse_args()
    output = prepare_output(args.output)
    paths = standard_paths()
    manifest = base_manifest("entrega2-entorno-v1", Path(__file__))
    manifest.update({"instance_sha256": instance_hashes(paths), "seeds": SEEDS,
                     "budget": BUDGET, "execution": "sequential, single process"})
    write_manifest(output, manifest)

    rows = []
    for path in paths:
        context = load_instance(path)
        for seed in SEEDS:
            result = run_portfolio(context, seed, BUDGET)
            rows.append({
                "instance_id": context.instance_id, "size": len(context.jobs),
                "seed": seed, "evaluations": result.evaluations,
                "feasible_evaluations": result.feasible_evaluations,
                "runtime_seconds": result.runtime_seconds,
            })
        print(f"{context.instance_id}: completa", flush=True)
    write_rows(output / "timings.csv", rows)

    summary = []
    for size in SIZES:
        times = [row["runtime_seconds"] for row in rows if row["size"] == size]
        summary.append({
            "size": size, "runs": len(times), "median_seconds": median(times),
            "minimum_seconds": min(times), "maximum_seconds": max(times),
            "evaluations_per_second": BUDGET / median(times),
        })
    write_rows(output / "summary.csv", summary)

    hardware = manifest["hardware"]
    software = manifest["software"]
    lines = [
        "# Caracterización del entorno", "",
        f"- CPU: {hardware.get('cpu')}, {hardware.get('cores')} núcleos, "
        f"{hardware.get('threads')} hilos.",
        f"- RAM: {hardware.get('ram_bytes', 0) / 2**30:.1f} GiB.",
        f"- Sistema: {hardware.get('os')}, compilación {hardware.get('os_build')}.",
        f"- Python {software['python']}, NumPy {software['numpy']}, SciPy {software['scipy']}, "
        f"PyYAML {software['pyyaml']}.", "",
        "Tiempo de pared de una cartera de 6.060 evaluaciones. Doce instancias, cinco "
        "semillas (80–84), un solo proceso.", "",
        "| Cirugías | Corridas | Mediana (s) | Mínimo (s) | Máximo (s) | Evaluaciones/s |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(f"| {row['size']} | {row['runs']} | {row['median_seconds']:.2f} | "
                     f"{row['minimum_seconds']:.2f} | {row['maximum_seconds']:.2f} | "
                     f"{row['evaluations_per_second']:.0f} |")
    lines += ["", "El tiempo depende del equipo y de su carga. Estos valores describen "
              "este equipo y no se comparan entre máquinas.", ""]
    (output / "ENTORNO.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print(f"Entorno escrito en {output}")


if __name__ == "__main__":
    main()
