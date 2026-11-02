#!/usr/bin/env python3
"""Check that index.json describes the catalog's manifests without downloading anything."""

import base64
import json
from pathlib import Path
import re
import struct
import sys


MAXIMUM_DOCUMENT_BYTES = 256 * 1024
MAXIMUM_ICON_BYTES = 64 * 1024
MAXIMUM_ICON_DIMENSION = 512
ICON_PREFIX = "data:image/png;base64,"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SLUG = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")
RESERVED_SLUGS = {
    "admin", "api", "assets", "services", "connect", "auth", "oauth",
    "authorize", "token", "revoke", "add", "manifest.webmanifest",
}


def check(root: Path) -> list[str]:
    failures = []
    index_path = root / "index.json"
    try:
        if index_path.stat().st_size > MAXIMUM_DOCUMENT_BYTES:
            failures.append("index.json: keep the complete index within 256 KiB.")
        index = json.loads(index_path.read_text())
    except (OSError, ValueError) as error:
        return failures + [f"index.json: {error}"]
    entries = index.get("services") if isinstance(index, dict) else None
    if not isinstance(entries, list):
        return failures + ['index.json: expected an object with a "services" array.']

    indexed = set()
    for position, entry in enumerate(entries):
        label = f"index.json services[{position}]"
        if not isinstance(entry, dict):
            failures.append(f"{label}: expected an object.")
            continue
        slug = entry.get("slug")
        if isinstance(slug, str):
            label = f"index.json ({slug})"
        failures.extend(f"{label}: {failure}" for failure in check_entry(root, entry, indexed))

    for manifest in sorted(root.glob("services/*/manifest.json")):
        slug = manifest.parent.name
        if slug not in indexed:
            failures.append(f"{manifest.relative_to(root)} ({slug}): add an entry to index.json.")
    return failures


def check_entry(root: Path, entry: dict, indexed: set) -> list[str]:
    failures = []
    for field in ("slug", "name", "description", "manifest"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            failures.append(f'"{field}" must be a non-empty string.')
    if failures:
        return failures
    slug = entry["slug"]
    if len(slug.encode()) > 40 or SLUG.fullmatch(slug) is None or slug in RESERVED_SLUGS:
        failures.append("use a lowercase slug of letters, digits, and inner hyphens that Localish does not reserve.")
    if slug in indexed:
        failures.append("list each service once.")
    indexed.add(slug)
    expected = f"services/{slug}/manifest.json"
    if entry["manifest"] != expected:
        return failures + [f'"manifest" must be "{expected}".']
    for field in ("icon", "transport"):
        if field in entry and not isinstance(entry[field], str):
            failures.append(f'"{field}" must be a string when present.')

    manifest_path = root / expected
    try:
        if manifest_path.stat().st_size > MAXIMUM_DOCUMENT_BYTES:
            failures.append(f"{expected}: keep the manifest within 256 KiB.")
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as error:
        return failures + [f"{expected}: {error}"]
    if not isinstance(manifest, dict) or list(manifest) != [slug] or not isinstance(manifest[slug], dict):
        return failures + [f"{expected}: the manifest must contain exactly one service keyed by the slug."]
    service = manifest[slug]

    if entry["name"] != service.get("displayName"):
        failures.append('"name" must match the manifest\'s "displayName".')
    if entry.get("transport", "http") != service.get("transport", "http"):
        failures.append('"transport" must match the manifest\'s transport.')
    icon = service.get("icon")
    if "icon" in service and not isinstance(icon, str):
        failures.append(f"{expected}: \"icon\" must be a string when present.")
    elif entry.get("icon") != icon:
        failures.append('copy the manifest\'s "icon" into the index entry, and omit it when the manifest has none.')
    elif isinstance(icon, str):
        failures.extend(check_icon(icon))
    return failures


def check_icon(icon: str) -> list[str]:
    """Validate the data URL's shape and PNG header; Localish decodes the pixels at install."""
    if not icon.startswith(ICON_PREFIX):
        return [f'"icon" must start with "{ICON_PREFIX}".']
    try:
        data = base64.b64decode(icon[len(ICON_PREFIX):], validate=True)
    except ValueError:
        return ['"icon" must contain standard base64 data.']
    if not data or len(data) > MAXIMUM_ICON_BYTES:
        return ['"icon" must decode to a PNG of at most 64 KiB.']
    if len(data) < 33 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        return ['"icon" must be a PNG image.']
    width, height = struct.unpack(">II", data[16:24])
    if not (1 <= width <= MAXIMUM_ICON_DIMENSION and 1 <= height <= MAXIMUM_ICON_DIMENSION):
        return ['"icon" must be at most 512 pixels on each side.']
    if b"acTL" in data:
        return ['"icon" must contain a single frame, not an animation.']
    return []


if __name__ == "__main__":
    failures = check(Path(__file__).resolve().parent.parent)
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        sys.exit(1)
    print("Catalog index passed.")
