"""Validate and compare completed local/Colab CPU smoke-test records.

This command only analyzes recorded searches. It does not run optimization.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("TS-U", "TS-DMAB")
SIZES = (15, 20, 25, 30)
SEEDS = tuple(range(2100, 2105))
TOLERANCE = 1e-9
KEY = ("instance_id", "seed", "method")
QUALITY = ("initial_objective", "objective", "makespan", "total_wait", "max_wait")
EXPECTED_CONFIG = {
    "population_size": 30, "evaluation_budget": 6060,
    "candidates_per_batch": 15, "tabu_tenure": 7,
    "ph_delta": 0.01, "ph_lambda": 1.0, "exploration": 0.1,
    "tabu_memory": "solution", "common_random_numbers": True,
}
INTEGER = (
    "jobs", "seed", "order_in_pair", "evaluations", "feasible_evaluations",
    "dmab_restarts", "repaired_candidates",
)
FLOATS = ("wall_seconds", "cpu_seconds", "engine_seconds", *QUALITY)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def relative(path: Path, base: Path = ROOT) -> str:
    return os.path.relpath(path, base).replace(os.sep, "/")


def quality_digest(rows: list[dict]) -> str:
    columns = (*KEY, "evaluations", *QUALITY)
    payload = [
        {column: row[column] for column in columns}
        for row in sorted(rows, key=lambda row: tuple(row[k] for k in KEY))
    ]
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()).hexdigest()


def load_completed(folder: Path, label: str) -> dict:
    manifest = read_json(folder / "manifest.json")
    summary = read_json(folder / "summary.json")
    require(manifest.get("state") == summary.get("state") == "completed",
            f"{label}: se requiere una ejecución completa.")
    require(manifest.get("label") == summary.get("label") == label,
            f"{label}: etiqueta incorrecta.")
    require(manifest.get("benchmark") == "OII464-local-colab-cpu-smoke-v1",
            f"{label}: protocolo smoke desconocido.")
    require(manifest.get("seeds") == list(SEEDS), f"{label}: semillas diferentes.")
    require(manifest.get("warmup_seed") == 2199, f"{label}: calentamiento diferente.")
    require(manifest.get("runs_planned") == 120, f"{label}: plan distinto de 120 corridas.")
    require(manifest.get("config") == EXPECTED_CONFIG,
            f"{label}: configuración diferente del smoke predefinido.")
    instance_hashes = manifest.get("instance_sha256", {})
    require(len(instance_hashes) == 12, f"{label}: inventario diferente de doce instancias.")
    expected_ids = {
        f"HOSP-STD-{size}-{replica:02d}"
        for size in SIZES for replica in (1, 2, 3)
    }
    require({Path(name).stem for name in instance_hashes} == expected_ids,
            f"{label}: catálogo de instancias incorrecto.")
    with (folder / "runs.csv").open(newline="", encoding="utf-8") as stream:
        rows = []
        for record in csv.DictReader(stream):
            row = dict(record)
            for column in INTEGER:
                row[column] = int(record[column])
            for column in FLOATS:
                row[column] = float(record[column])
                require(math.isfinite(row[column]), f"{label}: {column} no finito.")
            require(row["status"] == "valid", f"{label}: corrida no válida.")
            require(row["evaluations"] == row["feasible_evaluations"] == 6060,
                    f"{label}: presupuesto o factibilidad incompletos.")
            require(row["wall_seconds"] > 0 and row["cpu_seconds"] > 0,
                    f"{label}: duración no positiva.")
            require(row["jobs"] == int(row["instance_id"].split("-")[2]),
                    f"{label}: tamaño incorrecto.")
            require(row["policy"] == {"TS-U": "uniform", "TS-DMAB": "dmab"}.get(row["method"]),
                    f"{label}: política y sigla no coinciden.")
            require(row["order_in_pair"] in (1, 2), f"{label}: orden incorrecto.")
            require(row["objective"] <= row["initial_objective"] + TOLERANCE,
                    f"{label}: el mejor global empeora respecto del inicio.")
            rows.append(row)
    expected_keys = {
        (instance_id, seed, method)
        for instance_id in expected_ids for seed in SEEDS for method in METHODS
    }
    keys = [tuple(row[column] for column in KEY) for row in rows]
    require(len(rows) == len(set(keys)) == 120 and set(keys) == expected_keys,
            f"{label}: faltantes, duplicados o corridas adicionales.")
    by_key = {key: row for key, row in zip(keys, rows)}
    for instance_id in expected_ids:
        for seed in SEEDS:
            first = by_key[instance_id, seed, "TS-U"]
            second = by_key[instance_id, seed, "TS-DMAB"]
            require({first["order_in_pair"], second["order_in_pair"]} == {1, 2},
                    f"{label}: orden de pareja repetido.")
            require(abs(first["initial_objective"] - second["initial_objective"]) <= TOLERANCE,
                    f"{label}: inicio no compartido entre métodos.")
    wall = sum(row["wall_seconds"] for row in rows)
    cpu = sum(row["cpu_seconds"] for row in rows)
    require(summary.get("runs") == 120, f"{label}: resumen incompleto.")
    require(summary.get("candidate_evaluations") == 727200,
            f"{label}: total de evaluaciones incorrecto.")
    require(math.isclose(wall, summary["search_wall_seconds"], rel_tol=1e-12, abs_tol=1e-6),
            f"{label}: total de pared no coincide con CSV.")
    require(math.isclose(cpu, summary["search_cpu_seconds"], rel_tol=1e-12, abs_tol=1e-6),
            f"{label}: total CPU no coincide con CSV.")
    require(summary["loop_wall_seconds"] + 1e-6 >= wall,
            f"{label}: el bucle dura menos que sus búsquedas.")
    require(summary.get("quality_sha256") == quality_digest(rows),
            f"{label}: huella de métricas no coincide con CSV.")
    require(summary.get("hardware") == manifest.get("hardware")
            and summary.get("versions") == manifest.get("versions"),
            f"{label}: entorno de manifiesto y resumen no coincide.")
    return {
        "folder": folder, "manifest": manifest, "summary": summary,
        "rows": rows, "by_key": by_key, "wall": wall, "cpu": cpu,
    }


def aggregate(local: dict, colab: dict) -> list[dict]:
    records = []
    for method in METHODS:
        for size in SIZES:
            lrows = [r for r in local["rows"] if r["method"] == method and r["jobs"] == size]
            crows = [r for r in colab["rows"] if r["method"] == method and r["jobs"] == size]
            ls = sum(r["wall_seconds"] for r in lrows)
            cs = sum(r["wall_seconds"] for r in crows)
            records.append({
                "method": method, "jobs": size, "runs_per_environment": len(lrows),
                "local_wall_seconds": ls, "colab_wall_seconds": cs,
                "local_mean_seconds": statistics.mean(r["wall_seconds"] for r in lrows),
                "colab_mean_seconds": statistics.mean(r["wall_seconds"] for r in crows),
                "local_median_seconds": statistics.median(r["wall_seconds"] for r in lrows),
                "colab_median_seconds": statistics.median(r["wall_seconds"] for r in crows),
                "colab_over_local_ratio": cs / ls,
            })
    return records


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def chart(output: Path, local: dict, colab: dict, groups: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    import numpy as np

    labels = ("Mac local", "Colab CPU")
    colors = ("#215A8A", "#D9A33B")
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    totals = [local["wall"] / 60, colab["wall"] / 60]
    bars = axes[0].bar(labels, totals, color=colors, edgecolor="#333333", linewidth=.7)
    bars[1].set_hatch("///")
    axes[0].bar_label(bars, fmt="%.2f", padding=4)
    axes[0].set_title("Total de las 120 corridas")
    axes[0].set_ylabel("Tiempo de búsqueda (minutos)")
    axes[0].set_ylim(0, max(totals) * 1.2)
    x = np.arange(2)
    width = .35
    for environment, label, color, offset, hatch in (
        ("local", labels[0], colors[0], -width / 2, None),
        ("colab", labels[1], colors[1], width / 2, "///"),
    ):
        values = [
            sum(g[f"{environment}_wall_seconds"] for g in groups if g["method"] == method) / 60
            for method in METHODS
        ]
        b = axes[1].bar(x + offset, values, width, label=label, color=color,
                        hatch=hatch, edgecolor="#333333", linewidth=.7)
        axes[1].bar_label(b, fmt="%.2f", padding=3, fontsize=10)
    axes[1].set_xticks(x, METHODS)
    axes[1].set_title("Por método · 60 corridas")
    axes[1].set_ylabel("Tiempo de búsqueda (minutos)")
    axes[1].set_ylim(0, max(
        sum(g[f"{env}_wall_seconds"] for g in groups if g["method"] == method) / 60
        for env in ("local", "colab") for method in METHODS
    ) * 1.25)
    axes[1].legend(frameon=False, loc="upper left")
    x = np.arange(4)
    for environment, label, color, offset, hatch in (
        ("local", labels[0], colors[0], -width / 2, None),
        ("colab", labels[1], colors[1], width / 2, "///"),
    ):
        values = [
            sum(g[f"{environment}_wall_seconds"] for g in groups if g["jobs"] == size) / 60
            for size in SIZES
        ]
        b = axes[2].bar(x + offset, values, width, label=label, color=color,
                        hatch=hatch, edgecolor="#333333", linewidth=.7)
        axes[2].bar_label(b, fmt="%.2f", padding=3, fontsize=9)
    axes[2].set_xticks(x, [str(n) for n in SIZES])
    axes[2].set_xlabel("Cirugías por instancia")
    axes[2].set_ylabel("Tiempo de búsqueda (minutos)")
    axes[2].set_title("Por tamaño · 30 corridas")
    axes[2].set_ylim(0, max(
        sum(g[f"{env}_wall_seconds"] for g in groups if g["jobs"] == size) / 60
        for env in ("local", "colab") for size in SIZES
    ) * 1.25)
    for ax in axes:
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color="#E5E5E5", linewidth=.7)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Prueba de tiempos: mismo código, instancias y presupuesto", fontsize=14)
    fig.savefig(output / "tiempos_smoke.png", dpi=180, facecolor="white")
    plt.close(fig)


def clock(seconds: float) -> str:
    return f"{seconds:.2f} s ({seconds / 60:.2f} min)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--colab", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--colab-context",
        default="CPU estándar en cuenta Pro, según registro de la ejecución.",
        help="Contexto observado de Colab; no implica un efecto causal del plan.",
    )
    args = parser.parse_args()
    local = load_completed(args.local.resolve(), "local")
    colab = load_completed(args.colab.resolve(), "colab")
    for field in ("benchmark", "config", "seeds", "warmup_seed", "runs_planned",
                  "code_sha256", "instance_sha256"):
        require(local["manifest"].get(field) == colab["manifest"].get(field),
                f"Comparación inválida: {field} difiere entre entornos.")
    for package in ("numpy", "PyYAML"):
        require(local["manifest"]["versions"].get(package)
                == colab["manifest"]["versions"].get(package),
                f"Comparación inválida: versión de {package} diferente.")
    # Check current source bytes when this tool is run from the matching project.
    for field in ("code_sha256", "instance_sha256"):
        for name, expected in local["manifest"][field].items():
            require((ROOT / name).is_file() and sha(ROOT / name) == expected,
                    f"El archivo del proyecto no coincide con la evidencia: {name}")
    paired = []
    max_differences = {metric: 0.0 for metric in QUALITY}
    mismatching_pairs = 0
    for key in sorted(local["by_key"]):
        left, right = local["by_key"][key], colab["by_key"][key]
        match = True
        record = {column: left[column] for column in KEY}
        record["jobs"] = left["jobs"]
        for column in ("wall_seconds", "cpu_seconds"):
            record[f"local_{column}"] = left[column]
            record[f"colab_{column}"] = right[column]
        record["colab_over_local_ratio"] = right["wall_seconds"] / left["wall_seconds"]
        for column in QUALITY:
            difference = abs(right[column] - left[column])
            max_differences[column] = max(max_differences[column], difference)
            match = match and difference <= TOLERANCE
            record[f"local_{column}"] = left[column]
            record[f"colab_{column}"] = right[column]
            record[f"absolute_difference_{column}"] = difference
        record["quality_matches_1e_9"] = match
        mismatching_pairs += not match
        paired.append(record)
    groups = aggregate(local, colab)
    versions = {
        package: {"local": local["manifest"]["versions"].get(package),
                  "colab": colab["manifest"]["versions"].get(package)}
        for package in sorted(
            set(local["manifest"]["versions"]) | set(colab["manifest"]["versions"])
        )
        if local["manifest"]["versions"].get(package)
        != colab["manifest"]["versions"].get(package)
    }
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    observations = {}
    for label, item in (("local", local), ("colab", colab)):
        observations[label] = {
            "runs": 120,
            "search_wall_seconds": item["wall"],
            "search_cpu_seconds": item["cpu"],
            "loop_wall_seconds": item["summary"]["loop_wall_seconds"],
            "setup_seconds": item["summary"]["setup_seconds"],
            "warmup_seconds": item["summary"]["warmup_seconds"],
            "setup_warmup_loop_seconds": sum(item["summary"][k] for k in (
                "setup_seconds", "warmup_seconds", "loop_wall_seconds"
            )),
            "method_wall_seconds": {
                method: sum(r["wall_seconds"] for r in item["rows"] if r["method"] == method)
                for method in METHODS
            },
            "hardware": item["manifest"]["hardware"],
            "versions": item["manifest"]["versions"],
        }
    result = {
        "comparison": "OII464-local-colab-cpu-smoke-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "state": "completed_analysis",
        "scope": "One completed sequential CPU smoke run per environment, not a causal comparison of operating systems, processors or Colab account plans.",
        "colab_context": args.colab_context,
        "observed": observations,
        "colab_over_local_wall_ratio": colab["wall"] / local["wall"],
        "colab_wall_percent_difference": 100 * (colab["wall"] / local["wall"] - 1),
        "paired_quality": {
            "pairs": len(paired), "tolerance": TOLERANCE,
            "matching_pairs": len(paired) - mismatching_pairs,
            "mismatching_pairs": mismatching_pairs,
            "maximum_absolute_differences": max_differences,
            "exact_quality_digest_match":
                local["summary"]["quality_sha256"] == colab["summary"]["quality_sha256"],
        },
        "comparability": {
            "same_code_hashes": True, "same_instance_hashes": True,
            "same_config": True, "same_seeds": True,
            "same_numpy_and_pyyaml": True,
            "package_version_differences": versions,
            "calendar_validation": "Final strict validation performed by run_tabu in each recorded run; calendars were not independently revalidated by this comparison command.",
        },
        "groups": groups,
        "estimates_not_observed": {
            label: {
                "main_720_search_seconds": item["wall"] * 6,
                "secondary_720_nominal_search_seconds": 7200,
                "main_plus_secondary_nominal_search_seconds": item["wall"] * 6 + 7200,
                "assumption": "Six times the 120-run smoke search total, same instance mix and approximately stable throughput; add 720*10 seconds for the separate timed campaign. Excludes installation, analysis, storage, atomic deadline overrun and validation overhead of the timed runner.",
            } for label, item in (("local", local), ("colab", colab))
        },
        "sources": {
            label: {
                "directory": relative(item["folder"]),
                "files_sha256": {
                    name: sha(item["folder"] / name)
                    for name in ("manifest.json", "summary.json", "runs.csv", "solutions.json")
                },
            } for label, item in (("local", local), ("colab", colab))
        },
    }
    write_csv(output / "comparison.csv", paired)
    write_csv(output / "timing_summary.csv", groups)
    write_json(output / "comparison.json", result)
    chart(output, local, colab, groups)
    lines = [
        "# Comparación de tiempos: Mac local y Colab CPU", "",
        "Prueba completada: doce instancias, cinco semillas (2100-2104), dos métodos",
        "y 6.060 evaluaciones por corrida. Son 120 corridas y 727.200 evaluaciones",
        "en cada entorno. Las dos búsquedas se ejecutaron secuencialmente.", "",
        f"**Contexto de Colab:** {args.colab_context}",
        "Esta observación no mide el efecto de pagar Pro ni garantiza el rendimiento",
        "de otra sesión gratuita o de pago.", "",
        "| Entorno | Búsquedas observadas | Bucle, incluida escritura | Preparación + calentamiento + bucle |",
        "|---|---:|---:|---:|",
    ]
    for label, name in (("local", "Mac local"), ("colab", "Colab CPU")):
        obs = observations[label]
        lines.append(
            f"| {name} | {clock(obs['search_wall_seconds'])} | "
            f"{clock(obs['loop_wall_seconds'])} | {clock(obs['setup_warmup_loop_seconds'])} |"
        )
    lines += [
        "",
        f"El cociente Colab/local del tiempo total de búsqueda fue **{result['colab_over_local_wall_ratio']:.3f}**.",
        "Un cociente mayor que uno indica que Colab tardó más en esta prueba.",
        "Las duraciones de búsqueda incluyen inicialización, búsqueda y validación",
        "estricta final; excluyen instalación, importación, carga de datos y calentamiento.", "",
        "## Reproducibilidad y entorno", "",
        f"Coincidieron **{len(paired) - mismatching_pairs} de {len(paired)}** parejas",
        "en objetivo inicial/final, makespan y esperas con tolerancia absoluta 1e-9.",
        "Se verificaron cobertura, claves únicas, 6.060 evaluaciones factibles por corrida,",
        "configuración, semillas, versiones de NumPy/PyYAML y hashes del código y datos.",
        "La validación estricta corresponde al motor en cada corrida; este análisis",
        "no volvió a reconstruir todos los calendarios.", "",
        "| Entorno | Procesador | CPU lógicas | RAM declarada (GiB) | Python |",
        "|---|---|---:|---:|---|",
    ]
    for label, name in (("local", "Mac local"), ("colab", "Colab CPU")):
        hw = observations[label]["hardware"]
        ram = f"{hw['ram_bytes'] / 1024**3:.2f}" if hw.get("ram_bytes") else "No disponible"
        lines.append(
            f"| {name} | {hw.get('processor') or 'No disponible'} | "
            f"{hw.get('logical_cpus')} | {ram} | {observations[label]['versions']['python']} |"
        )
    if versions:
        lines += ["", "Diferencias de versiones registradas:"]
        lines += [
            f"- {name}: local {value['local']}; Colab {value['colab']}."
            for name, value in versions.items()
        ]
    lines += [
        "", "Se comparan entornos completos, con una sesión por entorno. Las diferencias",
        "de hardware, Python, virtualización y carga no permiten atribuir todo el",
        "cociente observado a un solo factor.", "",
        "## Estimación de la campaña completa", "",
        "**Estas cifras son estimaciones, no ejecuciones de la campaña de 720 corridas.**",
        "La principal escala el tiempo observado por seis. La secundaria añade su",
        "cuota nominal de 720 × 10 segundos, sin haber ejecutado aquí el runner temporal.", "",
        "| Entorno | Principal: 720 corridas | Principal + secundaria nominal |",
        "|---|---:|---:|",
    ]
    for label, name in (("local", "Mac local"), ("colab", "Colab CPU")):
        est = result["estimates_not_observed"][label]
        lines.append(
            f"| {name} | {clock(est['main_720_search_seconds'])} | "
            f"{clock(est['main_plus_secondary_nominal_search_seconds'])} |"
        )
    lines += [
        "", "El escalamiento supone una mezcla de instancias y rendimiento similares.",
        "No incluye instalación, análisis, almacenamiento ni sobrepasos y validación",
        "adicional de la fase temporal.", "",
        "## Evidencia", "",
        "- [Resultados emparejados](comparison.csv).",
        "- [Resumen por método y tamaño](timing_summary.csv).",
        "- [Cálculos, comprobaciones y fuentes](comparison.json).",
        "- [Figura de tiempos](tiempos_smoke.png).",
    ]
    for label, name in (("local", "Mac local"), ("colab", "Colab CPU")):
        folder = (local if label == "local" else colab)["folder"]
        for filename in ("manifest.json", "summary.json", "runs.csv"):
            lines.append(f"- [{name}: {filename}]({relative(folder / filename, output)}).")
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "state": "completed_analysis", "output": str(output),
        "local_search_seconds": local["wall"], "colab_search_seconds": colab["wall"],
        "ratio_colab_over_local": result["colab_over_local_wall_ratio"],
        "quality_matching_pairs": len(paired) - mismatching_pairs,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
