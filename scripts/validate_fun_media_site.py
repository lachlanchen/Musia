#!/usr/bin/env python3
"""Validate the static Fun Lazying Art media website protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


CATALOG_SCHEMA = "fun.lazying.media.catalog.v1"
MANIFEST_SCHEMA = "fun.lazying.media.manifest.v1"
TEXT_TRACK_SCHEMA = "fun.lazying.media.text-track.v1"
MEDIA_KINDS = {"song", "localized-song", "mv", "short-film", "video", "youtube-video", "album", "playlist"}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc


def is_external(path: str) -> bool:
    parsed = urlparse(path)
    return bool(parsed.scheme and parsed.netloc)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def check_local_path(root: Path, value: str, label: str) -> None:
    if not value or is_external(value) or value.startswith("#"):
        return
    path = root / value
    require(path.exists(), f"{label}: missing local path {path}")


def iter_asset_paths(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in {"src", "href"} and isinstance(value, str):
                yield value
            else:
                yield from iter_asset_paths(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_asset_paths(item)


def validate_external_videos(manifest_path: Path, manifest: dict) -> None:
    assets = manifest.get("assets", {})
    external_items = []
    if isinstance(assets.get("youtube"), dict):
        external_items.append(assets["youtube"])
    external_items.extend(assets.get("externalVideos", []) or [])
    for item in external_items:
        provider = item.get("provider", "youtube")
        require(provider in {"youtube", "vimeo", "bilibili", "external"}, f"{manifest_path}: unsupported external video provider {provider}")
        has_locator = any(item.get(key) for key in ("videoId", "url", "embedUrl", "src"))
        require(has_locator, f"{manifest_path}: external video must include videoId, url, embedUrl, or src")


def validate_text_track(
    manifest_path: Path,
    manifest: dict,
    track_info: dict,
    timeline_ids: set[str] | None,
) -> set[str]:
    track_path = manifest_path.parent / track_info["path"]
    require(track_path.exists(), f"{manifest_path}: missing text track {track_path}")
    track = load_json(track_path)
    require(track.get("schema") == TEXT_TRACK_SCHEMA, f"{track_path}: expected schema {TEXT_TRACK_SCHEMA}")
    media_id = track.get("mediaId") or track.get("songId")
    require(media_id == manifest["id"], f"{track_path}: mediaId does not match manifest id")
    require(track.get("language", {}).get("code") == track_info["code"], f"{track_path}: language code mismatch")

    seen = set()
    for line in track.get("lines", []):
        line_id = line.get("id")
        if timeline_ids is not None:
            require(line_id in timeline_ids, f"{track_path}: unknown line id {line_id}")
        require(line.get("end", 0) >= line.get("start", 0), f"{track_path}: bad timing for {line_id}")
        require(isinstance(line.get("text"), str) and line["text"], f"{track_path}: missing text for {line_id}")
        seen.add(line_id)

    missing = (timeline_ids or set()) - seen
    line_coverage = track_info.get("lineCoverage") or track.get("lineCoverage") or "complete"
    allow_partial = line_coverage in {"partial", "partial-asr", "asr-partial"}
    require(allow_partial or not missing, f"{track_path}: missing line ids {sorted(missing)}")
    return seen


def validate_lyric_set(manifest_path: Path, manifest: dict, lyric_set: dict) -> None:
    require(lyric_set.get("id"), f"{manifest_path}: lyric set missing id")
    require(lyric_set.get("languageCode"), f"{manifest_path}: lyric set {lyric_set.get('id')} missing languageCode")
    tracks = lyric_set.get("tracks") or lyric_set.get("textTracks") or []
    require(tracks, f"{manifest_path}: lyric set {lyric_set['id']} missing tracks")

    reference_ids: set[str] | None = None
    for track_info in tracks:
        require(track_info.get("path"), f"{manifest_path}: lyric set {lyric_set['id']} track missing path")
        seen = validate_text_track(manifest_path, manifest, track_info, reference_ids)
        if reference_ids is None:
            reference_ids = seen


def validate_manifest(root: Path, item: dict) -> None:
    manifest_path = root / item["manifest"]
    require(manifest_path.exists(), f"catalog item {item['id']}: missing manifest {manifest_path}")
    manifest = load_json(manifest_path)
    require(manifest.get("schema") == MANIFEST_SCHEMA, f"{manifest_path}: expected schema {MANIFEST_SCHEMA}")
    require(manifest.get("id") == item["id"], f"{manifest_path}: id does not match catalog item")
    require(manifest.get("duration", 0) > 0, f"{manifest_path}: duration must be positive")

    for asset_path in iter_asset_paths(manifest.get("assets", {})):
        check_local_path(root, asset_path, str(manifest_path))
    for artifact_path in iter_asset_paths(manifest.get("artifacts", [])):
        check_local_path(root, artifact_path, str(manifest_path))
    validate_external_videos(manifest_path, manifest)

    lines = manifest.get("timeline", {}).get("lines", [])
    last_start = -1.0
    timeline_ids = set()
    for line in lines:
        require(line.get("id"), f"{manifest_path}: timeline line missing id")
        require(line["id"] not in timeline_ids, f"{manifest_path}: duplicate line id {line['id']}")
        require(line.get("end", 0) >= line.get("start", 0), f"{manifest_path}: bad timing for {line['id']}")
        require(line["start"] >= last_start, f"{manifest_path}: timeline not sorted at {line['id']}")
        last_start = line["start"]
        timeline_ids.add(line["id"])

    tracks = manifest.get("textTracks", [])
    require(lines or not tracks, f"{manifest_path}: textTracks require matching timeline lines")
    for track_info in tracks:
        require(track_info.get("path"), f"{manifest_path}: text track missing path")
        validate_text_track(manifest_path, manifest, track_info, timeline_ids)

    for lyric_set in manifest.get("lyricSets", []):
        validate_lyric_set(manifest_path, manifest, lyric_set)


def validate(root: Path) -> None:
    catalog_path = root / "data/catalog.json"
    require(catalog_path.exists(), f"missing catalog {catalog_path}")
    catalog = load_json(catalog_path)
    require(catalog.get("schema") == CATALOG_SCHEMA, f"{catalog_path}: expected schema {CATALOG_SCHEMA}")
    items = catalog.get("items", [])
    require(items, f"{catalog_path}: items is required")
    ids = {item["id"] for item in items}
    require(catalog.get("defaultMedia") in ids, f"{catalog_path}: defaultMedia not found in items")

    for item in items:
        require(item.get("kind"), f"{catalog_path}: item {item.get('id')} missing kind")
        require(item.get("kind") in MEDIA_KINDS, f"{catalog_path}: item {item.get('id')} has unsupported kind {item.get('kind')}")
        require(item.get("manifest"), f"{catalog_path}: item {item.get('id')} missing manifest")
        check_local_path(root, item.get("cover", ""), f"catalog item {item['id']}")
        validate_manifest(root, item)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="website", help="Website root directory")
    args = parser.parse_args()
    validate(Path(args.root).resolve())
    print(f"ok: {args.root} follows fun.lazying.media.v1")


if __name__ == "__main__":
    main()
