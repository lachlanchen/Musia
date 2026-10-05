"""Small, offline API and sample-clock tests; run with unittest discovery."""

from __future__ import annotations

import copy
import io
import json
import math
import os
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from musia import learning


class LearningAPITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.item = {"id": "public-song", "kind": "song", "title": "Public Song", "artist": "Musia",
                     "manifest": "data/songs/public-song/manifest.json", "cover": "assets/covers/public-song.png"}
        self.catalog = {"version": 1, "items": [self.item]}
        self.manifest = {
            "id": "public-song", "title": "Public Song", "artist": "Musia", "duration": 12,
            "provenance": {"source": "/home/private/master.wav", "apiKey": "SECRET"},
            "assets": {
                "primaryAudio": {"id": "vocal-en", "label": "English vocal", "languageCode": "en",
                                 "lyricSetId": "en-vocal", "duration": 12,
                                 "src": "https://lazyingart.github.io/MusiaSongs/audio/public-en.mp3"},
                "alternateAudio": [{"id": "vocal-ja", "label": "Japanese vocal", "languageCode": "ja",
                                    "lyricSetId": "ja-vocal", "duration": 14,
                                    "src": "https://lazyingart.github.io/MusiaSongs/audio/public-ja.mp3"}],
            },
            "lyricSets": [{"id": "en-vocal", "languageCode": "en", "tracks": [
                {"code": "en", "path": "lyrics/en-vocal/en.json"},
                {"code": "ja", "path": "lyrics/en-vocal/ja.json"}]},
                {"id": "ja-vocal", "languageCode": "ja", "tracks": [{"code": "ja", "path": "lyrics/ja-vocal/ja.json"}]}],
        }
        self.study = {"mediaId": "public-song", "defaultAssetId": "vocal-en", "assets": {}}
        for index, asset in enumerate([self.manifest["assets"]["primaryAudio"], *self.manifest["assets"]["alternateAudio"]]):
            self.study["assets"][asset["id"]] = {
                "src": asset["src"], "languageCode": asset["languageCode"], "bpm": 90 + index,
                "timeSignature": "4/4", "beatConfidence": "verified", "chordConfidence": "analysis",
                "melodyConfidence": "verified", "beatSource": "/home/private/beats.json",
                "melodySource": "data/runs/private/analysis/melody_f0.csv",
                "beats": [{"time": 1 + index, "index": 0, "downbeat": True}, {"time": 2 + index, "index": 1}],
                "chords": [{"start": 1 + index, "end": 3 + index, "name": "Em" if index == 0 else "Am",
                            "confidence": 0.8, "private": "SECRET"}],
                "melody": {"source": "/home/private/melody.csv", "lines": [{"tokens": [
                    {"start": 1 + index, "end": 2 + index, "note": "E4", "numberNote": "3", "text": "Sun",
                     "midi": 64, "source": "SECRET"}]}]},
            }
        self.en_lyrics = {"language": {"code": "en"}, "provenance": "SECRET", "lines": [
            {"id": "en-1", "start": 1, "end": 3, "text": "Sun", "source": "SECRET", "tokens": [
                {"text": "Sun", "start": 1, "end": 2, "pinyin": "sun1", "source": "SECRET"}]},
            {"id": "rest", "start": 3, "end": 4, "text": "Instrumental", "role": "instrumental"},
        ]}
        self.ja_lyrics = {"language": {"code": "ja"}, "lines": [
            {"id": "ja-1", "start": 2, "end": 4, "text": "Hikari", "tokens": [
                {"text": "Hikari", "start": 2, "end": 4, "reading": "hikari"}]}]}
        self.save_sources()
        self.write_json("website/data/songs/public-song/lyrics/en-vocal/en.json", self.en_lyrics)
        self.write_json("website/data/songs/public-song/lyrics/ja-vocal/ja.json", self.ja_lyrics)
        self.write_json("website/data/songs/public-song/lyrics/en-vocal/ja.json",
                        {"language": {"code": "ja"}, "lines": [{"id": "wrong", "start": 9, "end": 10, "text": "TRANSLATION"}]})
        for relative, _ in set(learning.STATIC_FILES.values()):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"public: " + relative.encode())
        self.client = TestClient(learning.create_app(self.root, "http://127.0.0.1:18440"))
        self.addCleanup(self.client.close)

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def save_sources(self):
        self.write_json("website/data/catalog.json", self.catalog)
        self.write_json("website/data/songs/public-song/manifest.json", self.manifest)
        self.write_json("website/data/songs/public-song/study.json", self.study)

    def song(self):
        response = self.client.get("/api/v1/songs/public-song")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_health_library_and_exact_contract(self):
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})
        library = self.client.get("/api/v1/library").json()
        self.assertEqual(set(library), {"version", "items"})
        self.assertEqual(library["version"], 1)
        self.assertEqual([i["id"] for i in library["items"]], ["first-pulse", "public-song"])
        for item in library["items"]:
            self.assertEqual(set(item), {"id", "title", "artist", "coverUrl", "duration", "kind"})
        song = self.song()
        self.assertEqual(set(song), {"version", "id", "title", "artist", "coverUrl", "assets", "defaultAssetId"})
        self.assertEqual(song["defaultAssetId"], "vocal-en")
        self.assertEqual(song["coverUrl"], "https://fun.lazying.art/assets/covers/public-song.png")
        for asset in song["assets"]:
            self.assertEqual(set(asset), {"id", "label", "language", "audioUrl", "duration", "bpm", "timeSignature",
                                          "confidence", "beats", "chords", "lyrics", "lyricTracks", "phrases", "melody"})
            self.assertEqual(asset["confidence"], {"beats": "analysis", "chords": "analysis", "melody": "analysis"})
            self.assertTrue(all(set(beat) == {"time"} for beat in asset["beats"]))
            self.assertEqual(set(asset["melody"][0]), {"start", "end", "note", "numberNote", "text"})
            self.assertEqual(set(asset["lyrics"][0]), {"id", "start", "end", "text", "tokens"})
        serialized = json.dumps(song)
        for forbidden in ("SECRET", "/home/", "data/runs", "provenance", "Source", "lyricEvidence", "downbeat"):
            self.assertNotIn(forbidden, serialized)

    def test_per_vocal_lyrics_timing_readings_and_phrases(self):
        en, ja = self.song()["assets"]
        self.assertEqual((en["duration"], ja["duration"]), (12, 14))
        self.assertEqual([r["text"] for r in en["lyrics"]], ["Sun"])
        self.assertEqual([r["text"] for r in ja["lyrics"]], ["Hikari"])
        self.assertEqual(en["lyrics"][0]["tokens"][0]["reading"], "sun1")
        self.assertEqual(ja["lyrics"][0]["tokens"][0]["reading"], "hikari")
        self.assertEqual(en["phrases"], [{"id": "en-1", "start": 1, "end": 3, "text": "Sun"}])
        self.assertEqual(ja["beats"][0], {"time": 2})
        self.assertEqual(ja["chords"][0]["name"], "Am")

    def test_translations_belong_to_selected_vocal(self):
        en, ja = self.song()["assets"]
        tracks = {t["language"]: t["lines"] for t in en["lyricTracks"]}
        self.assertEqual(tracks["en"], en["lyrics"])
        self.assertEqual(tracks["ja"][0]["text"], "TRANSLATION")
        self.assertEqual(tracks["ja"][0]["start"], 9)
        self.assertEqual(ja["lyricTracks"], [{"language": "ja", "lines": ja["lyrics"]}])

    def test_translation_tracks_fail_closed(self):
        descriptor = self.manifest["lyricSets"][0]["tracks"][1]
        for change in ({"hidden": True}, {"path": "../../private.json"}, {"code": "zh-Hans"}):
            saved = copy.deepcopy(descriptor)
            descriptor.update(change)
            self.save_sources()
            self.assertEqual([t["language"] for t in self.song()["assets"][0]["lyricTracks"]], ["en"])
            descriptor.clear()
            descriptor.update(saved)
        self.manifest["lyricSets"][0]["tracks"].append(copy.deepcopy(descriptor))
        self.save_sources()
        self.assertEqual([t["language"] for t in self.song()["assets"][0]["lyricTracks"]], ["en"])

    def test_chinese_pronunciation_formats_without_inference(self):
        self.assertEqual(learning.pinyin_tones("chuang1 bian1 nu:3 lve4 shui3 liu2 ou3 ma5"),
                         "chuāng biān nǚ lüè shuǐ liú ǒu ma")
        self.assertEqual(learning.pinyin_tones("窓 まど shēn"), "窓 まど shēn")
        self.manifest["lyricSets"][0]["tracks"].append({"code": "zh-Hans", "path": "lyrics/en-vocal/zh.json"})
        self.write_json("website/data/songs/public-song/lyrics/en-vocal/zh.json", {
            "language": {"code": "zh-Hans"}, "lines": [{"id": "en-1", "start": 1, "end": 3,
            "text": "身", "tokens": [{"text": "身", "start": 1, "end": 2, "pinyin": "shen1"}]}]})
        self.save_sources()
        track = self.song()["assets"][0]["lyricTracks"][-1]
        self.assertEqual(track["lines"][0]["tokens"][0]["reading"], "shēn")

    def test_hidden_and_preview_checks_apply_to_detail_and_library(self):
        original_item, original_manifest = copy.deepcopy(self.item), copy.deepcopy(self.manifest)
        denied = [{"hidden": True}, {"hidden": "false"}, {"visibility": "private"}, {"visibility": "unlisted"},
                  {"releaseStage": "preview"}, {"category": "preview"}, {"listed": False}, {"status": "draft"},
                  {"title": "Song Preview"}, {"tags": ["experimental"]}, {"publication": {"listed": False}},
                  {"publication": {"visibility": "private"}}, {"publication": {"stage": "preview"}},
                  {"publication": []}]
        for location in ("catalog", "manifest"):
            for change in denied:
                with self.subTest(location=location, change=change):
                    self.item = copy.deepcopy(original_item)
                    self.manifest = copy.deepcopy(original_manifest)
                    (self.item if location == "catalog" else self.manifest).update(change)
                    self.catalog["items"] = [self.item]
                    self.save_sources()
                    self.assertEqual(self.client.get("/api/v1/songs/public-song").status_code, 404)
                    self.assertEqual([i["id"] for i in self.client.get("/api/v1/library?showall=1").json()["items"]], ["first-pulse"])

    def test_legacy_preview_id_and_non_catalog_song_not_discoverable(self):
        self.item["id"] = "unflagged-preview"
        self.save_sources()
        self.assertEqual(len(self.client.get("/api/v1/library").json()["items"]), 1)
        self.assertEqual(self.client.get("/api/v1/songs/unflagged-preview").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/songs/public-song").status_code, 404)

    def test_asset_filter_and_default_fallback(self):
        self.manifest["assets"]["primaryAudio"]["hidden"] = True
        self.save_sources()
        song = self.song()
        self.assertEqual(song["defaultAssetId"], "vocal-ja")
        self.assertEqual([a["id"] for a in song["assets"]], ["vocal-ja"])
        self.assertEqual(self.client.get("/api/v1/library").json()["items"][1]["duration"], 14)

    def test_missing_or_mismatched_lyric_set_never_uses_other_vocal(self):
        self.manifest["lyricSets"][1]["tracks"].append(
            {"code": "en", "path": "lyrics/en-vocal/en.json", "features": ["translation"]})
        for value in ("absent", "ja-vocal"):
            with self.subTest(value=value):
                self.manifest["assets"]["primaryAudio"]["lyricSetId"] = value
                self.save_sources()
                self.assertEqual(self.song()["assets"][0]["lyrics"], [])
        self.manifest["assets"]["primaryAudio"]["lyricSetId"] = "en-vocal"
        self.manifest["lyricSets"][0]["tracks"] = [{"code": "ja", "path": "lyrics/en-vocal/ja.json"}]
        self.save_sources()
        self.assertEqual(self.song()["assets"][0]["lyrics"], [])

    def test_shared_legacy_text_tracks(self):
        tracks = self.manifest.pop("lyricSets")[0]["tracks"]
        self.manifest["textTracks"] = tracks
        del self.manifest["assets"]["primaryAudio"]["lyricSetId"]
        self.save_sources()
        self.assertEqual(self.song()["assets"][0]["lyrics"][0]["text"], "Sun")

    def test_stale_analysis_not_reused(self):
        self.study["assets"]["vocal-en"]["src"] = "https://lazyingart.github.io/MusiaSongs/audio/old.mp3"
        self.save_sources()
        en = self.song()["assets"][0]
        self.assertEqual(en["confidence"], {"beats": "unavailable", "chords": "unavailable", "melody": "unavailable"})
        self.assertIsNone(en["bpm"])
        self.assertIsNone(en["timeSignature"])
        self.assertEqual(en["beats"], [])
        self.assertEqual(en["melody"], [])

    def test_missing_study_and_per_asset_musical_fallback(self):
        (self.root / "website/data/songs/public-song/study.json").unlink()
        self.manifest["assets"]["primaryAudio"]["musical"] = {"bpm": 60, "beats": [{"time": 1, "index": 0}],
                                                                 "chords": [{"start": 1, "end": 2, "name": "Em"}]}
        self.manifest["musical"] = {"beats": [{"time": 5}], "bpm": 200}
        self.write_json("website/data/songs/public-song/manifest.json", self.manifest)
        en, ja = self.song()["assets"]
        self.assertEqual(en["beats"], [{"time": 1}])
        self.assertEqual(ja["beats"], [])
        self.assertIsNone(ja["bpm"])

    def test_input_changes_visible_without_restart(self):
        self.assertEqual(self.song()["assets"][0]["lyrics"][0]["text"], "Sun")
        self.en_lyrics["lines"][0]["text"] = "Moon"
        self.write_json("website/data/songs/public-song/lyrics/en-vocal/en.json", self.en_lyrics)
        self.assertEqual(self.song()["assets"][0]["lyrics"][0]["text"], "Moon")
        self.item["hidden"] = True
        self.save_sources()
        self.assertEqual(self.client.get("/api/v1/songs/public-song").status_code, 404)

    def test_audio_urls_reject_userinfo_private_hosts_queries_and_traversal(self):
        unsafe = ["file:///home/private.wav", "/home/private.wav", "http://127.0.0.1/audio.wav",
                  "https://lazyingart.github.io.evil.test/MusiaSongs/audio/x.mp3",
                  "https://user:pass@lazyingart.github.io/MusiaSongs/audio/x.mp3",
                  "https://lazyingart.github.io/MusiaSongs/audio/../secret.mp3",
                  "https://lazyingart.github.io/MusiaSongs/audio/%2e%2e/secret.mp3",
                  "https://lazyingart.github.io/MusiaSongs/audio/x.mp3?token=SECRET",
                  "https://lazyingart.github.io/MusiaSongs/audio/x.mp3#SECRET",
                  "https://lazyingart.github.io:443/MusiaSongs/audio/x.mp3",
                  "https://lazyingart.github.io/MusiaSongs/audio/x.mp3\n"]
        for src in unsafe:
            with self.subTest(src=src):
                self.manifest["assets"]["primaryAudio"]["src"] = src
                self.save_sources()
                self.assertEqual([a["id"] for a in self.song()["assets"]], ["vocal-ja"])

    def test_private_cover_drops_song(self):
        self.item["cover"] = "https://user:SECRET@fun.lazying.art/assets/covers/a.png"
        self.save_sources()
        self.assertEqual(self.client.get("/api/v1/songs/public-song").status_code, 404)

    def test_static_allowlist_and_no_directory_fallback(self):
        for route, (relative, _) in learning.STATIC_FILES.items():
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"public: " + relative.encode())
        self.assertEqual(self.client.get("/assets/musia.js").content, b"public: website/musia.js")
        for route in ("/vendor/", "/vendor/private.js", "/website/musia.js", "/musia/learning.py", "/.env",
                      "/website/data/catalog.json", "/data/catalog.json", "/apps/web/index.html", "/unknown",
                      "/openapi.json", "/docs", "/privacy/"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route, follow_redirects=False).status_code, 404)

    def test_symlinked_static_and_catalog_files_are_not_served(self):
        secret = self.root / "secret.txt"
        secret.write_text("SECRET", encoding="utf-8")
        for relative, endpoint in (("apps/web/app.js", "/app.js"), ("website/data/songs/public-song/manifest.json", "/api/v1/songs/public-song")):
            path = self.root / relative
            path.unlink()
            path.symlink_to(secret)
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("SECRET", response.text)

    def test_symlinked_parent_and_lyric_paths_are_rejected(self):
        vendor = self.root / "apps/web/vendor"
        vendor.rename(self.root / "saved-vendor")
        vendor.symlink_to(self.root / "saved-vendor", target_is_directory=True)
        self.assertEqual(self.client.get("/vendor/lucide.js").status_code, 404)
        for path in ("../../../../secret.json", "/etc/passwd", "lyrics/../../secret.json", "lyrics/%2e%2e/secret.json", "lyrics/secret.json"):
            with self.subTest(path=path):
                self.manifest["lyricSets"][0]["tracks"][0]["path"] = path
                self.save_sources()
                self.assertEqual(self.song()["assets"][0]["lyrics"], [])

    def test_manifest_path_is_not_an_arbitrary_file_endpoint(self):
        self.item["manifest"] = "../secret.json"
        self.save_sources()
        self.assertEqual(self.client.get("/api/v1/songs/public-song").status_code, 404)
        for route in ("/api/v1/files?path=/etc/passwd", "/api/v1/models", "/api/v1/execute", "/api/v1/upload"):
            self.assertEqual(self.client.get(route).status_code, 404)

    def test_invalid_ids_and_encoded_traversal(self):
        for path in ("/api/v1/songs/%2e%2e", "/api/v1/songs/a%2fb", "/%2e%2e/musia/learning.py",
                     "/assets/%252e%252e/secret", "/assets/%5csecret", "/api/v1/songs/%00", "/api/v1/songs/" + "x" * 129):
            with self.subTest(path=path):
                response = self.client.get(path, follow_redirects=False)
                self.assertIn(response.status_code, (400, 404))
                self.assertNotIn("location", response.headers)

    def test_mutation_and_request_bodies_rejected(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"):
            for path in ("/api/v1/library", "/api/v1/songs/public-song", "/api/v1/upload", "/", "/api/v1/exercises/first-pulse/audio.wav"):
                with self.subTest(method=method, path=path):
                    response = self.client.request(method, path, content=b"untrusted")
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.headers["allow"], "GET, HEAD")
        self.assertEqual(self.client.request("GET", "/healthz", content=b"body").status_code, 400)
        after = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_security_headers_bounded_cache_and_head(self):
        for path in ("/healthz", "/api/v1/library", "/api/v1/songs/public-song", "/app.js", "/missing"):
            response = self.client.get(path)
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertEqual(response.headers["x-frame-options"], "DENY")
            self.assertEqual(response.headers["referrer-policy"], "no-referrer")
            self.assertIn("microphone=()", response.headers["permissions-policy"])
            self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])
            self.assertNotIn("set-cookie", response.headers)
            self.assertNotIn("access-control-allow-origin", response.headers)
            head = self.client.head(path)
            self.assertEqual(head.content, b"")
            self.assertEqual(head.status_code, response.status_code)
            self.assertEqual(head.headers["content-length"], response.headers["content-length"])
        self.assertEqual(self.client.get("/healthz").headers["cache-control"], "no-store")
        self.assertIn("max-age=30", self.client.get("/api/v1/library").headers["cache-control"])
        self.assertEqual(self.client.get("/missing").headers["cache-control"], "no-store")

    def test_host_and_forwarded_headers_never_construct_urls(self):
        response = self.client.get("/api/v1/songs/first-pulse", headers={
            "Host": "user:SECRET@evil.example", "Forwarded": "host=evil.example;proto=https",
            "X-Forwarded-Host": "evil.example", "X-Forwarded-Proto": "https"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["assets"][0]["audioUrl"], "http://127.0.0.1:18440/api/v1/exercises/first-pulse/audio.wav")
        self.assertNotIn("SECRET", response.text)
        self.assertNotIn("evil", response.text)

    def test_public_base_configuration(self):
        with patch.dict(os.environ, {"MUSIA_PUBLIC_BASE_URL": "https://learning.example/"}):
            with TestClient(learning.create_app(self.root)) as client:
                self.assertEqual(client.get("/api/v1/songs/first-pulse").json()["coverUrl"], "https://learning.example/assets/brand.png")
        with patch.dict(os.environ, {}, clear=True):
            with TestClient(learning.create_app(self.root)) as client:
                self.assertEqual(client.get("/api/v1/songs/first-pulse").json()["coverUrl"], "https://musia.lazying.art/assets/brand.png")
        for value in ("https://user:SECRET@example.com", "https://example.com/?token=SECRET", "https://example.com/#secret",
                      "file:///tmp", "http://example.com", "https://example.com/path", "https://example.com:99999", "https://example.com\n"):
            with self.subTest(value=value), self.assertRaises(ValueError) as caught:
                learning.create_app(self.root, value)
            self.assertNotIn("SECRET", str(caught.exception))

    def test_malformed_and_oversized_json_fail_closed(self):
        path = self.root / "website/data/catalog.json"
        for content in (b'{"items": NaN}', b'{broken', b'[]', b'{"items":null}', b'\xff', b'[' * 2000):
            path.write_bytes(content)
            self.assertEqual(len(self.client.get("/api/v1/library").json()["items"]), 1)
        self.save_sources()
        with patch.object(learning, "MAX_JSON_BYTES", 64):
            self.assertEqual(learning._json(self.root, "website/data/catalog.json"), {})
            response = self.client.get("/api/v1/songs/first-pulse")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["cache-control"], "no-store")

    def test_nonfinite_out_of_bounds_events_and_unknown_confidence(self):
        en = self.study["assets"]["vocal-en"]
        en.update({"bpm": -1, "timeSignature": "guess", "beatConfidence": "estimated", "tags": None})
        en["beats"] += [{"time": True}, {"time": -1}, {"time": "3"}, {"time": 15}, {"time": 2}]
        en["chords"] += [{"start": 2, "end": 1, "name": "Am"}, {"start": 3, "end": 4, "name": "/home/private/key"}]
        self.save_sources()
        en = self.song()["assets"][0]
        self.assertEqual(en["beats"], [{"time": 1}, {"time": 2}])
        self.assertEqual(len(en["chords"]), 1)
        self.assertEqual(en["confidence"]["beats"], "estimated")
        self.assertIsNone(en["bpm"])
        self.assertIsNone(en["timeSignature"])
        self.study["assets"]["vocal-en"]["bpm"] = float("inf")
        self.save_sources()
        self.assertEqual(self.song()["assets"][0]["beats"], [])

    def test_generic_error_does_not_leak_private_exception(self):
        with patch.object(learning.PublicLibrary, "entries", side_effect=RuntimeError("/home/private SECRET")):
            response = self.client.get("/api/v1/library")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Public data unavailable"})
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_lessons_and_truthful_capabilities(self):
        lessons = self.client.get("/api/v1/lessons").json()["lessons"]
        self.assertEqual(len(lessons), 3)
        self.assertEqual(len({lesson["id"] for lesson in lessons}), 3)
        for lesson in lessons:
            self.assertEqual(set(lesson), {"id", "title", "focus", "body", "exerciseId", "steps"})
            self.assertEqual(lesson["exerciseId"], "first-pulse")
            self.assertTrue(all(isinstance(step, str) and step for step in lesson["steps"]))
        capabilities = self.client.get("/api/v1/capabilities").json()
        self.assertTrue(capabilities["readOnly"])
        for key in ("cloudGeneration", "upload", "aiCoaching", "accounts"):
            self.assertFalse(capabilities[key]["available"])
            self.assertTrue(capabilities[key]["reason"])

    def test_first_pulse_contract_and_no_instrumental_lyrics(self):
        song = self.client.get("/api/v1/songs/first-pulse").json()
        self.assertEqual(song["defaultAssetId"], "first-pulse")
        asset = song["assets"][0]
        self.assertEqual(asset["duration"], 22)
        self.assertEqual(asset["bpm"], 60)
        self.assertEqual(asset["timeSignature"], "4/4")
        self.assertEqual(asset["beats"], [{"time": i, "index": i} for i in range(20)])
        self.assertEqual([(c["start"], c["end"], c["name"]) for c in asset["chords"]],
                         [(4, 8, "Em"), (8, 12, "Am"), (12, 16, "Em"), (16, 20, "Am")])
        self.assertEqual([p["id"] for p in asset["phrases"]], ["bar-1", "bar-2", "bar-3", "bar-4"])
        self.assertEqual(asset["lyrics"], [])
        self.assertEqual(asset["melody"], [])
        self.assertEqual(asset["confidence"], {"beats": "verified", "chords": "verified", "melody": "unavailable"})

    def test_wav_exact_samples_onsets_harmony_and_decay(self):
        response = self.client.get("/api/v1/exercises/first-pulse/audio.wav")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "audio/wav")
        with wave.open(io.BytesIO(response.content), "rb") as wav:
            self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()), (1, 2, 24000))
            self.assertEqual(wav.getnframes(), 22 * 24000)
            raw = wav.readframes(wav.getnframes())
        samples = struct.unpack("<" + "h" * (len(raw) // 2), raw)
        asset = self.client.get("/api/v1/songs/first-pulse").json()["assets"][0]
        for beat in asset["beats"]:
            index = round(beat["time"] * 24000)
            self.assertGreater(abs(samples[index]), 10000)
            if beat["time"] < 4:
                self.assertEqual(samples[index + 2000:index + 23000], (0,) * 21000)
        for start, end, name in learning.EXERCISE_BARS:
            window = samples[int((start + 0.5) * 24000):int((start + 1) * 24000)]
            notes = (52, 55, 59) if name == "Em" else (45, 48, 52)
            for note in notes:
                frequency = 440 * 2 ** ((note - 69) / 12)
                real = sum(v * math.cos(2 * math.pi * frequency * i / 24000) for i, v in enumerate(window))
                imag = sum(v * math.sin(2 * math.pi * frequency * i / 24000) for i, v in enumerate(window))
                amplitude = 2 * math.hypot(real, imag) / len(window)
                self.assertGreater(amplitude, 1500)
        self.assertGreater(max(abs(n) for n in samples[20 * 24000:21 * 24000]), 100)
        self.assertEqual(samples[-1], 0)
        self.assertLess(max(abs(n) for n in samples), 32767)
        self.assertEqual(response.content, self.client.get("/api/v1/exercises/first-pulse/audio.wav").content)
        learning._synthesize_first_pulse.cache_clear()
        self.assertEqual(response.content, learning.first_pulse_wav())

    def test_audio_range_and_head_for_native_players(self):
        path = "/api/v1/exercises/first-pulse/audio.wav"
        full = self.client.get(path)
        for value, expected in (("bytes=0-43", full.content[:44]), ("bytes=-10", full.content[-10:]),
                                ("bytes=44-", full.content[44:])):
            response = self.client.get(path, headers={"Range": value})
            self.assertEqual(response.status_code, 206)
            self.assertEqual(response.content, expected)
            self.assertIn(f"/{len(full.content)}", response.headers["content-range"])
        for value in ("bytes=999999999-", "bytes=3-2", "bytes=-0", "bytes=-", "bytes=0-1,4-5", "items=0-2"):
            self.assertEqual(self.client.get(path, headers={"Range": value}).status_code, 416)
        head = self.client.head(path)
        self.assertEqual(head.content, b"")
        self.assertEqual(int(head.headers["content-length"]), len(full.content))


class RepositorySmokeTest(unittest.TestCase):
    def test_real_catalog_is_public_and_per_vocal(self):
        with TestClient(learning.create_app(public_base_url="https://musia.lazying.art")) as client:
            library = client.get("/api/v1/library")
            self.assertEqual(library.status_code, 200)
            self.assertGreater(len(library.json()["items"]), 1)
            for item in library.json()["items"]:
                self.assertFalse(learning.NONPUBLIC.search(item["id"]))
                response = client.get("/api/v1/songs/" + item["id"])
                self.assertEqual(response.status_code, 200)
                for forbidden in ("/home/", "data/runs/", "beatSource", "melodySource", "provenance", "lyricEvidence"):
                    self.assertNotIn(forbidden, response.text)
                for asset in response.json()["assets"]:
                    if item["kind"] != "exercise":
                        self.assertTrue(all(set(beat) == {"time"} for beat in asset["beats"]))
                        self.assertIn(asset["confidence"]["melody"], ("analysis", "unavailable"))
            for song_id in ("luoshenfu-original-excerpt-preview", "luoshui-zhaoying-preview", "take-care-of-yourself"):
                self.assertEqual(client.get("/api/v1/songs/" + song_id).status_code, 404)


if __name__ == "__main__":
    unittest.main()
