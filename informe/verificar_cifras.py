"""Check every figure of the results and conclusion sections against its source.

Recomputes each quoted value from the archived result files and checks that the
LaTeX text contains it. Then it lists any number in the text that is neither a
verified result nor a declared design constant. It writes nothing:

    python informe/verificar_cifras.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "experiments/results"
# Design constants fixed by the protocols, the instances or the document structure.
DESIGN = {
    "95": "nivel del intervalo (protocolo, sección 6)",
    "0,05": "alfa (protocolo, sección 1)",
    "0,25": "umbral práctico (protocolo, sección 7)",
    "0,65": "efecto de planificación (protocolo, sección 5)",
    "50": "criterio de celda válida (protocolo, sección 5)",
    "3.030": "presupuesto por camino (protocolo, sección 4)",
    "6.060": "presupuesto de igual cómputo (protocolo, sección 4)",
    "48": "instancias del catálogo de congestión",
    "90": "semillas 90-109 (protocolo de la Entrega 2)",
    "109": "semillas 90-109 (protocolo de la Entrega 2)",
    "120": "semillas 120-139 (protocolo de la Entrega 3)",
    "139": "semillas 120-139 (protocolo de la Entrega 3)",
    "150": "tamaños futuros declarados en la sección 2.5",
    "0,001": "cota de redacción para p (ver comprobación de E1)",
}


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def tex(value: float, digits: int = 3, signed: bool = False) -> str:
    text = f"{abs(value):.{digits}f}".replace(".", "{,}")
    sign = "-" if value < 0 else ("+" if signed else "")
    return f"${sign}{text}$"


def plain(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def checks() -> list[tuple[str, str, str]]:
    """Return (claim, text that must appear, source)."""
    found = []
    family = {r["comparison"]: r for r in rows(RESULTS / "entrega2_congestion_90_109/comparisons.csv")}
    for code in ("C1", "C2", "C3", "C4"):
        row = family[code]
        source = f"entrega2_congestion_90_109/comparisons.csv ({code})"
        found.append((f"{code} media", tex(float(row["mean_difference"]), signed=True), source))
        found.append((f"{code} IC inferior", tex(float(row["ci_low"]), signed=True), source))
        found.append((f"{code} IC superior", tex(float(row["ci_high"]), signed=True), source))
        found.append((f"{code} p Holm", plain(float(row["holm_p"]), 3), source))
    c1 = family["C1"]
    found.append(("C1 pares a favor de D-MAB", c1["wins"], "comparisons.csv (wins)"))
    found.append(("C1 pares a favor de Tabu uniforme", c1["losses"], "comparisons.csv (losses)"))
    found.append(("C1 perjuicio descartado", plain(float(c1["ci_high"]), 2), "comparisons.csv (ci_high)"))
    found.append(("C1 beneficio descartado", plain(-float(c1["ci_low"]), 2), "comparisons.csv (ci_low)"))

    audit = json.loads((RESULTS / "entrega2_congestion_90_109/verification.json").read_text(encoding="utf-8"))
    assert audit["status"] == "passed" and audit["failed_pairs"] == 0
    found.append(("calendarios auditados", thousands(audit["schedules_replayed"]), "verification.json"))
    found.append(("pares", str(audit["pairs"]), "verification.json"))

    waiting = rows(RESULTS / "entrega2_exploratorio/espera_por_tamano.csv")
    shares = [100 * float(r["waiting_share"]) for r in waiting if r["size"] != "todas"]
    total = [100 * float(r["waiting_share"]) for r in waiting if r["size"] == "todas"][0]
    assert sum(share < 50 for share in shares) == 2 and min(shares[:2]) == min(shares)
    found.append(("soluciones con espera", plain(total, 1), "espera_por_tamano.csv"))
    found.append(("espera mínima por tamaño", plain(min(shares), 1), "espera_por_tamano.csv"))
    found.append(("espera máxima por tamaño", plain(max(shares), 1), "espera_por_tamano.csv"))

    realized = [r for r in rows(RESULTS / "entrega2_exploratorio/potencia_realizada.csv")
                if r["effect"] == "0.65"][0]
    found.append(("potencia realizada", plain(float(realized["t_power_alpha_05"]), 2),
                  "potencia_realizada.csv"))

    described = {r["method"]: r for r in rows(RESULTS / "entrega2_congestion_90_109/descriptive.csv")}
    source = "entrega2_congestion_90_109/descriptive.csv"
    found.append(("espera total uniforme", plain(float(described["uniform3030"]["mean_blocked"]), 2), source))
    found.append(("espera total D-MAB", plain(float(described["dmab3030"]["mean_blocked"]), 2), source))
    found.append(("makespan uniforme", plain(float(described["uniform3030"]["mean_makespan"]), 2), source))
    found.append(("makespan D-MAB", plain(float(described["dmab3030"]["mean_makespan"]), 2), source))

    extra = {(r["measure"], r["method"]): float(r["value"])
             for r in rows(RESULTS / "entrega3_descriptivos/descriptivos.csv")}
    source = "entrega3_descriptivos/descriptivos.csv"
    found.append(("Tabu prolongado sin mejoras", f"{extra['runs_without_improvement_after_3030', 'uniform6060']:.0f}", source))
    found.append(("proporción sin mejoras", plain(100 * extra["share_without_improvement_after_3030", "uniform6060"], 1), source))
    found.append(("mediana de reinicios", f"{extra['median_restarts', 'dmab3030']:.0f}", source))
    found.append(("evaluaciones por reinicio", f"{extra['evaluations_per_median_restart', 'dmab3030']:.0f}", source))
    found.append(("reparación D-MAB", plain(100 * extra["mean_repaired_share", "dmab3030"], 1), source))

    simulated = [r for r in rows(RESULTS / "entrega2_potencia/simulacion.csv")
                 if r["method"] == "fixed_portfolio6060" and r["reference"] == "uniform6060"
                 and float(r["effect"]) == 0 and r["instances"] == "48"][0]
    found.append(("error tipo I de C2", plain(float(simulated["rejection_alpha_05"]), 3), "simulacion.csv"))

    exploratory = rows(RESULTS / "entrega2_exploratorio/contrastes.csv")[0]
    found.append(("exploratorio UCB1 − uniforme", tex(float(exploratory["mean_difference"]), signed=True),
                  "contrastes.csv"))

    confirmation = rows(RESULTS / "entrega3_confirmacion_ucb1/comparisons.csv")[0]
    source = "entrega3_confirmacion_ucb1/comparisons.csv (E1)"
    assert float(confirmation["wilcoxon_p"]) < 0.001
    found.append(("E1 media", tex(float(confirmation["mean_difference"]), signed=True), source))
    found.append(("E1 IC inferior", tex(float(confirmation["ci_low"]), signed=True), source))
    found.append(("E1 IC superior", tex(float(confirmation["ci_high"]), signed=True), source))
    replay = json.loads((RESULTS / "entrega3_confirmacion_ucb1/verification.json").read_text(encoding="utf-8"))
    assert replay["status"] == "passed" and replay["h1c_supported"]
    found.append(("E1 calendarios auditados", thousands(replay["schedules_replayed"]), "verification.json"))

    diagnosis = [r for r in rows(RESULTS / "entrega2_diagnostico_115_119/summary.csv")
                 if r["policy"] == "dmab"][0]
    found.append(("recompensa positiva", plain(100 * float(diagnosis["positive_reward_share"]), 1),
                  "entrega2_diagnostico_115_119/summary.csv"))
    return found


def visible(source: str) -> str:
    """LaTeX text without comments, labels, references or file names."""
    text = re.sub(r"(?<!\\)%.*", "", source)
    text = re.sub(r"\\(label|ref|input|includegraphics(\[[^\]]*\])?|vspace|textcite|parencite"
                  r"|setlength\{\\tabcolsep\})\{[^}]*\}", "", text)
    # Layout markup: penalties, column counts and column widths are not results.
    text = re.sub(r"\\@?\w*penalty=\d+", "", text)
    text = re.sub(r"\\multicolumn\{\d+\}", "", text)
    return re.sub(r"p\{[\d.]+\\textwidth\}", "", text)


def numbers(text: str) -> set[str]:
    """Numeric tokens, skipping digits inside identifiers such as C3, E1 or UCB1."""
    flat = text.replace("{,}", ",")
    return set(re.findall(r"(?<![A-Za-z\d.,])\d+(?:[.,]\d+)*", flat))


def main() -> None:
    body = visible((HERE / "resultados.tex").read_text(encoding="utf-8"))
    table = visible((HERE / "tablas/tabla_comparaciones.tex").read_text(encoding="utf-8"))
    conclusion = visible((HERE / "conclusion.tex").read_text(encoding="utf-8"))
    failures = 0
    verified = set()
    for claim, text, source in checks():
        present = text in body or text in table
        failures += not present
        verified |= numbers(text)
        print(f"{'OK ' if present else 'NO '} {claim}: {text}  ({source})")

    # The section numbers of the cross-references are not results.
    allowed = verified | set(DESIGN) | {"1", "2", "4", "5"}
    for name, text in (("resultados.tex", body), ("tabla_comparaciones.tex", table),
                       ("conclusion.tex", conclusion)):
        unknown = sorted(numbers(text) - allowed, key=lambda item: (len(item), item))
        failures += len(unknown)
        print(f"{'OK ' if not unknown else 'NO '} {name}: números sin fuente {unknown or 'ninguno'}")
    print(f"\nFallos: {failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
