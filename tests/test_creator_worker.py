import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from musia.creator.worker import resource_check


class WorkerResources(unittest.TestCase):
    def check(self, row, *, device="0", available=32*1024*1024, swapfree=1024):
        memory = f"MemAvailable: {available} kB\nSwapTotal: 1024 kB\nSwapFree: {swapfree} kB"
        with patch("pathlib.Path.read_text", return_value=memory), \
             patch.dict("os.environ", {"CUDA_VISIBLE_DEVICES":device}), \
             patch("subprocess.check_output", return_value=row) as query:
            resource_check()
            self.assertIn("--id="+device, query.call_args.args[0])

    def test_idle_small_resident_services_allowed(self):
        self.check("24564, 23514, 0\n")

    def test_busy_or_insufficient_gpu_stays_queued(self):
        for row in ("24564, 23514, 40", "24564, 19503, 0", "49152, 23000, 0"):
            with self.subTest(row=row), self.assertRaises(RuntimeError):
                self.check(row)

    def test_memory_swap_and_device_guard(self):
        for kwargs in ({"available":1024}, {"swapfree":0}, {"device":"0,1"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                self.check("24564, 23514, 0", **kwargs)


class CatalogPreservesCreator(unittest.TestCase):
    def test_catalog_update_preserves_scoped_creator_bytes(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("learning_deploy", root/"deploy/learning/remote.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            release = Path(folder)
            (release/"release.json").write_text('{"staticPaths":[],"songIds":[]}')
            block = module.site_block(release)
            fragment = (root/"deploy/creator/caddy-creator.caddy").read_text()
            previous = block.replace("    request_body {", fragment+"    request_body @musia_not_creator {")
            result = module.replace_site("# unrelated before\n"+previous+"# unrelated after\n", block)
            self.assertIn(fragment, result)
            self.assertEqual(result.count("# BEGIN MUSIA CREATOR SCOPED"), 1)
            self.assertIn("request_body @musia_not_creator", result)
            self.assertTrue(result.endswith("# unrelated after\n"))
            self.assertTrue(result.startswith("# unrelated before\n"))
            with self.assertRaises(AssertionError):
                module.replace_site(previous.replace("# END MUSIA CREATOR SCOPED", "# broken"), block)
