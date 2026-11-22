"""Check the final slides and the script against the archived results.

Recomputes each figure from its source file, then checks the slide limits and
the script timing. It writes nothing:

    python -X utf8 presentacion_final/verificar.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / "experiments/results"
MAX_BULLETS = 5
MAX_WORDS = 12
CONTENT_SLIDES = range(13, 16)
TARGET_SECONDS = 840
MAX_SECONDS = 900
SPOKEN_WORDS_PER_SECOND = 2.5


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def comma(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def tex(value: float, digits: int = 3) -> str:
    """Signed number as written in the slides, inside math mode."""
    sign = "-" if value < 0 else "+"
    return f"${sign}{abs(value):.{digits}f}$".replace(".", "{,}")


def spoken(value: float, digits: int = 3) -> str:
    """Signed number as written in the script."""
    sign = "−" if value < 0 else "+"
    return sign + comma(abs(value), digits)


def thousands(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def figures() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Return (claim, text, source) lists for the slides and for the script."""
    slides, script = [], []
    family = {r["comparison"]: r for r in rows(RESULTS / "entrega2_congestion_90_109/comparisons.csv")}
    for code in ("C1", "C2", "C3", "C4"):
        row = family[code]
        source = f"entrega2_congestion_90_109/comparisons.csv ({code})"
        slides.append((f"{code} media", tex(float(row["mean_difference"])), source))
        slides.append((f"{code} IC", f"[{tex(float(row['ci_low']))}; {tex(float(row['ci_high']))}]", source))
        slides.append((f"{code} p Holm", f"Holm {comma(float(row['holm_p']))}", source))
    c1 = family["C1"]
    script.append(("C1 media", spoken(float(c1["mean_difference"])), "comparisons.csv (C1)"))
    script.append(("C1 p Holm", comma(float(c1["holm_p"])), "comparisons.csv (C1)"))
    script.append(("C1 IC", f"[{spoken(float(c1['ci_low']))}; {spoken(float(c1['ci_high']))}]",
                   "comparisons.csv (C1)"))

    audit = json.loads((RESULTS / "entrega2_congestion_90_109/verification.json").read_text(encoding="utf-8"))
    assert audit["status"] == "passed" and audit["failed_pairs"] == 0
    for target in (slides, script):
        target.append(("calendarios auditados", thousands(audit["schedules_replayed"]), "verification.json"))
        target.append(("pares", f"{audit['pairs']} pares", "verification.json"))

    waiting = [r for r in rows(RESULTS / "entrega2_exploratorio/espera_por_tamano.csv")
               if r["size"] == "todas"][0]
    share = comma(100 * float(waiting["waiting_share"]), 1)
    slides.append(("espera final", f"{share} \\%", "espera_por_tamano.csv"))
    script.append(("espera final", f"{share} %", "espera_por_tamano.csv"))
    cells = rows(RESULTS / "entrega2_calibracion_congestion_85_89/celdas.csv")
    no_cut = max(float(c["waiting_share"]) for c in cells if float(c["rho_surgeons"]) == 1.0)
    slides.append(("máximo sin reducir cirujanos", f"{100 * no_cut:.0f} \\%", "celdas.csv"))
    chosen = json.loads((RESULTS / "entrega2_calibracion_congestion_85_89/manifest.json")
                        .read_text(encoding="utf-8"))["selected_cell"]
    slides.append(("celda elegida", f"{100 * chosen['waiting_share']:.0f} \\%", "manifest.json"))
    portfolio = [r for r in rows(RESULTS / "portfolios_60_79/runs.csv")
                 if r["method"] == "fixed_portfolio6060"]
    old = f"{sum(float(r['blocked']) > 0 for r in portfolio)} de {len(portfolio)}"
    for target in (slides, script):
        target.append(("espera estándar", old, "portfolios_60_79/runs.csv"))

    simulation = rows(RESULTS / "entrega2_potencia/simulacion.csv")
    planned = [r for r in simulation if r["method"] == "dmab3030" and r["effect"] == "0.65"
               and r["instances"] == "48"][0]
    realized = [r for r in rows(RESULTS / "entrega2_exploratorio/potencia_realizada.csv")
                if r["effect"] == "0.65"][0]
    for target in (slides, script):
        target.append(("potencia simulada", comma(float(planned["rejection_alpha_05"]), 2), "simulacion.csv"))
        target.append(("potencia realizada", comma(float(realized["t_power_alpha_05"]), 2),
                       "potencia_realizada.csv"))
    slides.append(("DE supuesta", comma(float(realized["assumed_sd"]), 2), "potencia_realizada.csv"))
    slides.append(("DE observada", comma(float(realized["realized_sd"]), 2), "potencia_realizada.csv"))
    slides.append(("pares para 0,65", thousands(int(realized["pairs_needed_realized_sd"])),
                   "potencia_realizada.csv"))
    type_one = [r for r in simulation if r["method"] == "fixed_portfolio6060"
                and r["reference"] == "uniform6060" and float(r["effect"]) == 0
                and r["instances"] == "48"][0]
    slides.append(("error tipo I de C2", comma(float(type_one["rejection_alpha_05"])), "simulacion.csv"))

    extra = {(r["measure"], r["method"]): float(r["value"])
             for r in rows(RESULTS / "entrega3_descriptivos/descriptivos.csv")}
    source = "entrega3_descriptivos/descriptivos.csv"
    stalled = comma(100 * extra["share_without_improvement_after_3030", "uniform6060"], 1)
    slides.append(("Tabu prolongado sin mejoras", f"{stalled} \\%", source))
    script.append(("Tabu prolongado sin mejoras", f"{stalled} %", source))
    slides.append(("corridas sin mejoras",
                   f"{extra['runs_without_improvement_after_3030', 'uniform6060']:.0f} de 960", source))
    restarts = f"{extra['median_restarts', 'dmab3030']:.0f}"
    slides.append(("mediana de reinicios", f"{{{restarts}}}", source))
    script.append(("mediana de reinicios", f"mediana de {restarts} veces", source))
    slides.append(("evaluaciones por reinicio",
                   f"cada {extra['evaluations_per_median_restart', 'dmab3030']:.0f} evaluaciones", source))
    repaired = comma(100 * extra["mean_repaired_share", "dmab3030"], 1)
    slides.append(("reparación D-MAB", f"{repaired} \\%", source))
    script.append(("reparación D-MAB", f"{repaired} %", source))

    posterior = {(r["measure"], r["item"]): float(r["value"])
                 for r in rows(RESULTS / "entrega3_diagnostico_revision/summary.csv")}
    source = "entrega3_diagnostico_revision/summary.csv"
    noise = f"{posterior['stationary_median_restarts', 'identical_arms']:.0f}"
    slides.append(("reinicios sin cambios", f"{{{noise}}}", source))
    script.append(("reinicios sin cambios", f"{noise} veces", source))
    steady = f"{posterior['instances_with_room_1_best_in_all_phases', 'uniform']:.0f} de 48"
    leading = comma(posterior["restarts_by_leader_share", "dmab"], 1)
    slides.append(("reinicios por el líder", f"{leading} \\%", source))
    script.append(("reinicios por el líder", f"{leading} %", source))
    script.append(("mismo mejor operador", steady, source))
    script.append(("recompensas que mejoran el global",
                   f"{comma(posterior['rewarded_that_improve_best', 'uniform'], 1)} %", source))
    script.append(("infactibles con la regla docente",
                   f"{comma(posterior['infeasible_with_repository_rule', 'all'], 1)} %", source))

    timing = {(r["measure"], r["item"]): float(r["value"])
              for r in rows(RESULTS / "entrega3_diagnostico_recompensa/summary.csv")}
    source = "entrega3_diagnostico_recompensa/summary.csv"
    later = comma(timing["restarts_after_first_third", "dmab"], 1)
    slides.append(("reinicios con recompensa estable", f"{later} \\%", source))
    script.append(("reinicios con recompensa estable", f"{later} %", source))
    source = "entrega3_sensibilidad_bases/comparisons.csv"
    nested = {r["comparison"]: r for r in rows(RESULTS / source)}
    assert [code for code, r in nested.items() if r["criteria_by_base"] == "1"] == ["E1"]
    for code, row in nested.items():
        interval = f"[{tex(float(row['ci_low']))}; {tex(float(row['ci_high']))}]"
        slides.append((f"{code} por base", f"{interval} & {comma(float(row['holm_p']))}", source))
    for code in ("C1", "C2"):
        script.append((f"{code} por base", comma(float(nested[code]["holm_p"])), source))

    exploratory = rows(RESULTS / "entrega2_exploratorio/contrastes.csv")[0]
    slides.append(("exploratorio", tex(float(exploratory["mean_difference"])), "contrastes.csv"))
    script.append(("exploratorio", spoken(float(exploratory["mean_difference"])), "contrastes.csv"))
    confirmation = rows(RESULTS / "entrega3_confirmacion_ucb1/comparisons.csv")[0]
    source = "entrega3_confirmacion_ucb1/comparisons.csv (E1)"
    assert float(confirmation["wilcoxon_p"]) < 0.001
    slides.append(("E1 media", tex(float(confirmation["mean_difference"])), source))
    slides.append(("E1 IC", f"[{tex(float(confirmation['ci_low']))}; {tex(float(confirmation['ci_high']))}]",
                   source))
    script.append(("E1 media", spoken(float(confirmation["mean_difference"])), source))
    script.append(("E1 IC", f"[{spoken(float(confirmation['ci_low']))}; "
                            f"{spoken(float(confirmation['ci_high']))}]", source))
    replay = json.loads((RESULTS / "entrega3_confirmacion_ucb1/verification.json").read_text(encoding="utf-8"))
    assert replay["status"] == "passed" and replay["h1c_supported"]
    slides.append(("E1 calendarios auditados", thousands(replay["schedules_replayed"]), "verification.json"))
    manifest = json.loads((RESULTS / "entrega3_confirmacion_ucb1/manifest.json").read_text(encoding="utf-8"))
    slides.append(("commit del protocolo E1", manifest["protocol_commit"][:7], "manifest.json"))
    revision = {(r["study"], r["measure"], r["item"]): float(r["value"])
                for r in rows(RESULTS / "entrega3_revision/descriptivos.csv")}
    source = "entrega3_revision/descriptivos.csv"
    study = "90-109"
    for method in ("uniform3030", "dmab3030", "ucb3030", "uniform6060", "two_uniform6060",
                   "fixed_portfolio6060"):
        cells = " & ".join(comma(revision[study, measure, method], 2)
                           for measure in ("best", "objective", "worst", "sd", "rpd", "runtime"))
        slides.append((f"descriptivos {method}", cells, source))
    for origin in ("20-39", "40-59"):
        cells = " & ".join(tex(revision[origin, "difference", pair])
                           for pair in ("ucb-uniform", "dmab-uniform", "dmab-ucb"))
        slides.append((f"estándar {origin}", cells, source))
        script.append((f"estándar {origin}", spoken(revision[origin, "difference", "ucb-uniform"]), source))
    slides.append(("E1 con 15 cirugías", tex(revision["120-139", "difference_15", "E1"], 2), source))
    for size in (15, 20, 25, 30):
        script.append((f"E1 con {size} cirugías",
                       spoken(revision["120-139", f"difference_{size}", "E1"], 2), source))
    cost = comma(revision[study, "time_overhead", "ucb3030"], 1)
    slides.append(("tiempo UCB1", f"{cost} \\%", source))
    script.append(("tiempo UCB1", f"{cost} %", source))
    script.append(("decodificación UCB1",
                   f"{comma(revision[study, 'decoded_overhead', 'ucb3030'], 1)} %", source))
    script.append(("diferencia relativa de E1",
                   f"{comma(-revision['120-139', 'relative_difference', 'E1'], 2)} %", source))
    script.append(("razón de errores estándar",
                   f"{comma(revision[study, 'bootstrap_se_ratio', 'C1'], 2)} veces", source))
    return slides, script


