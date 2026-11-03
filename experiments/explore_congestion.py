"""Post-hoc, exploratory reading of the finished congestion study.

Nothing here was pre-registered and no search is executed. It computes what the
protocol did not foresee: UCB1 against uniform Tabu, the power implied by the
variance actually observed, and the share of waiting solutions per size:

    python -m experiments.explore_congestion

These results stay out of the confirmatory family C1-C4 and need fresh seeds.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from experiments.entrega2_common import (
    ROOT, SIZES, base_manifest, prepare_output, read_rows, sha256, write_manifest, write_rows,
)
from experiments.power_analysis import required_n, t_test_power, variance_components
from experiments.study_congestion import clustered_interval


SOURCE = ROOT / "experiments/results/entrega2_congestion_90_109/runs.csv"
BOOTSTRAP_SEED = 20261103
EFFECTS = (0.25, 0.65)
ASSUMED_SD = 7.034


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_exploratorio")
    args = parser.parse_args()
    output = prepare_output(args.output)
    manifest = base_manifest("entrega2-exploratorio-v1", Path(__file__))
    manifest.update({"status_note": "post-hoc; not pre-registered",
                     "source_runs_sha256": sha256(SOURCE), "bootstrap_seed": BOOTSTRAP_SEED})
    write_manifest(output, manifest)

    rows = read_rows(SOURCE)
    objective = {(r["instance_id"], int(r["seed"]), r["method"]): float(r["objective"]) for r in rows}
    instances = sorted({r["instance_id"] for r in rows})
    seeds = sorted({int(r["seed"]) for r in rows})

    def matrix(method: str, reference: str) -> np.ndarray:
        return np.array([[objective[i, s, method] - objective[i, s, reference] for s in seeds]
                         for i in instances])

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    contrasts = []
    for method, reference, label in (("ucb3030", "uniform3030", "UCB1 − Tabu uniforme (3.030)"),):
        data = matrix(method, reference)
        means = data.mean(axis=1)
        low, high = clustered_interval(list(data), rng)
        contrasts.append({
            "contrast": label, "pairs": data.size, "mean_difference": float(data.mean()),
            "ci_low": low, "ci_high": high,
            "wilcoxon_p_uncorrected": float(wilcoxon(means, zero_method="zsplit").pvalue),
            "instances_better": int((means < -1e-9).sum()),
            "instances_worse": int((means > 1e-9).sum()),
        })
    write_rows(output / "contrastes.csv", contrasts)

    primary = matrix("dmab3030", "uniform3030")
    components = variance_components(primary)
    sd = float(primary.std(ddof=1))
    sd_design = math.sqrt(components["between_variance"]
                          + components["within_variance"] / len(seeds))
    power = []
    for effect in EFFECTS:
        power.append({
            "effect": effect, "assumed_sd": ASSUMED_SD, "realized_sd": sd,
            "realized_sd_design": sd_design, "instances": len(instances),
            "t_power_alpha_05": t_test_power(len(instances), effect / sd_design, 0.05),
            "t_power_alpha_0125": t_test_power(len(instances), effect / sd_design, 0.0125),
            "pairs_needed_realized_sd": required_n(sd, effect),
        })
    write_rows(output / "potencia_realizada.csv", power)

    waiting = []
    for size in SIZES:
        current = [r for r in rows if int(r["size"]) == size
                   and r["method"] in ("uniform3030", "dmab3030")]
        waiting.append({"size": size, "solutions": len(current),
                        "waiting_share": float(np.mean([float(r["blocked"]) > 0 for r in current])),
                        "mean_blocked": float(np.mean([float(r["blocked"]) for r in current]))})
    current = [r for r in rows if r["method"] in ("uniform3030", "dmab3030")]
    waiting.append({"size": "todas", "solutions": len(current),
                    "waiting_share": float(np.mean([float(r["blocked"]) > 0 for r in current])),
                    "mean_blocked": float(np.mean([float(r["blocked"]) for r in current]))})
    write_rows(output / "espera_por_tamano.csv", waiting)

    lines = ["# Lectura exploratoria del estudio de congestión", "",
             "**No estaba pre-registrada.** No integra la familia C1–C4, no corrige por "
             "comparaciones múltiples y necesita semillas nuevas para confirmarse.", "",
             "## Contraste fuera de la familia", "",
             "| Contraste | Pares | Media dif. | IC 95 % agrupado | Instancias mejor / peor | "
             "p sin corregir |", "|---|---:|---:|---|---|---:|"]
    for row in contrasts:
        lines.append(f"| {row['contrast']} | {row['pairs']} | {row['mean_difference']:+.3f} | "
                     f"[{row['ci_low']:+.3f}, {row['ci_high']:+.3f}] | {row['instances_better']} / "
                     f"{row['instances_worse']} | {row['wilcoxon_p_uncorrected']:.4f} |")
    lines += ["", "## Potencia con la variabilidad observada en C1", "",
              f"La potencia del protocolo supuso DE {ASSUMED_SD:.3f}. La DE observada en congestión "
              f"fue {sd:.3f}. Aproximación t sobre medias por instancia, con DE de diseño "
              f"{sd_design:.3f}.", "",
              "| Efecto | Potencia con alfa 0,05 | Potencia con alfa 0,0125 | Pares necesarios |",
              "|---:|---:|---:|---:|"]
    for row in power:
        lines.append(f"| {row['effect']:.2f} | {row['t_power_alpha_05']:.2f} | "
                     f"{row['t_power_alpha_0125']:.2f} | {row['pairs_needed_realized_sd']} |")
    lines += ["", "## Soluciones finales con espera", "",
              "Tabu uniforme y D-MAB, 3.030 evaluaciones.", "",
              "| Cirugías | Soluciones | Con espera | Espera total media |", "|---|---:|---:|---:|"]
    for row in waiting:
        lines.append(f"| {row['size']} | {row['solutions']} | {row['waiting_share']:.1%} | "
                     f"{row['mean_blocked']:.2f} |")
    lines.append("")
    (output / "EXPLORATORIO.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
