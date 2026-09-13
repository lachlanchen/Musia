#!/usr/bin/env python3
"""Publish the selected, reviewed MiniMax Aya song as a Fun media item.

Uses the audited source package, never the initial incomplete VAD transcript.
Does not generate audio, change other catalog items, or push repositories.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "data/creative_projects/aya-chan-ban-qu-chang-an-minimax-20260913"
ANALYSIS = ROOT / "data/runs/ban-qu-chang-an-minimax-91302"
LYRICS = PROJECT / "review/minimax-91302/lyrics-publication"
MEDIA_ID = "ban-qu-chang-an"
SONGS = ROOT.parent / "MusiaSongs"
AUDIO = "ban-qu-chang-an-zh-minimax-music3-seed91302-20260914.mp3"
COVER = f"assets/covers/{MEDIA_ID}-16x9.png"
URL = f"https://fun.lazying.art/#{MEDIA_ID}"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    selected = read_json(PROJECT / "selected/manifest.json")
    if digest(PROJECT / "selected/ban-qu-chang-an-minimax.wav") != selected["audio"]["wavSha256"]:
        raise ValueError("Selected audio no longer matches the reviewed vocal")
    duration = selected["audio"]["durationSeconds"]
    tracks = {code: read_json(LYRICS / f"{code}.json") for code in ("zh-Hans", "en", "ja")}
    reference = tracks["zh-Hans"]["lines"]
    if len(reference) != 28:
        raise ValueError("This reviewed vocal must account for all 28 sung lines")
    for code, track in tracks.items():
        if track["provenance"]["audioSha256"] != selected["audio"]["wavSha256"]:
            raise ValueError(f"Wrong audio provenance for {code}")
        if [line["id"] for line in track["lines"]] != [line["id"] for line in reference]:
            raise ValueError(f"Translation line mismatch: {code}")
        track["provenance"].update(releaseStage="published", publicationAuthorization="User requested website upload on 2026-09-14")
        write_json(ROOT / f"website/data/songs/{MEDIA_ID}/lyrics/zh-minimax-91302/{code}.json", track)

    audio_source = PROJECT / "selected/ban-qu-chang-an-minimax.mp3"
    audio_target = SONGS / "audio" / AUDIO
    if audio_target.exists() and digest(audio_target) != digest(audio_source):
        raise FileExistsError("Public audio name already belongs to different bytes")
    if not audio_target.exists():
        shutil.copy2(audio_source, audio_target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=SONGS, check=True)
    shutil.copy2(PROJECT / "selected/cover-16x9.png", ROOT / "website" / COVER)

    chord_data = read_json(ANALYSIS / "analysis/chords.json")["chords"]
    beat_data = read_json(ANALYSIS / "analysis/beats.json")
    musical = {
        "key": "Unverified", "bpm": round(beat_data["tempo_bpm"], 3),
        "timeSignature": "4/4", "meterStatus": "estimate", "quality": "analysis",
        "chords": [{"start": round(c["start"], 3), "end": round(min(c["end"], duration), 3),
                    "name": c["chord"], "confidence": round(c["confidence"], 3)}
                   for c in chord_data if c["start"] < duration],
        "beats": [{"index": b["index"], "time": round(b["time"], 3)}
                  for b in beat_data["beats"] if b["time"] < duration],
        "chordSource": "Analysis-grade chord estimates from this exact selected render; not a verified score",
        "beatSource": "Audio beat tracking from this exact render; meter not independently verified",
    }
    asset = {
        "id": f"{MEDIA_ID}-zh-minimax-91302", "label": "中文", "selectorLabel": "中文",
        "publicRoleLabel": "中文", "role": "vocal", "languageCode": "zh-Hans",
        "languageLabel": "中文", "lyricSetId": "zh-minimax-91302",
        "src": "https://lazyingart.github.io/MusiaSongs/audio/" + AUDIO,
        "mime": "audio/mpeg", "musical": musical,
    }
    track_infos = []
    for code, track in tracks.items():
        features = {"zh-Hans": ["active-vocal", "pinyin", "word-highlight"],
                    "en": ["translation", "rough-highlight"],
                    "ja": ["translation", "furigana", "rough-highlight"]}[code]
        track_infos.append({**track["language"], "features": features,
                            "path": f"lyrics/zh-minimax-91302/{code}.json"})
    description = "Half a melody waits in Chang'an; the other half travels across the Yellow River and red mountains, carrying a promise to return."
    manifest = {
        "schema": "fun.lazying.media.manifest.v1", "version": 1, "id": MEDIA_ID,
        "kind": "song", "title": "半曲长安", "artist": "Musia",
        "localizedTitles": {"zh-Hans": "半曲长安", "en": "The Melody I Left in Chang'an", "ja": "長安に残した調べ"},
        "description": description, "caption": "半首琴声留在长安，一半随她越过千山。",
        "generationCredit": "AI-generated music · MiniMax-Music3",
        "duration": duration, "canonicalUrl": URL,
        "publication": {"visibility": "public", "stage": "published", "listed": True},
        "share": {"title": "半曲长安 | Musia", "description": description,
                  "url": URL, "image": COVER, "siteName": "Fun Lazying Art"},
        "assets": {
            "cover": {"id": "cover", "label": "半曲长安 cover", "role": "cover", "src": COVER,
                      "mime": "image/png", "width": 1672, "height": 941},
            "poster": {"id": "poster", "label": "半曲长安 poster", "role": "poster", "src": COVER,
                       "mime": "image/png", "width": 1672, "height": 941},
            "primaryAudio": asset, "alternateAudio": [],
        },
        "musical": musical, "textTracks": [],
        "lyricSets": [{"id": "zh-minimax-91302", "label": "中文", "languageCode": "zh-Hans", "tracks": track_infos}],
        "timeline": {"unit": "seconds", "lines": [{key: line[key] for key in ("id", "start", "end", "text")} for line in reference]},
        "provenance": {
            "createdBy": "Musia", "model": selected["model"], "modelRevision": selected["modelRevision"],
            "selectedSeed": 91302, "aiGenerated": True,
            "generationProject": str(PROJECT.relative_to(ROOT)), "analysisRun": str(ANALYSIS.relative_to(ROOT)),
            "audioSha256": selected["audio"]["wavSha256"], "publicMp3Sha256": digest(audio_target),
            "coverSource": str((PROJECT / "assets/ban-qu-chang-an-cover-16x9.png").relative_to(ROOT)),
            "lyricCorrection": "Source-informed large-v3 full-mix/no-VAD vocal passes and independent MOSS; all 28 lines accounted for",
            "quality": {"audioHealth": "pass", "humanListeningApproved": False,
                        "timing": "ASR-derived estimates; not frame-accurate recording approval",
                        "unresolved": selected["lyrics"]["unresolved"]},
        },
    }
    write_json(ROOT / f"website/data/songs/{MEDIA_ID}/manifest.json", manifest)
    path = ROOT / "website/data/catalog.json"
    catalog = read_json(path)
    item = {"id": MEDIA_ID, "kind": "song", "title": "半曲长安", "artist": "Musia",
            "summary": description, "manifest": f"data/songs/{MEDIA_ID}/manifest.json", "cover": COVER,
            "visibility": "public", "releaseStage": "published", "category": "music",
            "languages": ["zh-Hans", "en", "ja"],
            "tags": ["music", "Mandarin", "Aya Chan", "hanfu", "Chang'an", "Yellow River", "homecoming", "pinyin", "furigana", "chords"]}
    catalog["items"] = [item] + [entry for entry in catalog["items"] if entry["id"] != MEDIA_ID]
    write_json(path, catalog)
    print(URL)


if __name__ == "__main__":
    main()
