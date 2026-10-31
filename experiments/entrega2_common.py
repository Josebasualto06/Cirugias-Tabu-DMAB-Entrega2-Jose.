"""Provenance helpers shared by the Entrega 2 studies.

Every study writes to its own directory, records code and instance hashes and
refuses to replace a completed study, so archived evidence stays untouched.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import scipy
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "docs/protocolo-entrega2.md"
SIZES = (15, 20, 25, 30)
REPLICAS = (1, 2, 3)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def standard_paths() -> list[Path]:
    return [ROOT / f"instances/standard/HOSP-STD-{size}-{replica:02d}.yaml"
            for size in SIZES for replica in REPLICAS]


def code_hashes(*scripts: Path) -> dict[str, str]:
    """Hash the search package, this module and the calling scripts."""
    paths = sorted((ROOT / "src/surgery_optim").rglob("*.py"))
    paths += [Path(__file__), *scripts]
    return {relative(path): sha256(path) for path in paths}


def instance_hashes(paths: Iterable[Path]) -> dict[str, str]:
    return {relative(path): sha256(path) for path in paths}


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def software() -> dict[str, str]:
    return {
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "pyyaml": yaml.__version__,
        "platform": platform.platform(),
    }


def hardware() -> dict[str, Any]:
    """Describe the machine; Windows CIM data is used when it is available."""
    query = (
        "$c=Get-CimInstance Win32_Processor | Select-Object -First 1;"
        "$m=Get-CimInstance Win32_ComputerSystem;"
        "$o=Get-CimInstance Win32_OperatingSystem;"
        "@{cpu=$c.Name;cores=$c.NumberOfCores;threads=$c.NumberOfLogicalProcessors;"
        "max_clock_mhz=$c.MaxClockSpeed;ram_bytes=$m.TotalPhysicalMemory;"
        "os=$o.Caption;os_build=$o.BuildNumber} | ConvertTo-Json -Compress"
    )
    try:
        text = subprocess.check_output(
            ["powershell.exe", "-NoProfile", "-Command", query], text=True, timeout=60
        )
        return json.loads(text)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"cpu": platform.processor(), "os": platform.platform()}


def prepare_output(output: Path) -> Path:
    """Create a study directory; a completed study is never replaced."""
    output = output.resolve()
    manifest = output / "manifest.json"
    if manifest.exists():
        status = json.loads(manifest.read_text(encoding="utf-8")).get("status")
        if status == "completed":
            raise FileExistsError(f"completed study must not be replaced: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_manifest(output: Path, document: dict[str, Any]) -> None:
    (output / "manifest.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def base_manifest(protocol_id: str, *scripts: Path) -> dict[str, Any]:
    return {
        "protocol": protocol_id, "status": "running",
        "protocol_document": PROTOCOL,
        "protocol_sha256": sha256(ROOT / PROTOCOL),
        "git_head": git_head(),
        "code_sha256": code_hashes(*scripts),
        "software": software(), "hardware": hardware(),
    }


def write_rows(path: Path, rows: list[dict], fields: Iterable[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"no rows for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(fields or rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def interpreter() -> str:
    return sys.executable
