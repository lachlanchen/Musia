"""Guard the existing guest release while the shared account adapter is incubated."""

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from musia.learning import create_app


class LazyingArtAdoptionTest(unittest.TestCase):
    def test_candidate_manifest_does_not_enable_public_accounts_or_writes(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "apps/shared/lazyingart-app.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            with TestClient(create_app(Path(directory))) as client:
                capabilities = client.get("/api/v1/capabilities").json()
                self.assertTrue(capabilities["readOnly"])
                self.assertFalse(manifest["account"]["enabled"])
                self.assertFalse(capabilities["accounts"]["available"])
                self.assertEqual(manifest["account"]["registrations"], [])
                for feature in manifest["features"]:
                    actual = capabilities.get(feature["id"], {"available": False})
                    available = actual if isinstance(actual, bool) else actual["available"]
                    self.assertEqual(feature["available"], available, feature["id"])
                self.assertEqual(client.get("/api/v1/lessons").status_code, 200)
                self.assertGreater(len(client.get("/api/v1/exercises/first-pulse/audio.wav").content), 44)
                self.assertNotEqual(client.get("/account/authorize").status_code, 200)
                self.assertNotEqual(client.post("/account/token", json={}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
