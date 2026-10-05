#!/usr/bin/env python3
"""Apply reviewed catalog names and editions without changing musical content."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {"en": "English", "zh": "中文", "zh-Hans": "中文", "zh-Hant": "中文",
             "ja": "日本語", "yue-Hant": "粵語", "yue-Hans": "粵語", "mul": "English · 中文 · 日本語"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audio_assets(manifest):
    assets = manifest.get("assets", {})
    return [a for a in [assets.get("primaryAudio"), *assets.get("alternateAudio", [])] if a]


def musical_identity(manifest):
    return {"id": manifest["id"], "duration": manifest.get("duration"),
            "timeline": manifest.get("timeline"), "musical": manifest.get("musical"),
            "lyricSets": manifest.get("lyricSets"), "textTracks": manifest.get("textTracks"),
            "assets": [{k: a.get(k) for k in ("id", "src", "lyricSetId", "musical", "duration", "languageCode")}
                       for a in audio_assets(manifest)]}


def apply_entry(item, manifest, group, status, number=0):
    before = copy.deepcopy(musical_identity(manifest))
    title_language = group.get("titleLanguage", "zh-Hans")
    if title_language not in {"zh-Hans", "ja"}:
        raise ValueError(f"Unsupported catalog title language: {title_language}")
    base = f"{group['titles'][title_language]} · {group['titles']['en']}"
    suffix = f" · Archive {number:02d}" if status == "archive" else " · MV" if status == "companion" else ""
    title = base + suffix
    for obj in (item, manifest):
        obj["title"] = title
        obj["displayTitle"] = title
        obj["workId"] = group["id"]
        obj["edition"] = {"status": status, **({"number": number} if number else {})}
        if status == "archive":
            obj["hidden"] = True
            obj["hiddenLabel"] = f"Archive {number:02d}"
            obj["hiddenReason"] = "Earlier recording; retained for listening history and direct links."
        elif status != "preview":
            if obj.get("hidden") or obj.get("visibility") in {"hidden", "unlisted"}:
                raise ValueError(f"Refusing implicit promotion of {item['id']}")
    manifest["localizedTitles"] = {key: value + suffix for key, value in group["titles"].items()}
    if manifest.get("generationCredit"):
        manifest["generationCredit"] = "AI-generated music"
    manifest.setdefault("share", {})["title"] = title + " - Musia"
    cover = manifest.get("assets", {}).get("cover")
    if cover:
        cover["label"] = title + " cover"
    if status == "archive":
        manifest.setdefault("publication", {}).update(visibility="hidden", stage="legacy", listed=False)
    # Preserve different vocal languages. Hide only competing takes in one language.
    seen = set()
    archives = 0
    for asset in audio_assets(manifest):
        code = asset.get("languageCode", "")
        label = LANGUAGES.get(code, asset.get("languageLabel", "Audio"))
        if status != "preview" and code in seen:
            archives += 1
            asset["hidden"] = True
            asset["hiddenLabel"] = f"Archive {archives:02d}"
            label += " · " + asset["hiddenLabel"]
        elif status == "preview":
            continue
        seen.add(code)
        for key in ("label", "selectorLabel", "languageLabel"):
            asset[key] = label
    if musical_identity(manifest) != before:
        raise ValueError(f"Musical content changed for {item['id']}")


def plan(root):
    config = load(root / "references/catalog-curation.json")
    catalog_path = root / "website/data/catalog.json"
    catalog = load(catalog_path)
    items = {i["id"]: i for i in catalog["items"]}
    if len(items) != len(catalog["items"]):
        raise ValueError("Duplicate catalog IDs")
    updates = {}
    seen = set()
    for group in config["groups"]:
        members = []
        if group["selected"]:
            members.append((group["selected"], "selected", 0))
        members += [(name, "archive", n) for n, name in enumerate(group["archives"], 1)]
        members += [(name, "preview", 0) for name in group["previews"]]
        members += [(name, "companion", 0) for name in group["companions"]]
        for media_id, status, number in members:
            if media_id in seen or media_id not in items:
                raise ValueError(f"Missing or duplicate curation member: {media_id}")
            seen.add(media_id)
            item = items[media_id]
            if item["manifest"] != f"data/songs/{media_id}/manifest.json":
                raise ValueError(f"Unexpected manifest path: {media_id}")
            path = root / "website" / item["manifest"]
            manifest = load(path)
            apply_entry(item, manifest, group, status, number)
            updates[path] = manifest
            study_path = path.with_name("study.json")
            if study_path.exists():
                study = load(study_path)
                study["title"] = manifest["title"] + " Atlas"
                for asset in audio_assets(manifest):
                    if asset["id"] in study.get("assets", {}):
                        study["assets"][asset["id"]]["label"] = asset["label"]
                updates[study_path] = study
    if set(items) != seen:
        raise ValueError(f"Curate new items before publishing: {sorted(set(items) - seen)}")
    if items[catalog["defaultMedia"]].get("hidden"):
        raise ValueError("Default item must be visible")
    updates[catalog_path] = catalog
    return updates


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--apply", action="store_true", help="Write metadata; otherwise check only")
    args = parser.parse_args(argv)
    updates = plan(args.root)
    changed = []
    for path, obj in updates.items():
        text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
        if load(path) != obj:
            changed.append(str(path.relative_to(args.root)))
            if args.apply:
                path.write_text(text, encoding="utf-8")
    print(json.dumps({"applied": args.apply, "changed": changed}, indent=2))
    return 0 if args.apply or not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
