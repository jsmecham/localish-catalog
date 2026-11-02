import base64
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from check_index import check


def png(width=1, height=1, extra=b""):
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    pixels = zlib.compress(b"\x00" + b"\x00\x00\x00\xff" * width)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + extra + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")


def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


def icon(data=None):
    return "data:image/png;base64," + base64.b64encode(png() if data is None else data).decode()


class Catalog:
    def __init__(self, root):
        self.root = Path(root)
        self.entries = []

    def add(self, slug, index=None, manifest=None, indexed=True):
        service = {"displayName": slug.title(), "transport": "stdio", "command": ["npx", "-y", slug]}
        service.update(manifest or {})
        path = self.root / "services" / slug / "manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({slug: service}))
        entry = {
            "slug": slug, "name": service["displayName"], "description": "Does one thing.",
            "manifest": f"services/{slug}/manifest.json", "transport": service["transport"],
        }
        if "icon" in service:
            entry["icon"] = service["icon"]
        entry.update(index or {})
        entry = {key: value for key, value in entry.items() if value is not None}
        if indexed:
            self.entries.append(entry)
        return entry

    def write(self, index=None):
        (self.root / "index.json").write_text(json.dumps({"services": self.entries} if index is None else index))
        return check(self.root)


class CatalogIndexChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.catalog = Catalog(directory.name)

    def test_matching_entries_pass(self):
        self.catalog.add("plain")
        self.catalog.add("pictured", manifest={"icon": icon()})
        self.catalog.add("served", manifest={"transport": "http", "image": "ghcr.io/o/s@sha256:" + "a" * 64})
        self.assertEqual(self.catalog.write(), [])

    def test_name_must_match_display_name(self):
        self.catalog.add("example", index={"name": "Example Service"})
        self.assertIn("displayName", "\n".join(self.catalog.write()))

    def test_transport_must_match(self):
        self.catalog.add("example", index={"transport": "http"})
        self.assertIn("transport", "\n".join(self.catalog.write()))

    def test_icon_is_copied_exactly(self):
        for index, manifest in [
            ({"icon": None}, {"icon": icon()}),
            ({"icon": icon()}, {}),
            ({"icon": icon(png(2, 2))}, {"icon": icon()}),
        ]:
            with self.subTest(index=index.get("icon") is not None, manifest=bool(manifest)):
                self.setUp()
                self.catalog.add("example", index=index, manifest=manifest)
                self.assertIn("copy the manifest", "\n".join(self.catalog.write()))

    def test_icon_format(self):
        oversized = png(1, 1, extra=chunk(b"tEXt", b"x" * (64 * 1024)))
        for data, valid in [
            (png(), True),
            (png(512, 512), True),
            (png(513, 1), False),
            (png(1, 0), False),
            (oversized, False),
            (b"GIF89a" + png()[6:], False),
            (png(extra=chunk(b"acTL", b"\x00" * 8)), False),
        ]:
            with self.subTest(data=data[:40]):
                self.setUp()
                self.catalog.add("example", manifest={"icon": icon(data)})
                self.assertEqual(self.catalog.write() == [], valid)
        for value in ["https://example.invalid/icon.png", "data:image/png;base64,***", "data:image/png;base64,"]:
            with self.subTest(value=value):
                self.setUp()
                self.catalog.add("example", manifest={"icon": value})
                self.assertTrue(self.catalog.write())

    def test_every_manifest_is_indexed_once(self):
        self.catalog.add("listed")
        self.catalog.add("missing", indexed=False)
        failures = self.catalog.write()
        self.assertEqual(len(failures), 1)
        self.assertIn("services/missing/manifest.json", failures[0])
        self.catalog.entries.append(dict(self.catalog.entries[0]))
        self.assertIn("once", "\n".join(self.catalog.write()))

    def test_manifest_path_and_contents(self):
        self.catalog.add("example", index={"manifest": "services/other/manifest.json"})
        self.assertIn('"manifest" must be', "\n".join(self.catalog.write()))
        self.catalog.entries.clear()
        self.catalog.add("second", indexed=True)
        (self.catalog.root / "services/second/manifest.json").write_text(json.dumps({"second": {}, "extra": {}}))
        self.assertIn("exactly one service", "\n".join(self.catalog.write()))

    def test_slugs(self):
        for slug, valid in [("ok-slug", True), ("Bad", False), ("-lead", False), ("api", False), ("a" * 41, False)]:
            with self.subTest(slug=slug):
                self.setUp()
                self.catalog.add(slug)
                self.assertEqual(self.catalog.write() == [], valid)

    def test_required_fields(self):
        for field in ("slug", "name", "description", "manifest"):
            with self.subTest(field=field):
                self.setUp()
                self.catalog.add("example", index={field: " "})
                self.assertIn(f'"{field}"', "\n".join(self.catalog.write()))

    def test_document_sizes(self):
        self.catalog.add("example", index={"description": "x" * (256 * 1024)})
        self.assertIn("256 KiB", "\n".join(self.catalog.write()))
        self.catalog.entries.clear()
        self.catalog.add("padded", manifest={"notes": "x" * (256 * 1024)})
        self.assertIn("manifest within 256 KiB", "\n".join(self.catalog.write()))

    def test_index_shape(self):
        self.catalog.add("example")
        self.assertTrue(self.catalog.write(index=[]))
        self.assertTrue(self.catalog.write(index={"services": [1]}))
        (self.catalog.root / "index.json").write_text("{")
        self.assertTrue(check(self.catalog.root))
        (self.catalog.root / "index.json").unlink()
        self.assertTrue(check(self.catalog.root))


if __name__ == "__main__":
    unittest.main()
