"""Check the writing style of the results and conclusion sections.

Lists every sentence with 25 words or more and counts explicit connectors per
subsection. It reads the LaTeX sources and writes nothing:

    python informe/verificar_estilo.py
    python informe/verificar_estilo.py informe/resultados.tex informe/conclusion.tex
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT = (HERE / "resultados.tex", HERE / "conclusion.tex")
MAX_WORDS = 24
CONNECTORS = {
    "contraste": ("sin embargo", "no obstante", "en cambio", "pese a ello", "aunque"),
    "causa": ("por tanto", "por consiguiente", "por eso", "porque", "así"),
    "adición": ("además", "primero", "segundo", "tercero", "por último", "luego", "también"),
    "síntesis": ("en síntesis", "en conjunto", "en suma"),
}


def plain_text(source: str) -> str:
    """Drop comments, floats and markup; keep the words a reader sees."""
    text = re.sub(r"(?<!\\)%.*", "", source)
    text = re.sub(r"\\begin\{(table|figure)\}.*?\\end\{\1\}", "", text, flags=re.S)
    text = re.sub(r"\\(label|ref|eqref|input|vspace|centering)\{[^}]*\}", "", text)
    text = re.sub(r"\\(textcite|parencite)\{[^}]*\}", "Cita", text)
    text = re.sub(r"\$[^$]*\$", "N", text)
    text = re.sub(r"\\(emph|textbf|texttt|textit)\{([^}]*)\}", r"\2", text)
    text = text.replace("~", " ").replace("\\%", "%").replace("--", "–")
    text = re.sub(r"\\(begin|end)\{(itemize|enumerate)\}", "\n\n", text)
    text = re.sub(r"\\item\b", "\n\n", text)
    return text


def sections(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"\\(?:sub)?section\{([^}]*)\}", text)
    return [(title.strip(), body) for title, body in zip(parts[1::2], parts[2::2])]


def sentences(body: str) -> list[str]:
    found = []
    for paragraph in re.split(r"\n\s*\n", body):
        flat = " ".join(paragraph.split())
        found += [piece.strip() for piece in re.split(r"(?<=[.?!])\s+", flat) if piece.strip()]
    return found


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]] or [path for path in DEFAULT if path.exists()]
    long_total = 0
    for path in paths:
        print(f"== {path.name}")
        for title, body in sections(plain_text(path.read_text(encoding="utf-8"))):
            found = sentences(body)
            lengths = [len(sentence.split()) for sentence in found]
            lower = " ".join(found).lower()
            counts = {kind: sum(len(re.findall(rf"\b{re.escape(word)}\b", lower)) for word in words)
                      for kind, words in CONNECTORS.items()}
            summary = ", ".join(f"{kind} {count}" for kind, count in counts.items())
            print(f"-- {title}\n   {len(found)} frases, {sum(lengths)} palabras, "
                  f"máximo {max(lengths, default=0)}; conectores: {summary}")
            for sentence, length in zip(found, lengths):
                if length > MAX_WORDS:
                    long_total += 1
                    print(f"   LARGA ({length}): {sentence}")
    print(f"\nFrases de 25 palabras o más: {long_total}")


if __name__ == "__main__":
    main()
