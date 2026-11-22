"""Check every figure of the abstract, results and conclusion against its source.

Recomputes each quoted value from the archived result files and checks that the
LaTeX text contains it, including the two generated tables and the calibration
figures of section 3. It also asserts the qualitative claims that depend on a
sign or an order. Then it lists any number in the text that is neither a
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
    "12": "instancias por tamaño y del catálogo estándar",
    "15": "tamaño de instancia", "20": "tamaño de instancia y semillas por instancia",
    "25": "tamaño de instancia", "30": "tamaño de instancia",
    "39": "semillas 20-39", "40": "semillas 40-59", "59": "semillas 40-59",
    "60": "semillas 60-79", "79": "semillas 60-79",
    "5": "percentiles 5-95 de la figura 2",
    "0,35": "lambda de la configuración de las semillas 20-39",
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
    # The text says that the interval includes harm and benefit beyond the threshold.
    assert float(c1["ci_low"]) < -0.25 and float(c1["ci_high"]) > 0.25

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
    found.append(("DE observada", plain(float(realized["realized_sd"]), 2), "potencia_realizada.csv"))
    found.append(("DE supuesta", plain(float(realized["assumed_sd"]), 2), "potencia_realizada.csv"))

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
    for method in ("uniform3030", "ucb3030"):
        found.append((f"reparación {method}", plain(100 * extra["mean_repaired_share", method], 1), source))
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

    return (found + revision_checks() + diagnosis_checks() + reward_checks()
            + sensitivity_checks() + closing_checks())


def revision_checks() -> list[tuple[str, str, str]]:
    """Figures and qualitative claims added by the final revision."""
    source = "entrega3_revision/descriptivos.csv"
    value = {(r["study"], r["measure"], r["item"]): float(r["value"])
             for r in rows(RESULTS / source)}
    found = []

    def add(claim: str, text: str) -> None:
        found.append((claim, text, source))

    study = "90-109"
    methods = ("uniform3030", "dmab3030", "ucb3030", "uniform6060", "two_uniform6060",
               "fixed_portfolio6060")
    for method in methods:
        for measure in ("best", "objective", "worst", "sd", "rpd", "makespan", "blocked",
                        "max_wait", "runtime"):
            add(f"{measure} {method}", plain(value[study, measure, method], 2))
    for rule in ("fifo", "spt", "lpt"):
        for measure in ("objective", "rpd", "makespan", "blocked", "max_wait"):
            add(f"{measure} {rule}", plain(value[study, measure, rule], 2))
    for code in ("C1", "C2", "C3", "C4", "E1"):
        origin = "120-139" if code == "E1" else study
        for size in (15, 20, 25, 30):
            add(f"{code} con {size} cirugías",
                tex(value[origin, f"difference_{size}", code], 2, signed=True))

    gain = {m: value[study, "improvement_over_best_rule", m] for m in ("uniform3030", "ucb3030")}
    assert gain["ucb3030"] - gain["uniform3030"] < 1
    for method, percent in gain.items():
        add(f"mejora sobre la mejor regla {method}", plain(percent, 1))
    add("razón de errores estándar C1", plain(value[study, "bootstrap_se_ratio", "C1"], 2))
    add("E1 instancias a favor", f"{value['120-139', 'instances_better', 'E1']:.0f}")
    add("E1 diferencia relativa", plain(-value["120-139", "relative_difference", "E1"], 2))
    add("decodificación UCB1", plain(value[study, "decoded_overhead", "ucb3030"], 1))
    add("tiempo UCB1", plain(value[study, "time_overhead", "ucb3030"], 1))
    add("tiempo D-MAB", plain(value[study, "time_overhead", "dmab3030"], 1))
    add("tiempo UCB1 en E1", plain(value["120-139", "time_overhead", "ucb3030"], 1))
    for method in ("uniform3030", "ucb3030"):
        add(f"DE en E1 {method}", plain(value["120-139", "sd", method], 2))
        add(f"cambio de sala de anestesia en E1 {method}",
            plain(value["120-139", "share_room_1", method], 1))
    # The rules finish earlier and wait more than ten times as long as uniform Tabu.
    for rule in ("fifo", "spt", "lpt"):
        assert value[study, "makespan", rule] < value[study, "makespan", "uniform3030"]
        assert value[study, "blocked", rule] > 10 * value[study, "blocked", "uniform3030"]
    assert value[study, "blocked", "dmab3030"] < value[study, "blocked", "uniform3030"]
    assert value[study, "makespan", "dmab3030"] >= value[study, "makespan", "uniform3030"]
    for origin in (study, "120-139"):
        assert value[origin, "sd", "ucb3030"] > value[origin, "sd", "uniform3030"]
    assert value[study, "difference_15", "C2"] > 0 and value[study, "difference_20", "C2"] > 0
    assert value[study, "difference_25", "C2"] < 0 and value[study, "difference_30", "C2"] < 0
    assert value[study, "difference_15", "C4"] < 0
    assert value[study, "instances_better_25", "C4"] == 0
    assert value["120-139", "difference_15", "E1"] > 0

    for origin in ("20-39", "40-59"):
        for pair in ("ucb-uniform", "dmab-uniform", "dmab-ucb"):
            add(f"estándar {origin} {pair}", tex(value[origin, "difference", pair], signed=True))
    for pair in ("dmab3030-uniform3030", "fixed_portfolio6060-uniform6060",
                 "fixed_portfolio6060-two_uniform6060"):
        add(f"estándar 60-79 {pair}", tex(value["60-79", "difference", pair], signed=True))

    pilot = [value["110-114", f"difference_{size}", "dmab-uniform"] for size in (15, 20, 25, 30)]
    assert sum(difference > 0 for difference in pilot) == 3
    for size, difference in zip((15, 20, 25, 30), pilot):
        add(f"piloto con {size} cirugías", tex(difference, 2, signed=True))

    add("calibración elegida", tex(value["0-5", "difference", "chosen"]))
    add("calibración siguiente", tex(value["0-5", "difference", "runner_up"]))
    add("variantes calibradas", f"{value['0-5', 'variants', 'all']:.0f}")
    add("calibración con lambda 10", tex(value["0-5", "difference", "lambda_10"], signed=True))
    without = [r for r in rows(RESULTS / "calibration_0_5/runs.csv")
               if r["variant"] == "dmab|solution|C=0.1|lambda=10.0"]
    # "Almost removed": no restart in most runs and never more than one.
    assert sorted(int(r["dmab_restarts"]) for r in without)[len(without) // 2] == 0
    assert max(int(r["dmab_restarts"]) for r in without) <= 1
    assert value["0-5", "difference", "lambda_10"] > value["0-5", "difference", "chosen"]
    return found


def diagnosis_checks() -> list[tuple[str, str, str]]:
    """Figures of the post-hoc diagnosis and the restored figures of section 3."""
    source = "entrega3_diagnostico_revision/summary.csv"
    value = {(r["measure"], r["item"]): float(r["value"]) for r in rows(RESULTS / source)}
    found = []

    def add(claim: str, text: str, origin: str = source) -> None:
        found.append((claim, text, origin))

    # The text says the same move is the most rewarded one in the three thirds.
    assert value["instances_with_room_1_best_in_all_phases", "uniform"] >= 40
    add("mismo mejor operador", f"{value['instances_with_room_1_best_in_all_phases', 'uniform']:.0f} de 48")
    add("reinicios sin cambios",
        f"{value['stationary_median_restarts', 'identical_arms']:.0f} veces")
    add("reinicios por el líder", plain(value["restarts_by_leader_share", "dmab"], 1))
    add("recompensas que mejoran el global", plain(value["rewarded_that_improve_best", "uniform"], 1))
    for size in ("15", "30"):
        add(f"sobrecosto con {size} cirugías", plain(value["ucb_time_overhead_by_size", size], 1))
    add("sección 3: infactibles con la regla docente",
        plain(value["infeasible_with_repository_rule", "all"], 1))
    add("sección 3: calendarios finales", thousands(int(value["final_schedules", "all"])))

    origin = "entrega2_entorno_80_84/summary.csv"
    seconds = {r["size"]: float(r["median_seconds"]) for r in rows(RESULTS / origin)}
    for size, median in seconds.items():
        add(f"sección 3: tiempo con {size} cirugías", plain(median, 2), origin)
    add("sección 3: escalamiento del tiempo", plain(seconds["30"] / seconds["15"], 1), origin)
    origin = "entrega2_potencia/simulacion.csv"
    power = [r for r in rows(RESULTS / origin) if r["method"] == "dmab3030"
             and r["effect"] == "0.25" and r["instances"] == "48"][0]
    add("sección 3: potencia para 0,25", plain(float(power["rejection_alpha_05"]), 2), origin)
    return found


def reward_checks() -> list[tuple[str, str, str]]:
    """The reward drops early and is then stable; most restarts come later."""
    folder = RESULTS / "entrega3_diagnostico_recompensa"
    source = "entrega3_diagnostico_recompensa/summary.csv"
    value = {(r["measure"], r["item"]): float(r["value"]) for r in rows(folder / "summary.csv")}
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["seeds"]) == 4 and manifest["mismatches"] == 0
    for policy in ("uniform", "dmab"):
        first, second, third = (value["mean_reward_by_third", f"{policy}:{i}"] for i in (1, 2, 3))
        assert first > 1.05 * second and abs(third / second - 1) < 0.05
    later = value["restarts_after_first_third", "dmab"]
    assert later > 50
    return [("reinicios después del primer tercio", plain(later, 1), source)]


def sensitivity_checks() -> list[tuple[str, str, str]]:
    """Exploratory reanalysis with the base instance as the unit."""
    source = "entrega3_sensibilidad_bases/comparisons.csv"
    value = {r["comparison"]: r for r in rows(RESULTS / source)}
    # Only E1 meets the rule; C2 and C4 lose significance; C1 still includes zero.
    assert {code: r["criteria_by_base"] for code, r in value.items()} == {
        "C1": "0", "C2": "0", "C3": "0", "C4": "0", "E1": "1"}
    assert float(value["C2"]["holm_p"]) >= 0.05 and float(value["C4"]["holm_p"]) >= 0.05
    assert float(value["C1"]["ci_low"]) < 0 < float(value["C1"]["ci_high"])
    found = []
    for code, row in value.items():
        assert row["units"] == "12"
        for side in ("low", "high"):
            found.append((f"{code} por base, IC {side}",
                          tex(float(row[f"ci_{side}"]), signed=True) if code != "E1"
                          else tex(float(row[f"ci_{side}"])), source))
        prefix = "p=" if code == "E1" else ""
        found.append((f"{code} por base, p", prefix + plain(float(row["holm_p"]), 3), source))
    return found


def closing_checks() -> list[tuple[str, str, str]]:
    """Effect size, start-time rule and constructive rules in the official instances."""
    source = "entrega3_cierre/summary.csv"
    value = {(r["measure"], r["item"]): float(r["value"]) for r in rows(RESULTS / source)}
    found = []

    def add(claim: str, text: str) -> None:
        found.append((claim, text, source))

    for code in ("C1", "C2", "C3", "C4"):
        add(f"r de {code}", tex(value["effect_size_r", code], 2, signed=True))
    add("r de E1", "r=" + tex(value["effect_size_r", "E1"], 2, signed=True).strip("$"))

    # The delay removes every wait, and then the best rule wins in all 48 instances.
    assert value["schedules_waiting_after_delay", "all"] == 0
    wins = [v for (measure, _), v in value.items() if measure == "instances_where_best_rule_wins"]
    assert len(wins) == 8 and set(wins) == {48.0}
    add("sección 3: la mejor regla con retraso", f"en las {wins[0]:.0f} instancias")
    for name, study in (("E1", "entrega3_confirmacion_ucb1"),
                        ("90-109", "entrega2_congestion_90_109")):
        after = value["ucb_minus_uniform_delayed_objective", study]
        assert value["ucb_minus_uniform_objective", study] < after < 0
        add(f"sección 3: ventaja de UCB1 con retraso ({name})", plain(-after, 3))

    better = {measure: value["official_instances_better_than_best_rule",
                             f"fixed_portfolio6060:{measure}"]
              for measure in ("objective", "makespan", "course_objective")}
    assert better == {"objective": 12, "makespan": 10, "course_objective": 10}
    add("cartera gana en makespan y con desequilibrio", f"ganó en {better['makespan']:.0f}")
    gain = {method: value["official_mean_gain_percent", f"{method}:objective"]
            for method in ("fixed_portfolio6060", "two_uniform6060")}
    # The gain is not attributed to learning: two uniform Tabu obtain as much.
    assert gain["two_uniform6060"] >= gain["fixed_portfolio6060"]
    for method, percent in gain.items():
        add(f"mejora sobre las reglas en las oficiales, {method}", plain(percent, 2))
    return found


def visible(source: str) -> str:
    """LaTeX text without comments, labels, references or file names."""
    text = re.sub(r"(?<!\\)%.*", "", source)
    text = re.sub(r"\\(label|ref|input|includegraphics(\[[^\]]*\])?|vspace|textcite|parencite"
                  r"|setlength\{\\tabcolsep\})\{[^}]*\}", "", text)
    # Layout markup: penalties, column counts and column widths are not results.
    text = re.sub(r"\\@?\w*penalty=\d+", "", text)
    text = re.sub(r"\\multicolumn\{\d+\}(\{c\})?", "", text)
    text = re.sub(r"\\cmidrule(\(\w+\))?\{\d+-\d+\}", "", text)
    text = re.sub(r"\$\\mathbf\{((?:[^{}]|\{,\})*)\}\$", r"$\1$", text)
    text = re.sub(r"\\textbf\{([\d,]+)\}", r"\1", text)
    return re.sub(r"p\{[\d.]+\\textwidth\}", "", text)


def numbers(text: str) -> set[str]:
    """Numeric tokens, skipping digits inside identifiers such as C3, E1 or UCB1."""
    flat = text.replace("{,}", ",")
    return set(re.findall(r"(?<![A-Za-z\d.,])\d+(?:[.,]\d+)*", flat))


def main() -> None:
    body = visible((HERE / "resultados.tex").read_text(encoding="utf-8"))
    table = visible((HERE / "tablas/tabla_comparaciones.tex").read_text(encoding="utf-8"))
    described = visible((HERE / "tablas/tabla_descriptiva.tex").read_text(encoding="utf-8"))
    setup = visible((HERE / "experimental_setup.tex").read_text(encoding="utf-8"))
    conclusion = visible((HERE / "conclusion.tex").read_text(encoding="utf-8"))
    document = (HERE / "main.tex").read_text(encoding="utf-8")
    abstract = visible(document[document.index("\\chapter*{Resumen}"):document.index("\\noindent\\textbf{Palabras")])
    failures = 0
    verified = set()
    for claim, text, source in checks():
        # Section 3 only holds the calibration figures; it has its own constants.
        places = (setup,) if claim.startswith(("calibración", "variantes", "sección 3")) else (body, table, described)
        present = any(text in place or text in place.replace("{,}", ",") for place in places)
        failures += not present
        verified |= numbers(text)
        print(f"{'OK ' if present else 'NO '} {claim}: {text}  ({source})")

    # The section numbers of the cross-references are not results.
    allowed = verified | set(DESIGN) | {"1", "2", "4", "5"}
    for name, text in (("resumen", abstract), ("resultados.tex", body),
                       ("tabla_comparaciones.tex", table), ("tabla_descriptiva.tex", described),
                       ("conclusion.tex", conclusion)):
        unknown = sorted(numbers(text) - allowed, key=lambda item: (len(item), item))
        failures += len(unknown)
        print(f"{'OK ' if not unknown else 'NO '} {name}: números sin fuente {unknown or 'ninguno'}")
    print(f"\nFallos: {failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
