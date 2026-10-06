#!/usr/bin/env python3
import contextlib
import io
import json
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

import run_ace_candidate_sweep as sweep


class CandidateSweepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lyrics = self.root / "lyrics.txt"
        self.lyrics.write_text("[Verse]\nOriginal lyric\n", encoding="utf-8")
        self.caption = self.root / "caption.txt"
        self.caption.write_text("Warm acoustic pop", encoding="utf-8")
        self.out = self.root / "sweep"
        self.args = ["--lyrics", str(self.lyrics), "--caption", str(self.caption),
                     "--output-dir", str(self.out), "--seeds", "101", "102", "103"]

    def run_sweep(self, extra):
        with patch.object(sweep.subprocess, "check_output", return_value="test-commit\n"), \
                patch.object(sweep.subprocess, "run") as generate, \
                contextlib.redirect_stdout(io.StringIO()):
            sweep.main(self.args + extra)
        return generate

    def test_japanese_dry_run_writes_parseable_configs_without_inference(self):
        generate = self.run_sweep(["--language", "ja", "--dry-run"])
        generate.assert_not_called()
        request = json.loads((self.out / "request.json").read_text())
        self.assertEqual(request["vocal_language"], "ja")
        configs = sorted(self.out.glob("batch-*/ace.toml"))
        self.assertEqual(len(configs), 2)
        for path in configs:
            data = tomllib.loads(path.read_text())
            self.assertEqual(data["vocal_language"], "ja")
            self.assertFalse(data["thinking"])
            self.assertFalse(data["use_cot_lyrics"])
            self.assertEqual(data["config_path"], "acestep-v15-xl-turbo")
            self.assertEqual(data["batch_size"], len(data["seeds"]))
        self.assertFalse((self.out / "candidates.json").exists())

    def test_default_preserves_chinese_configuration(self):
        self.run_sweep(["--dry-run"])
        data = tomllib.loads((self.out / "batch-101-102/ace.toml").read_text())
        self.assertEqual(data["vocal_language"], "zh")

    def test_cannot_resume_with_a_different_language(self):
        self.run_sweep(["--language", "ja", "--dry-run"])
        with self.assertRaisesRegex(ValueError, "different inputs"):
            self.run_sweep(["--language", "en", "--dry-run"])

    def test_legacy_request_is_chinese_not_japanese(self):
        self.run_sweep(["--dry-run"])
        path = self.out / "request.json"
        old = json.loads(path.read_text())
        old.pop("vocal_language")
        path.write_text(json.dumps(old))
        with self.assertRaisesRegex(ValueError, "different inputs"):
            self.run_sweep(["--language", "ja", "--dry-run"])
        self.run_sweep(["--dry-run"])

    def test_dry_run_does_not_erase_existing_candidate_manifest(self):
        self.run_sweep(["--dry-run"])
        path = self.out / "candidates.json"
        path.write_text('[{"evidence": "preserve"}]\n')
        self.run_sweep(["--dry-run"])
        self.assertEqual(path.read_text(), '[{"evidence": "preserve"}]\n')

    def test_rejects_unknown_language_code(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_sweep(["--language", "jp", "--dry-run"])


if __name__ == "__main__":
    unittest.main()
