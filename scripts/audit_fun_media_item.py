#!/usr/bin/env python3
"""Audit one Fun Lazying Art media item for publication-quality metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


TEXT_TRACK_SCHEMA = "fun.lazying.media.text-track.v1"
CJK_RE = re.compile(r"[\u3400-\u9fff]")
KANA_RE = re.compile(r"[\u3040-\u30ff]")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc


def is_external(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and parsed.netloc)


def rel_path(root: Path, value: str) -> Path:
    return (root / value).resolve()


def playable_assets(manifest: dict) -> list[dict]:
    assets = manifest.get("assets") or {}
    result: list[dict] = []
    primary = assets.get("primaryAudio") or {}
    if primary.get("src"):
        result.append({**primary, "_slot": "primaryAudio"})
    for item in assets.get("alternateAudio") or []:
        if item.get("src"):
            result.append({**item, "_slot": "alternateAudio"})
    primary_video = assets.get("primaryVideo") or {}
    if primary_video.get("src"):
        result.append({**primary_video, "_slot": "primaryVideo"})
    return result


def has_cjk(value: str) -> bool:
    return bool(CJK_RE.search(value or ""))


def has_kana(value: str) -> bool:
    return bool(KANA_RE.search(value or ""))


def line_ids(track: dict) -> list[str]:
    return [str(line.get("id", "")) for line in track.get("lines", [])]


def line_note_blob(track: dict) -> str:
    parts = [
        str(track.get("notes", "")),
        json.dumps(track.get("provenance", {}), ensure_ascii=False),
        json.dumps(track.get("quality", {}), ensure_ascii=False),
    ]
    return " ".join(parts).lower()


class Audit:
    def __init__(self, root: Path, media_id: str) -> None:
        self.root = root.resolve()
        self.media_id = media_id
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def check_path(self, value: str, label: str) -> None:
        if not value or is_external(value) or value.startswith("#"):
            return
        path = rel_path(self.root, value)
        if not path.exists():
            self.error(f"{label}: missing local path {path}")

    def load_catalog_item(self) -> tuple[dict, Path, dict]:
        catalog_path = self.root / "data" / "catalog.json"
        catalog = load_json(catalog_path)
        item = next((entry for entry in catalog.get("items", []) if entry.get("id") == self.media_id), None)
        if not item:
            raise SystemExit(f"{catalog_path}: media id not found: {self.media_id}")
        manifest_path = rel_path(self.root, item["manifest"])
        if not manifest_path.exists():
            raise SystemExit(f"{catalog_path}: missing manifest for {self.media_id}: {manifest_path}")
        return item, manifest_path, load_json(manifest_path)

    def check_cover(self, manifest: dict) -> None:
        assets = manifest.get("assets") or {}
        for key in ("cover", "poster"):
            asset = assets.get(key) or {}
            src = asset.get("src")
            if not src:
                self.warn(f"assets.{key}: missing {key} artwork")
                continue
            self.check_path(src, f"assets.{key}")
            width = asset.get("width")
            height = asset.get("height")
            if not width or not height:
                self.warn(f"assets.{key}: missing width/height metadata")
            elif height and abs((width / height) - (16 / 9)) > 0.03:
                self.warn(f"assets.{key}: expected 16:9 artwork, found {width}x{height}")
        share_image = (manifest.get("share") or {}).get("image")
        if not share_image:
            self.warn("share.image: missing social preview image")
        else:
            self.check_path(share_image, "share.image")

    def load_track(self, manifest_path: Path, info: dict) -> tuple[Path, dict] | None:
        path_value = info.get("path")
        if not path_value:
            self.error(f"{manifest_path}: lyric track entry missing path")
            return None
        track_path = (manifest_path.parent / path_value).resolve()
        if not track_path.exists():
            self.error(f"{manifest_path}: missing lyric track {track_path}")
            return None
        track = load_json(track_path)
        if track.get("schema") != TEXT_TRACK_SCHEMA:
            self.error(f"{track_path}: expected schema {TEXT_TRACK_SCHEMA}")
        if track.get("mediaId") != self.media_id:
            self.error(f"{track_path}: mediaId does not match {self.media_id}")
        expected_code = info.get("code")
        actual_code = (track.get("language") or {}).get("code")
        if expected_code and actual_code != expected_code:
            self.error(f"{track_path}: language code mismatch, manifest says {expected_code}, file says {actual_code}")
        return track_path, track

    def check_track_quality(self, track_path: Path, track: dict, active: bool) -> None:
        code = (track.get("language") or {}).get("code", "")
        lines = track.get("lines") or []
        if not lines:
            self.error(f"{track_path}: no lyric lines")
            return

        previous_start = -1.0
        timed_token_count = 0
        token_count = 0
        missing_pinyin = 0
        missing_reading = 0
        has_pronunciation = False
        for line in lines:
            line_id = line.get("id", "?")
            start = line.get("start")
            end = line.get("end")
            if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                self.error(f"{track_path}: {line_id} missing numeric start/end")
                continue
            if end <= start:
                self.error(f"{track_path}: {line_id} end must be greater than start")
            if start < previous_start:
                self.error(f"{track_path}: lines are not sorted at {line_id}")
            previous_start = start
            if not str(line.get("text", "")).strip():
                self.error(f"{track_path}: {line_id} has empty text")

            for token in line.get("tokens") or []:
                text = str(token.get("text", ""))
                token_count += 1
                if isinstance(token.get("start"), (int, float)) and isinstance(token.get("end"), (int, float)):
                    timed_token_count += 1
                if token.get("pinyin") or token.get("reading"):
                    has_pronunciation = True
                if code.startswith("zh") and has_cjk(text) and not token.get("pinyin"):
                    missing_pinyin += 1
                if code == "ja" and has_cjk(text) and not has_kana(text) and not token.get("reading"):
                    missing_reading += 1
                if code.startswith("yue") and has_cjk(text) and not (token.get("reading") or token.get("jyutping")):
                    missing_reading += 1

        if active and token_count == 0:
            self.warn(f"{track_path}: active vocal track has no tokens; word highlighting will be line-only")
        elif active and timed_token_count == 0:
            self.warn(f"{track_path}: active vocal tokens have no start/end; word highlighting will be evenly distributed")
        if code.startswith("zh") and missing_pinyin:
            self.warn(f"{track_path}: {missing_pinyin} Chinese CJK tokens missing pinyin")
        if code == "ja" and missing_reading:
            self.warn(f"{track_path}: {missing_reading} Japanese kanji tokens missing furigana reading")
        if code.startswith("yue") and missing_reading:
            self.warn(f"{track_path}: {missing_reading} Cantonese CJK tokens missing Jyutping/reading")
        if code in {"zh-Hans", "zh-Hant", "ja", "yue-Hant", "yue-Hans"} and not has_pronunciation:
            self.warn(f"{track_path}: no ruby pronunciation metadata found")
        notes = line_note_blob(track)
        if active and not any(word in notes for word in ("asr", "stt", "listening", "corrected", "whisper")):
            self.warn(f"{track_path}: active track has no ASR/STT/listening correction note")

    def check_lyric_sets(self, manifest_path: Path, manifest: dict) -> None:
        lyric_sets = manifest.get("lyricSets") or []
        set_ids = {item.get("id") for item in lyric_sets}
        assets = playable_assets(manifest)
        if len(assets) > 1 and not lyric_sets:
            self.warn("multiple playable assets but no lyricSets[]; only safe if all vocals truly share timing")
        for asset in assets:
            self.check_path(asset.get("src", ""), f"{asset.get('_slot')}.{asset.get('id', asset.get('label', 'asset'))}")
            lyric_set_id = asset.get("lyricSetId")
            if lyric_sets and not lyric_set_id:
                self.error(f"asset {asset.get('id') or asset.get('label')}: missing lyricSetId")
            elif lyric_set_id and lyric_set_id not in set_ids:
                self.error(f"asset {asset.get('id') or asset.get('label')}: lyricSetId {lyric_set_id} not found")

        for lyric_set in lyric_sets:
            set_id = lyric_set.get("id", "")
            language_code = lyric_set.get("languageCode", "")
            tracks = lyric_set.get("tracks") or lyric_set.get("textTracks") or []
            if len(tracks) < 2:
                self.warn(f"lyricSet {set_id}: fewer than two language tracks")
            if len(tracks) < 3 and language_code != "yue-Hant":
                self.warn(f"lyricSet {set_id}: fewer than three tracks; trilingual display may be incomplete")
            loaded: list[tuple[dict, Path, dict]] = []
            for info in tracks:
                loaded_track = self.load_track(manifest_path, info)
                if loaded_track:
                    track_path, track = loaded_track
                    loaded.append((info, track_path, track))

            active = [(info, path, track) for info, path, track in loaded if info.get("code") == language_code]
            if not active:
                self.error(f"lyricSet {set_id}: missing active timing track for languageCode {language_code}")

            reference_ids = line_ids(loaded[0][2]) if loaded else []
            for info, track_path, track in loaded:
                ids = line_ids(track)
                if ids != reference_ids:
                    self.error(f"{track_path}: line ids/order do not match lyricSet {set_id} reference track")
                self.check_track_quality(track_path, track, active=info.get("code") == language_code)

    def check_manifest_quality(self, manifest_path: Path, manifest: dict) -> None:
        if manifest.get("artist") != "Musia":
            self.warn("manifest.artist should usually be Musia for generated Musia website items")
        if not manifest.get("localizedTitles"):
            self.warn("localizedTitles missing; title will not change cleanly by vocal language")
        has_chords = bool((manifest.get("musical") or {}).get("chords"))
        if not has_chords:
            has_chords = any(bool((asset.get("musical") or {}).get("chords")) for asset in playable_assets(manifest))
        if not has_chords:
            self.warn("manifest.musical.chords missing; chord carousel will be empty")
        provenance = json.dumps(manifest.get("provenance", {}), ensure_ascii=False).lower()
        if "cover" not in provenance:
            self.warn("manifest.provenance does not record cover prompt/source")
        if not any(word in provenance for word in ("asr", "stt", "whisper", "listening", "correct")):
            self.warn("manifest.provenance does not mention ASR/STT/listening lyric correction")

    def run(self) -> int:
        _item, manifest_path, manifest = self.load_catalog_item()
        self.check_cover(manifest)
        self.check_manifest_quality(manifest_path, manifest)
        self.check_lyric_sets(manifest_path, manifest)
        return 1 if self.errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="website", help="Website root directory")
    parser.add_argument("--media-id", required=True, help="Catalog media id to audit")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    audit = Audit(Path(args.root), args.media_id)
    status = audit.run()
    for message in audit.errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in audit.warnings:
        print(f"WARN: {message}", file=sys.stderr)
    if args.strict and audit.warnings:
        status = 1
    if status == 0:
        suffix = "" if not audit.warnings else f" with {len(audit.warnings)} warning(s)"
        print(f"ok: {args.media_id} passed Fun media item audit{suffix}")
    else:
        print(f"failed: {args.media_id} has {len(audit.errors)} error(s) and {len(audit.warnings)} warning(s)", file=sys.stderr)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
