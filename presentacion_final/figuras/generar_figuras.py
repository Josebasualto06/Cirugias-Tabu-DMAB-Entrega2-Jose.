"""Build the figures of the final presentation from archived results.

Run from any directory:

    python presentacion_final/figuras/generar_figuras.py

It copies the institutional images and the calibration figure of the Entrega 2
presentation, and draws the forest plot with the report's own script. It changes
nothing outside this folder.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIOUS = ROOT / "presentacion/figuras"
FOREST = ROOT / "experiments/scripts/forest_comparaciones.py"


def main() -> None:
    for name in ("encabezado.png", "logo_pucv.png", "calibracion_espera.pdf"):
        shutil.copyfile(PREVIOUS / name, HERE / name)
    # Same data and palette as the report; sans-serif type and the values column.
    subprocess.run(
        [sys.executable, str(FOREST), "--valores", "--fuente", "DejaVu Sans",
         "--ancho", "15", "--alto", "5.45", "--cuerpo", "7.8",
         "--salida", str(HERE / "forest_comparaciones.pdf")],
        check=True,
    )
    print(f"Figuras escritas en {HERE}")


if __name__ == "__main__":
    main()
