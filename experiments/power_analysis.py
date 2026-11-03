"""Task 2 of the Entrega 2 protocol: statistical power from archived differences.

Uses only experiments/results/portfolios_60_79/runs.csv and runs no search:

    python -m experiments.power_analysis

Pairs share instance data, so treating 240 pairs as independent understates the
required sample. The report therefore gives the naive count, the variance
components and a simulation of the test actually used: Wilcoxon on the means
per instance. The simulation resamples the twelve instances and assumes a
homogeneous shift, so results for more instances are an extrapolation.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from scipy.stats import nct, norm, t, wilcoxon

from experiments.entrega2_common import (
    ROOT, base_manifest, prepare_output, read_rows, sha256, write_manifest, write_rows,
)


SOURCE = ROOT / "experiments/results/portfolios_60_79/runs.csv"
COMPARISONS = (
    ("dmab3030", "uniform3030", "D-MAB − Tabu uniforme (3.030)"),
    ("fixed_portfolio6060", "uniform6060", "Cartera − Tabu prolongado (6.060)"),
    ("fixed_portfolio6060", "two_uniform6060", "Cartera − Dos Tabu (6.060)"),
)
PRIMARY = "dmab3030"
EFFECTS = (0.25, 0.65)
POWER = 0.80
ALPHA = 0.05
HOLM_WORST_ALPHA = 0.0125
INSTANCE_LEVELS = (12, 24, 36, 48)
SEEDS_PER_INSTANCE = 20
REPLICATES = 5000
SIMULATION_SEED = 20261102


def t_test_power(n: int, standardized: float, alpha: float) -> float:
    """Power of a two-sided one-sample t test."""
    df = n - 1
    noncentrality = standardized * math.sqrt(n)
    critical = t.ppf(1 - alpha / 2, df)
    return float(1 - nct.cdf(critical, df, noncentrality) + nct.cdf(-critical, df, noncentrality))


def required_n(sd: float, effect: float, alpha: float = ALPHA, power: float = POWER) -> int:
    """Smallest sample of a two-sided t test reaching the requested power."""
    if sd <= 0:
        return 2
    standardized = effect / sd
    n = max(2, int(((norm.ppf(1 - alpha / 2) + norm.ppf(power)) / standardized) ** 2) - 2)
    while t_test_power(n, standardized, alpha) < power:
        n += 1
    return n


def variance_components(matrix: np.ndarray) -> dict[str, float]:
    """One-way random-effects decomposition: instances by seeds."""
    seeds = matrix.shape[1]
    within = float(matrix.var(axis=1, ddof=1).mean())
    between_mean_square = seeds * float(matrix.mean(axis=1).var(ddof=1))
    between = max(0.0, (between_mean_square - within) / seeds)
    icc = between / (between + within) if between + within > 0 else 0.0
    return {"between_variance": between, "within_variance": within, "icc": icc,
            "design_effect": 1 + (seeds - 1) * icc}


def wilcoxon_pvalues(sampled: np.ndarray) -> np.ndarray:
    """Row-wise Wilcoxon p-values, with SciPy's default method for each row.

    SciPy moves a whole array to a permutation test when any row of at most 13
    values has ties or zeros, so tied rows are tested apart from the others.
    """
    magnitudes = np.sort(np.abs(sampled), axis=1)
    tied = (magnitudes[:, 0] == 0) | (magnitudes[:, 1:] == magnitudes[:, :-1]).any(axis=1)
    pvalues = np.empty(len(sampled))
    if (~tied).any():
        pvalues[~tied] = wilcoxon(sampled[~tied], zero_method="zsplit", axis=1,
                                  method="exact").pvalue
    for row in np.flatnonzero(tied):
        pvalues[row] = wilcoxon(sampled[row], zero_method="zsplit").pvalue
    return pvalues


def simulate_rejections(matrix: np.ndarray, effect: float, instances: int, seeds: int,
                        rng: np.random.Generator) -> dict[float, float]:
    """Rejection rate of Wilcoxon on instance means under a shift of ``effect``.

    Observed instance means already contain seed noise, and resampled residuals
    add it again. Means are therefore shrunk to the estimated between-instance
    variance, so a simulated mean has variance between + within / seeds.
    """
    centered = matrix - matrix.mean()
    raw_means = centered.mean(axis=1)
    residuals = centered - raw_means[:, None]
    observed = float(raw_means.var(ddof=1))
    between = variance_components(matrix)["between_variance"]
    means = raw_means * math.sqrt(between / observed) if observed > 0 else raw_means
    picked = rng.integers(matrix.shape[0], size=(REPLICATES, instances))
    drawn = rng.integers(matrix.shape[1], size=(REPLICATES, instances, seeds))
    sampled = means[picked] + residuals[picked[:, :, None], drawn].mean(axis=2) - effect
    pvalues = wilcoxon_pvalues(sampled)
    return {alpha: float(np.mean(pvalues < alpha)) for alpha in (ALPHA, HOLM_WORST_ALPHA)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/results/entrega2_potencia")
    args = parser.parse_args()
    output = prepare_output(args.output)
    manifest = base_manifest("entrega2-potencia-v1", Path(__file__))
    manifest.update({
        "source_runs": "experiments/results/portfolios_60_79/runs.csv",
        "source_runs_sha256": sha256(SOURCE), "effects": EFFECTS, "power": POWER,
        "alpha": ALPHA, "holm_worst_alpha": HOLM_WORST_ALPHA,
        "simulation": {"replicates": REPLICATES, "seed": SIMULATION_SEED,
                       "instance_levels": INSTANCE_LEVELS, "seeds": SEEDS_PER_INSTANCE},
    })
    write_manifest(output, manifest)

    runs = read_rows(SOURCE)
    instances = sorted({row["instance_id"] for row in runs})
    seeds = sorted({int(row["seed"]) for row in runs})
    objective = {(row["instance_id"], int(row["seed"]), row["method"]): float(row["objective"])
                 for row in runs}
    rng = np.random.default_rng(SIMULATION_SEED)
    summary, simulated = [], []
    for method, reference, label in COMPARISONS:
        matrix = np.array([[objective[i, s, method] - objective[i, s, reference] for s in seeds]
                           for i in instances])
        pairs = matrix.size
        sd = float(matrix.std(ddof=1))
        sd_means = float(matrix.mean(axis=1).std(ddof=1))
        components = variance_components(matrix)
        # Pooled estimate of the instance-mean spread; it extends to any seed count.
        sd_design = math.sqrt(components["between_variance"]
                              + components["within_variance"] / len(seeds))
        critical = t.ppf(1 - ALPHA / 2, len(instances) - 1) + t.ppf(POWER, len(instances) - 1)
        for effect in EFFECTS:
            naive = required_n(sd, effect)
            between_sd = math.sqrt(components["between_variance"])
            summary.append({
                "comparison": label, "method": method, "reference": reference,
                "effect": effect, "pairs": pairs, "observed_mean": float(matrix.mean()),
                "sd_difference": sd, "sd_instance_means": sd_means,
                "sd_design": sd_design, **components,
                "effective_pairs": pairs / components["design_effect"],
                "naive_pairs_needed": naive, "naive_ratio_to_current": naive / pairs,
                "naive_pairs_after_design_effect": math.ceil(naive * components["design_effect"]),
                "instances_needed_20_seeds": required_n(sd_design, effect),
                "instances_needed_infinite_seeds": (required_n(between_sd, effect)
                                                    if between_sd > 0 else ""),
                "minimum_detectable_effect_current": float(critical * sd_design
                                                           / math.sqrt(len(instances))),
            })
        for effect in (0.0, *EFFECTS):
            for level in INSTANCE_LEVELS:
                rates = simulate_rejections(matrix, effect, level, SEEDS_PER_INSTANCE, rng)
                simulated.append({
                    "comparison": label, "method": method, "reference": reference,
                    "effect": effect, "instances": level, "seeds": SEEDS_PER_INSTANCE,
                    "rejection_alpha_05": rates[ALPHA],
                    "rejection_alpha_0125": rates[HOLM_WORST_ALPHA],
                })
        print(f"{label}: completa", flush=True)
    write_rows(output / "potencia.csv", summary)
    write_rows(output / "simulacion.csv", simulated)

    primary = [row for row in simulated
               if row["method"] == PRIMARY and row["effect"] == 0.65]
    reaching = [row["instances"] for row in primary if row["rejection_alpha_0125"] >= POWER]
    chosen = min(reaching) if reaching else max(INSTANCE_LEVELS)
    manifest["congestion_instances"] = chosen
    manifest["congestion_power_reached"] = bool(reaching)

    lines = ["# Análisis de potencia estadística", "",
             "Fuente: `portfolios_60_79/runs.csv`, 12 instancias por 20 semillas, 240 pares. "
             "Potencia 0,80 y alfa 0,05 bilateral. Este análisis no ejecuta búsquedas.", "",
             "## Tamaños necesarios", "",
             "| Comparación | Efecto | DE dif. | ICC | Efecto de diseño | Pares si fueran "
             "independientes | Veces 240 | Instancias con 20 semillas | Instancias con semillas infinitas |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary:
        lines.append(
            f"| {row['comparison']} | {row['effect']:.2f} | {row['sd_difference']:.3f} | "
            f"{row['icc']:.3f} | {row['design_effect']:.2f} | {row['naive_pairs_needed']} | "
            f"{row['naive_ratio_to_current']:.1f} | {row['instances_needed_20_seeds']} | "
            f"{row['instances_needed_infinite_seeds'] or 'sin límite estimable'} |")
    lines += ["", "Si la varianza entre instancias se estima en cero, las semillas por sí solas "
              "bastarían y no hay límite estimable en instancias. Esa estimación tiene 11 grados "
              "de libertad y no prueba que la varianza sea nula.", "",
              "## Diseño actual", "",
              "| Comparación | Media observada | DE observada de medias | DE de diseño | "
              "Pares efectivos | Efecto mínimo detectable con 12 instancias |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in summary[::len(EFFECTS)]:
        lines.append(
            f"| {row['comparison']} | {row['observed_mean']:+.3f} | {row['sd_instance_means']:.3f} | "
            f"{row['sd_design']:.3f} | {row['effective_pairs']:.1f} | "
            f"{row['minimum_detectable_effect_current']:.2f} |")
    lines += ["", "La DE de diseño es `sqrt(entre + intra / 20)`. Se usa porque se extiende a otro "
              "número de semillas. Coincide con la DE observada salvo cuando la varianza entre "
              "instancias se trunca en cero."]
    lines += ["", "## Potencia simulada de la prueba real", "",
              f"Wilcoxon sobre medias por instancia, {REPLICATES} réplicas, "
              f"{SEEDS_PER_INSTANCE} semillas. El efecto 0 mide el error tipo I.", "",
              "| Comparación | Efecto | Instancias | Rechazo con alfa 0,05 | Rechazo con alfa 0,0125 |",
              "|---|---:|---:|---:|---:|"]
    for row in simulated:
        lines.append(f"| {row['comparison']} | {row['effect']:.2f} | {row['instances']} | "
                     f"{row['rejection_alpha_05']:.3f} | {row['rejection_alpha_0125']:.3f} |")
    lines += ["", "## Regla para el catálogo de congestión", "",
              f"Regla del protocolo sobre la hipótesis primaria: `I = {chosen}`. "
              + ("La regla alcanza la potencia pedida."
                 if reaching else
                 "Ningún nivel alcanza 0,80 con alfa 0,0125, por lo que el diseño queda "
                 "declarado como subdimensionado."), "",
              "La extrapolación supone instancias nuevas parecidas a las doce observadas y un "
              "efecto homogéneo. La varianza del catálogo de congestión puede ser distinta.", ""]
    (output / "POTENCIA.md").write_text("\n".join(lines), encoding="utf-8")
    manifest["status"] = "completed"
    write_manifest(output, manifest)
    print(f"Potencia escrita en {output}; I={chosen}, alcanzada={bool(reaching)}")


if __name__ == "__main__":
    main()
