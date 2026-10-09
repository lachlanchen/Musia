"""Isolated playback tests; no API, network, models, GPU, or live artifacts."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from musia.creator import media


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "song.wav"
        self.source.write_bytes(b"original wave fixture")
        self.expected = checksum(self.source)
        self.original = self.source.read_bytes()
        self.mp3 = self.root / "song.mp3"
        self.manifest = self.root / "playback.json"
        self.source_duration, self.playback_duration = 2.0, 2.04
        self.encoded = b"encoded mp3 fixture"
        self.runner = patch("musia.creator.media.subprocess.run", side_effect=self.fake_run)
        self.run = self.runner.start()
        self.addCleanup(self.runner.stop)

    def fake_run(self, command, **kwargs):
        self.assertTrue(kwargs["check"])
        self.assertGreater(kwargs["timeout"], 0)
        if command[0] == "ffmpeg":
            Path(command[-1]).write_bytes(self.encoded)
            return subprocess.CompletedProcess(command, 0)
        self.assertEqual(command[0], "ffprobe")
        is_mp3 = command[command.index("-f") + 1] == "mp3"
        data = {"format": {"duration": str(self.playback_duration if is_mp3 else self.source_duration)},
                "streams": [{"codec_type": "audio", "codec_name": "mp3" if is_mp3 else "pcm_s16le",
                             "sample_rate": "48000", "channels": 2, "bit_rate": "320000"}]}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(data))

    def prepare(self):
        return media.prepare_playback(self.source, self.expected)

    def lookup(self):
        return media.playback_path(self.source, self.expected)

    def assert_original(self):
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(checksum(self.source), self.expected)
        self.assertEqual(list(self.root.glob(".playback-*")), [])

    def private_write(self, path, content):
        path.write_bytes(content)
        path.chmod(0o600)

    def test_prepare_profile_manifest_full_length_and_idempotence(self):
        source_stat = self.source.stat()
        self.assertEqual(self.prepare(), self.mp3)
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest, {
            "schema": media.SCHEMA, "source_path": "song.wav", "playback_path": "song.mp3",
            "codec": "mp3", "bit_rate": 320000, "channels": 2, "sample_rate": 48000,
            "source_sha256": self.expected, "playback_sha256": checksum(self.mp3),
            "source_duration": 2.0, "playback_duration": 2.04,
        })
        command = next(call.args[0] for call in self.run.call_args_list if call.args[0][0] == "ffmpeg")
        for option, value in (("-c:a", "libmp3lame"), ("-b:a", "320k"), ("-ac", "2"),
                              ("-ar", "48000"), ("-map", "0:a:0"), ("-filter_threads", "1")):
            self.assertEqual(command[command.index(option) + 1], value)
        self.assertTrue(all(command[i + 1] == "1" for i, arg in enumerate(command) if arg == "-threads"))
        self.assertFalse(set(command) & {"-t", "-to", "-ss", "-af", "-filter:a", "-fs"})
        self.assertNotEqual(Path(command[-1]), self.mp3)
        self.assertEqual(command[command.index("-i") + 1], str(self.source))
        for path in (self.mp3, self.manifest):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        before = [path.stat() for path in (self.source, self.mp3, self.manifest)]
        self.run.reset_mock()
        self.assertEqual(self.lookup(), self.mp3)
        self.assertEqual(self.prepare(), self.mp3)
        self.run.assert_not_called()
        self.assertEqual(before, [path.stat() for path in (self.source, self.mp3, self.manifest)])
        self.assertEqual(self.source.stat().st_mtime_ns, source_stat.st_mtime_ns)
        self.assert_original()

    def test_lookup_missing_never_transcodes_or_writes(self):
        self.assertIsNone(self.lookup())
        self.assertEqual(list(self.root.iterdir()), [self.source])
        self.run.assert_not_called()

    def test_bad_expected_digest_or_source_hash_fails_before_subprocess(self):
        for expected in (None, "", "a" * 63, "G" * 64, self.expected.upper(), "0" * 64):
            with self.subTest(expected=expected):
                self.assertIsNone(media.playback_path(self.source, expected))
                with self.assertRaises(ValueError):
                    media.prepare_playback(self.source, expected)
        self.run.assert_not_called()
        self.assert_original()

    def test_source_path_guards(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        wrong_name = self.root / "other.wav"
        wrong_name.write_bytes(self.original)
        directory = self.root / "directory"
        directory.mkdir(mode=0o700)
        (directory / "song.wav").mkdir()
        missing = self.root / "missing" / "song.wav"
        for source in (alias / "song.wav", wrong_name, directory / "song.wav", missing,
                       self.root / "directory" / ".." / "song.wav"):
            with self.subTest(source=source):
                self.assertIsNone(media.playback_path(source, self.expected))
                with self.assertRaises((ValueError, OSError)):
                    media.prepare_playback(source, self.expected)
        self.run.assert_not_called()

    def test_source_symlink_hardlink_fifo_and_unsafe_permissions(self):
        target = self.root / "original.wav"
        self.source.rename(target)
        for kind in ("symlink", "hardlink", "fifo", "writable"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    self.source.symlink_to(target)
                elif kind == "hardlink":
                    os.link(target, self.source)
                elif kind == "fifo":
                    os.mkfifo(self.source, 0o600)
                else:
                    self.source.write_bytes(self.original)
                    self.source.chmod(0o666)
                self.assertIsNone(self.lookup())
                with self.assertRaises(ValueError):
                    self.prepare()
                self.source.unlink()
        self.assertEqual(target.read_bytes(), self.original)
        self.run.assert_not_called()

    def test_root_permissions_and_ownership(self):
        self.root.chmod(0o755)
        self.assertIsNone(self.lookup())
        with self.assertRaises(ValueError):
            self.prepare()
        self.root.chmod(0o700)
        with patch.object(media.os, "getuid", return_value=os.getuid() + 1):
            self.assertIsNone(self.lookup())
            with self.assertRaises(ValueError):
                self.prepare()
        self.run.assert_not_called()

    def test_foreign_file_ownership(self):
        real_check = media._check_file

        def foreign(info, limit, private):
            with patch.object(media.os, "getuid", return_value=info.st_uid + 1):
                return real_check(info, limit, private)

        with patch.object(media, "_check_file", side_effect=foreign):
            self.assertIsNone(self.lookup())
            with self.assertRaises(ValueError):
                self.prepare()
        self.run.assert_not_called()

    def test_source_size_bound_and_empty_file(self):
        for size in (0, media.MAX_FILE_BYTES + 1):
            with self.subTest(size=size):
                with self.source.open("wb") as stream:
                    stream.truncate(size)
                self.assertIsNone(self.lookup())
                with self.assertRaises(ValueError):
                    self.prepare()
        self.run.assert_not_called()

    def test_unsafe_destinations_refused_without_overwrite(self):
        target = self.root / "unrelated"
        target.write_bytes(b"preserve")
        for path in (self.mp3, self.manifest):
            for kind in ("symlink", "dangling", "hardlink", "directory", "fifo", "public", "oversize"):
                with self.subTest(path=path.name, kind=kind):
                    if kind in ("symlink", "dangling"):
                        path.symlink_to(target if kind == "symlink" else self.root / "absent")
                    elif kind == "hardlink":
                        os.link(target, path)
                    elif kind == "directory":
                        path.mkdir()
                    elif kind == "fifo":
                        os.mkfifo(path, 0o600)
                    else:
                        self.private_write(path, b"partial")
                        if kind == "public":
                            path.chmod(0o644)
                        else:
                            with path.open("r+b") as stream:
                                stream.truncate(media.MAX_FILE_BYTES + 1 if path == self.mp3
                                                else media.MAX_MANIFEST_BYTES + 1)
                    before = path.lstat()
                    self.assertIsNone(self.lookup())
                    with self.assertRaises(ValueError):
                        self.prepare()
                    self.assertEqual(path.lstat(), before)
                    if kind == "directory":
                        path.rmdir()
                    else:
                        path.unlink()
        self.run.assert_not_called()
        self.assertEqual(target.read_bytes(), b"preserve")
        self.assert_original()

    def test_invalid_owned_partials_repaired_after_success_only(self):
        for audio, manifest in ((b"partial", None), (None, b"{}"),
                                (b"", b""), (b"partial", b"not json")):
            with self.subTest(audio=audio, manifest=manifest):
                self.mp3.unlink(missing_ok=True)
                self.manifest.unlink(missing_ok=True)
                if audio is not None:
                    self.private_write(self.mp3, audio)
                if manifest is not None:
                    self.private_write(self.manifest, manifest)
                self.assertIsNone(self.lookup())
                self.assertEqual(self.prepare(), self.mp3)
                self.assertEqual(self.lookup(), self.mp3)
                self.assert_original()

    def test_lookup_rejects_manifest_tampering_without_subprocess(self):
        self.prepare()
        valid = json.loads(self.manifest.read_text())
        mutations = [{"schema": "future"}, {"source_path": "../song.wav"},
                     {"playback_path": str(self.mp3)}, {"playback_path": "../elsewhere.mp3"},
                     {"source_sha256": "0" * 64}, {"playback_sha256": "0" * 64},
                     {"source_duration": 241}, {"playback_duration": 1},
                     {"playback_duration": float("nan")}, {"playback_duration": float("inf")},
                     {"playback_duration": True}, {"playback_duration": "2.04"},
                     {"bit_rate": 128000}, {"channels": 1}, {"sample_rate": 44100},
                     {"extra": "unrecognized"}]
        self.run.reset_mock()
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.manifest.write_text(json.dumps({**valid, **mutation}))
                self.assertIsNone(self.lookup())
        for raw in (b"[]", b"null", b"invalid", b"\xff", b"[" * 2000):
            with self.subTest(raw=raw[:12]):
                self.manifest.write_bytes(raw)
                self.assertIsNone(self.lookup())
        self.run.assert_not_called()

    def test_lookup_rehashes_both_files_and_checks_bounds(self):
        self.prepare()
        self.run.reset_mock()
        self.mp3.write_bytes(b"modified mp3")
        self.assertIsNone(self.lookup())
        self.mp3.write_bytes(self.encoded)
        self.source.write_bytes(b"modified wav")
        self.assertIsNone(self.lookup())
        self.source.write_bytes(self.original)
        for path, limit in ((self.mp3, media.MAX_FILE_BYTES), (self.manifest, media.MAX_MANIFEST_BYTES)):
            saved = path.read_bytes()
            with path.open("wb") as stream:
                stream.truncate(limit + 1)
            self.assertIsNone(self.lookup())
            path.write_bytes(saved)
        self.assertEqual(self.lookup(), self.mp3)
        self.run.assert_not_called()

    def test_encoder_nonzero_timeout_and_missing_executable_preserve_original_and_partials(self):
        for error in (subprocess.CalledProcessError(1, "ffmpeg"),
                      subprocess.TimeoutExpired("ffmpeg", 120), FileNotFoundError("ffmpeg")):
            with self.subTest(error=type(error).__name__):
                self.private_write(self.mp3, b"old partial")
                self.private_write(self.manifest, b"old manifest")

                def fail(command, **kwargs):
                    if command[0] == "ffmpeg":
                        Path(command[-1]).write_bytes(b"unfinished")
                        raise error
                    return self.fake_run(command, **kwargs)

                self.run.side_effect = fail
                with self.assertRaises(type(error)):
                    self.prepare()
                self.assertEqual(self.mp3.read_bytes(), b"old partial")
                self.assertEqual(self.manifest.read_bytes(), b"old manifest")
                self.assertIsNone(self.lookup())
                self.assert_original()

    def test_source_and_playback_duration_guards(self):
        for source, playback in ((241, 241), (0, 0), (float("nan"), 2),
                                 (2, 1.8), (2, 2.121), (240, 240.024), (2, 0)):
            with self.subTest(source=source, playback=playback):
                self.source_duration, self.playback_duration = source, playback
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse(self.mp3.exists())
                self.assertFalse(self.manifest.exists())
                self.assert_original()

    def test_bad_probe_output_and_nonzero(self):
        for result in ("not json", "{}", '{"format":{"duration":"N/A"}}'):
            with self.subTest(result=result):
                self.run.side_effect = None
                self.run.return_value = subprocess.CompletedProcess([], 0, stdout=result)
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assert_original()
        self.run.side_effect = subprocess.CalledProcessError(1, "ffprobe")
        with self.assertRaises(subprocess.CalledProcessError):
            self.prepare()
        self.assert_original()

    def test_wrong_encoded_profile_rejected(self):
        def wrong_profile(command, **kwargs):
            result = self.fake_run(command, **kwargs)
            if command[0] == "ffprobe" and command[command.index("-f") + 1] == "mp3":
                data = json.loads(result.stdout)
                data["streams"][0]["sample_rate"] = "44100"
                result.stdout = json.dumps(data)
            return result

        self.run.side_effect = wrong_profile
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.manifest.exists())
        self.assert_original()

    def test_source_change_during_encoding_rejected(self):
        def mutate(command, **kwargs):
            result = self.fake_run(command, **kwargs)
            if command[0] == "ffmpeg":
                self.source.write_bytes(b"changed by another writer")
            return result

        self.run.side_effect = mutate
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.prepare()
        self.assertFalse(self.mp3.exists())
        self.assertFalse(self.manifest.exists())
        self.assertIsNone(self.lookup())
        self.assertEqual(list(self.root.glob(".playback-*")), [])

    def test_destination_change_during_encoding_not_overwritten(self):
        def mutate(command, **kwargs):
            result = self.fake_run(command, **kwargs)
            if command[0] == "ffmpeg":
                self.private_write(self.mp3, b"other writer")
            return result

        self.run.side_effect = mutate
        with self.assertRaisesRegex(ValueError, "destinations changed"):
            self.prepare()
        self.assertEqual(self.mp3.read_bytes(), b"other writer")
        self.assertFalse(self.manifest.exists())
        self.assert_original()

    def test_manifest_is_committed_last_and_interruption_is_recoverable(self):
        replace = os.replace

        def interrupted(source, destination):
            self.assertIsNone(self.lookup())
            if destination == self.manifest:
                raise OSError("simulated publication failure")
            return replace(source, destination)

        with patch.object(media.os, "replace", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.prepare()
        self.assertIsNone(self.lookup())
        self.assertFalse(self.manifest.exists())
        self.assert_original()
        self.assertEqual(self.prepare(), self.mp3)
        self.assertEqual(self.lookup(), self.mp3)


class RealFFmpegPlaybackTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real playback test requires ffmpeg and ffprobe")
    def test_short_generated_tone(self):
        encoders = subprocess.run(["ffmpeg", "-v", "error", "-encoders"],
                                  capture_output=True, text=True, check=True, timeout=15)
        if "libmp3lame" not in encoders.stdout:
            self.skipTest("Real playback test requires FFmpeg libmp3lame")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            source = root / "song.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-threads", "1",
                            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1.5",
                            "-ac", "2", "-c:a", "pcm_s16le", "-threads", "1",
                            "-filter_threads", "1", str(source)],
                           stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=15)
            original = source.read_bytes()
            expected = checksum(source)
            playback = media.prepare_playback(source, expected)
            manifest = json.loads((root / "playback.json").read_text())
            self.assertEqual(playback, root / "song.mp3")
            self.assertEqual(media.playback_path(source, expected), playback)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(manifest["source_sha256"], expected)
            self.assertEqual(manifest["playback_sha256"], checksum(playback))
            self.assertAlmostEqual(manifest["source_duration"], 1.5, places=3)
            self.assertLessEqual(abs(manifest["source_duration"] - manifest["playback_duration"]), 0.12)
            self.assertLess(playback.stat().st_size, source.stat().st_size)
            before = playback.stat()
            with patch.object(media.subprocess, "run", side_effect=AssertionError("Must reuse")):
                self.assertEqual(media.prepare_playback(source, expected), playback)
            self.assertEqual(playback.stat(), before)
            self.assertEqual(list(root.glob(".playback-*")), [])


if __name__ == "__main__":
    unittest.main()
