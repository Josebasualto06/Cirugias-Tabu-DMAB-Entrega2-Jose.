"""Check the slides and the script against the archived results.

Recomputes each figure from its source file, then checks the slide limits and
the script timing. It writes nothing:

    python presentacion/verificar.py
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
MAX_SECONDS = 600
SPOKEN_WORDS_PER_SECOND = 2.5


def rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def comma(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def figures() -> list[tuple[str, str, str]]:
    """Return (claim, text that must appear in the slides, source)."""
    # La defensa cubre solo la configuración experimental: no muestra C1-C4.
    checks = []
    power =[r for r in rows(RESULTS / "entrega2_potencia/potencia.csv")
             if r["method"] == "dmab3030" and r["effect"] == "0.65"][0]
    checks.append(("pares para 0,65", power["naive_pairs_needed"], "potencia.csv"))
    checks.append(("instancias t para 0,65", power["instances_needed_20_seeds"], "potencia.csv"))
    checks.append(("DE supuesta", comma(float(power["sd_difference"]), 2), "potencia.csv"))
    simulated = [r for r in rows(RESULTS / "entrega2_potencia/simulacion.csv")
                 if r["method"] == "dmab3030" and r["effect"] == "0.65" and r["instances"] == "12"][0]
    checks.append(("potencia 12 instancias", comma(float(simulated["rejection_alpha_05"]), 2),
                   "simulacion.csv"))
    realized = [r for r in rows(RESULTS / "entrega2_exploratorio/potencia_realizada.csv")
                if r["effect"] == "0.65"][0]
    checks.append(("DE real", comma(float(realized["realized_sd"]), 2), "potencia_realizada.csv"))
    checks.append(("potencia real", comma(float(realized["t_power_alpha_05"]), 2),
                   "potencia_realizada.csv"))
    pairs = int(realized["pairs_needed_realized_sd"])
    checks.append(("pares con DE real", f"{pairs // 1000}.{pairs % 1000:03d}", "potencia_realizada.csv"))
    waiting = [r for r in rows(RESULTS / "entrega2_exploratorio/espera_por_tamano.csv")
               if r["size"] == "todas"][0]
    checks.append(("espera final", comma(100 * float(waiting["waiting_share"]), 1), "espera_por_tamano.csv"))
    cells = rows(RESULTS / "entrega2_calibracion_congestion_85_89/celdas.csv")
    no_cut = max(float(c["waiting_share"]) for c in cells if float(c["rho_surgeons"]) == 1.0)
    checks.append(("maximo sin reducir cirujanos", f"{100 * no_cut:.0f} \\%", "celdas.csv"))
    chosen = json.loads((RESULTS / "entrega2_calibracion_congestion_85_89/manifest.json")
                        .read_text(encoding="utf-8"))["selected_cell"]
    checks.append(("celda elegida", f"{100 * chosen['waiting_share']:.0f} \\%", "manifest.json"))
    cartera = [r for r in rows(RESULTS / "portfolios_60_79/runs.csv")
               if r["method"] == "fixed_portfolio6060"]
    waiting_old = sum(float(r["blocked"]) > 0 for r in cartera)
    checks.append(("espera estandar", f"{waiting_old} de {len(cartera)}", "portfolios_60_79/runs.csv"))
    return checks


def bullet_words(text: str) -> int:
    text = re.sub(r"\$[^$]*\$", "X", text)
    text = re.sub(r"\\texttt\{([^}]*)\}", r"\1", text).replace("\\%", "%").replace("\\_", "_")
    return len(text.split())


def main() -> None:
    slides = (HERE / "main.tex").read_text(encoding="utf-8")
    body = slides[slides.index("\\begin{document}"):]
    failures = 0
    for claim, text, source in figures():
        found = text in body
        failures += not found
        print(f"{'OK ' if found else 'NO '} {claim}: {text}  ({source})")

    frames = re.findall(r"\\begin\{frame\}(?:\[plain\])?(?:\{(.*?)\})?\n(.*?)\\end\{frame\}", body, re.S)
    print(f"\nFrames: {len(frames)} (portada + contenido + apéndice)")
    for title, content in frames:
        items = re.findall(r"\\item (.+)", content)
        longest = max((bullet_words(item) for item in items), default=0)
        flag = len(items) > MAX_BULLETS or longest > MAX_WORDS
        failures += flag
        print(f"{'NO ' if flag else 'OK '} {len(items)} bullets, máximo {longest} palabras: {title[:60]}")

    script = (HERE / "guion.md").read_text(encoding="utf-8")
    sections = re.findall(r"### (\d+)\..*?\n\*\*Tiempo:\*\* (\d+):(\d+).*?\n\n(.*?)(?=\n### |\n## )", script, re.S)
    total = 0
    for number, minutes, seconds, speech in sections:
        duration = 60 * int(minutes) + int(seconds)
        total += duration
        words = len(speech.split())
        rate = words / duration
        flag = rate > SPOKEN_WORDS_PER_SECOND
        failures += flag
        print(f"{'NO ' if flag else 'OK '} Diapositiva {number}: {duration} s, {words} palabras, {rate:.2f} pal/s")
    print(f"Tiempo total: {total // 60}:{total % 60:02d} de máximo {MAX_SECONDS // 60}:00")
    failures += total > MAX_SECONDS
    print(f"\nFallos: {failures}")


if __name__ == "__main__":
    main()
