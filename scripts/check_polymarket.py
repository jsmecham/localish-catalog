#!/usr/bin/env python3
"""Run launcher checks with the package and Python selected by the manifest."""

import json
from pathlib import Path
import subprocess


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    service = json.loads((root / "services/polymarket/manifest.json").read_text())["polymarket"]
    command = service["command"]
    if command[-2] != "-c":
        raise SystemExit("Expected the Polymarket manifest's inline Python launcher")
    subprocess.run(
        command[:-2] + ["-B", str(root / "scripts/polymarket/mode_checks.py")],
        cwd=root,
        check=True,
        timeout=300,
    )
