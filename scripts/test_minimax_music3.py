#!/usr/bin/env python3
"""Small CPU-only regression checks for Musia's Music 3 input contract."""

import json
import tempfile
import unittest
from pathlib import Path

from run_minimax_music3 import export_gain, local_config, true_peak_gain, validate_lyrics, verify_download_manifest
from download_minimax_music3 import sha256_file


class InputContractTests(unittest.TestCase):
    def test_export_only_attenuates_and_rejects_silence(self):
        self.assertEqual(export_gain(0.5), 1.0)
        self.assertAlmostEqual(export_gain(2.0) * 2, 10 ** (-1 / 20))
        for invalid in (0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                export_gain(invalid)

    def test_true_peak_headroom_does_not_compress_or_amplify(self):
        self.assertEqual(true_peak_gain(-4.0), 1.0)
        self.assertAlmostEqual(true_peak_gain(0.1), 10 ** (-2.2 / 20))

    def test_accepts_native_mandarin(self):
        text = "[Verse]\n半首琴声 留在长安\n"
        self.assertEqual(validate_lyrics(text), text)

    def test_rejects_lyrics_after_tag(self):
        with self.assertRaisesRegex(ValueError, "own line"):
            validate_lyrics("[Verse] Words that would be silently dropped")

    def test_rejects_empty_lyrics(self):
        for text in ("", "  \n", "[Verse]\n[Chorus]"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_lyrics(text)

    def test_all_components_bound_to_local_directory(self):
        config = {"_class_name": "MiniMaxMusic3ModularPipeline", "language_model": [
            "transformers", "Qwen3ForCausalLM", {
                "pretrained_model_name_or_path": "MiniMaxAI/MiniMax-Music3",
                "revision": "main", "subfolder": "language_model"}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "modular_model_index.json"
            source.write_text(json.dumps(config))
            bound = local_config(root)
            self.assertEqual(bound["language_model"][2]["pretrained_model_name_or_path"], str(root.resolve()))
            self.assertIsNone(bound["language_model"][2]["revision"])
            self.assertEqual(json.loads(source.read_text()), config)

    def test_partial_download_is_not_accepted_by_file_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "weights.bin").write_bytes(b"abc")
            manifest = {"model_id": "MiniMaxAI/MiniMax-Music3", "files": [
                {"path": "weights.bin", "bytes": 3, "expected_sha256": "test", "sha256_verified": True}]}
            (root / "musia-download.json").write_text(json.dumps(manifest))
            self.assertEqual(verify_download_manifest(root), manifest)
            (root / "weights.bin.aria2").touch()
            with self.assertRaisesRegex(RuntimeError, "Incomplete"):
                verify_download_manifest(root)

    def test_streamed_sha256_on_supported_python(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "file"
            path.write_bytes(b"abc")
            self.assertEqual(sha256_file(path), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


if __name__ == "__main__":
    unittest.main()
