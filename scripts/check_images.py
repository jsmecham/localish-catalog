#!/usr/bin/env python3
"""Check catalog image pins without downloading or executing services."""

import json
from pathlib import Path
import re
import sys


IMAGE_REFERENCE = re.compile(
    r"(?:localhost|[a-z0-9.-]+\.[a-z0-9.-]+)(?::[0-9]+)?/"
    r"[a-z0-9]+(?:(?:[._-]+|/)[a-z0-9]+)*@sha256:[0-9a-f]{64}"
)


def check(root: Path) -> list[str]:
    failures = []
    manifests = sorted(root.glob("services/*/manifest.json"))
    if not manifests:
        return ["No service manifests found."]
    for path in manifests:
        try:
            services = json.loads(path.read_text())
            for slug, service in services.items():
                image = service.get("image")
                if service.get("transport", "http") == "stdio" and image is None:
                    continue
                if not isinstance(image, str) or IMAGE_REFERENCE.fullmatch(image) is None:
                    failures.append(
                        f"{path.relative_to(root)} ({slug}): use an explicit registry/"
                        "repository@sha256: reference with 64 lowercase hex digits and no tag."
                    )
        except (OSError, ValueError, AttributeError) as error:
            failures.append(f"{path.relative_to(root)}: {error}")
    return failures


if __name__ == "__main__":
    failures = check(Path(__file__).resolve().parent.parent)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        sys.exit(1)
    print("Catalog image pins passed.")
