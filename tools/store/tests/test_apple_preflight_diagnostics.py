import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apple_internal_preflight as preflight


class MetadataCommands:
    def __init__(self):
        self.names = []

    def run(self, argv, limit, env=None):
        self.names.append(argv[0])
        return {"exit": 0, "stdout": "", "stderr": ""}


class PartialDiagnosticsTests(unittest.TestCase):
    def test_occupied_gate_retains_safe_reason_without_probe_or_secret(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            config.write_text(json.dumps({
                "bundle_id": "art.lazying.musia", "apple_team": "Q8M2S2FY77",
                "private_value": "never-emit-this"}))
            config.chmod(0o600)
            commands, result = MetadataCommands(), {}
            busy = [{"pid": 42, "ppid": 1, "pgid": 42,
                     "started": "test", "comm": "python3", "reason": "external-python-runner-unqualified"}]
            with patch.object(preflight.platform, "system", return_value="Darwin"), \
                 patch.object(preflight, "parse_processes", return_value={}), \
                 patch.object(preflight, "own_chain", return_value={}), \
                 patch.object(preflight, "classify_processes", return_value=busy):
                with self.assertRaisesRegex(RuntimeError, "Host occupied"):
                    preflight.collect(config, commands, result)
            self.assertEqual(result["active_tools"], busy)
            self.assertIn("guard", result)
            self.assertNotIn("never-emit-this", json.dumps(result))
            self.assertNotIn("security", commands.names)
            self.assertNotIn("xcrun", commands.names)
            self.assertNotIn("configured_developer", result)


if __name__ == "__main__":
    unittest.main()