def bullet_words(text: str) -> int:
    text = re.sub(r"\$[^$]*\$", "X", text)
    text = re.sub(r"\\texttt\{([^}]*)\}", r"\1", text).replace("\\%", "%").replace("\\_", "_")
    return len(text.split())


def main() -> None:
    document = (HERE / "main.tex").read_text(encoding="utf-8")
    body = document[document.index("\\begin{document}"):]
    script = (HERE / "guion.md").read_text(encoding="utf-8")
    slide_figures, script_figures = figures()
    failures = 0
    for name, text, checks in (("diapositivas", body, slide_figures), ("guion", script, script_figures)):
        for claim, expected, source in checks:
            found = expected in text
            failures += not found
            print(f"{'OK ' if found else 'NO '} {name} · {claim}: {expected}  ({source})")

    presented, appendix = body.split("\\appendix")
    pattern = r"\\begin\{frame\}(?:\[plain\])?(?:\{(.*?)\})?\n(.*?)\\end\{frame\}"
    frames = re.findall(pattern, presented, re.S)
    content = len(frames) - 1
    flag = content not in CONTENT_SLIDES
    failures += flag
    print(f"\n{'NO ' if flag else 'OK '} Diapositivas de contenido: {content} "
          f"(más portada y {len(re.findall(pattern, appendix, re.S))} de apéndice)")
    for title, text in frames + re.findall(pattern, appendix, re.S):
        items = re.findall(r"\\item (.+)", text)
        longest = max((bullet_words(item) for item in items), default=0)
        flag = len(items) > MAX_BULLETS or longest > MAX_WORDS
        failures += flag
        print(f"{'NO ' if flag else 'OK '} {len(items)} viñetas, máximo {longest} palabras: {title[:62]}")

    sections = re.findall(r"### (\d+)\. (.*?)\n\*\*Tiempo:\*\* (\d+):(\d+).*?\n\n(.*?)(?=\n### |\n## )",
                          script, re.S)
    titles = [title for title, _ in frames[1:]]
    total = 0
    for number, title, minutes, seconds, speech in sections:
        duration = 60 * int(minutes) + int(seconds)
        total += duration
        words = len(speech.split())
        rate = words / duration
        normalized = title.replace("–", "--")
        matches = int(number) == 1 or normalized == titles[int(number) - 2]
        flag = rate > SPOKEN_WORDS_PER_SECOND or not matches
        failures += flag
        print(f"{'NO ' if flag else 'OK '} Diapositiva {number}: {duration} s, {words} palabras, "
              f"{rate:.2f} pal/s{'' if matches else ' · el título no coincide'}")
    flag = len(sections) != len(frames) or total > TARGET_SECONDS
    failures += flag
    print(f"{'NO ' if flag else 'OK '} Tiempo total: {total // 60}:{total % 60:02d} "
          f"(objetivo {TARGET_SECONDS // 60}:00, máximo {MAX_SECONDS // 60}:00)")
    questions = len(re.findall(r"^\*\*¿.*\?\*\*$", script, re.M))
    flag = questions < 8
    failures += flag
    print(f"{'NO ' if flag else 'OK '} Preguntas probables con respuesta: {questions}")
    print(f"\nFallos: {failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
