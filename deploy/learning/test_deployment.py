"""Offline tests for the release/ingress boundary; no SSH or services."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


remote = module("musia_deploy_remote", HERE / "remote.py")
builder = module("musia_deploy_builder", HERE.parents[1] / "scripts/deploy_musia_learning.py")


class DeploymentTest(unittest.TestCase):
    def test_additive_ingress_preserves_existing_bytes(self):
        original = "{\n admin 127.0.0.1:12019\n}\nedit.lazying.art {\n respond 200\n}\n"
        changed = remote.replace_site(original, remote.site_block(None, tls_only=True))
        self.assertTrue(changed.startswith(original))
        self.assertEqual(changed.count(remote.BEGIN), 1)
        self.assertIn('respond "Musia deployment pending" 503', changed)

    def test_replace_only_owned_block(self):
        original = "before\n" + remote.site_block(None, tls_only=True) + "after\n"
        changed = remote.replace_site(original, remote.BEGIN + "\nreplacement\n" + remote.END + "\n")
        self.assertEqual(changed, "before\n" + remote.BEGIN + "\nreplacement\n" + remote.END + "\nafter\n")

    def test_unmanaged_host_and_duplicate_markers_refused(self):
        for original in ("musia.lazying.art { respond 200 }", remote.BEGIN * 2 + remote.END):
            with self.assertRaises(AssertionError):
                remote.replace_site(original, "replacement")

    def test_route_list_is_exact_not_wildcard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "release.json").write_text(json.dumps({"staticPaths": ["/", "/app.js"], "songIds": ["first-pulse", "public-song"]}))
            result = remote.site_block(root)
            self.assertIn("127.0.0.1:18440", result)
            self.assertIn("/api/v1/songs/public-song", result)
            self.assertNotIn("/api/*", result)
            self.assertIn("not method GET HEAD", result)
            self.assertIn("handle @musia_write {", result)
            self.assertLess(result.index("handle @musia_write"), result.index("handle @musia_read"))
            self.assertIn("header_up -Authorization", result)
            (root / "release.json").write_text(json.dumps({"staticPaths": ["/*"], "songIds": []}))
            with self.assertRaises(AssertionError):
                remote.site_block(root)

    def test_archive_is_deterministic_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "ok.txt").write_text("public data")
            first, second = root / "one.tgz", root / "two.tgz"
            builder.archive(source, first)
            builder.archive(source, second)
            self.assertEqual(builder.digest(first), builder.digest(second))
            (source / "not-allowed").symlink_to("/etc/passwd")
            with self.assertRaises(RuntimeError):
                builder.archive(source, root / "bad.tgz")

    def test_single_worker_unprivileged_service(self):
        text = (HERE / "musia-learning.service.in").read_text()
        for required in ("User=musia-learning", "--host 127.0.0.1", "--workers 1", "--limit-concurrency 8", "MemoryMax=128M", "ProtectSystem=strict", "--no-proxy-headers"):
            self.assertIn(required, text)
        self.assertNotIn("--reload", text)


if __name__ == "__main__":
    unittest.main()
