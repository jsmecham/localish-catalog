import json
from pathlib import Path
import tempfile
import unittest

from check_images import check


class CatalogImageChecks(unittest.TestCase):
    def test_manifest_image_policy(self):
        digest = "a" * 64
        for image, valid in [
            ("ghcr.io/owner/service@sha256:" + digest, True),
            ("registry.example:5000/owner/service@sha256:" + digest, True),
            ("ghcr.io/owner/service:0.27.1@sha256:" + digest, False),
            ("ghcr.io/owner/service:latest", False),
            ("ghcr.io/owner/service@sha256:" + digest.upper(), False),
            ("ghcr.io/owner/service@sha256:abc", False),
            ("service@sha256:" + digest, False),
            (None, False),
        ]:
            with self.subTest(image=image), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = root / "services" / "example" / "manifest.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"example": {"image": image}}))
                self.assertEqual(check(root) == [], valid)

    def test_stdio_uses_bundled_image(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "services" / "example" / "manifest.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"example": {"transport": "stdio"}}))
            self.assertEqual(check(root), [])

    def test_empty_catalog_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(check(Path(directory)))


if __name__ == "__main__":
    unittest.main()
