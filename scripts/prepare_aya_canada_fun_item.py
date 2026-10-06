#!/usr/bin/env python3
"""Reproduce the reviewed Canada song package; never generate, commit, or push."""

import json
import shutil
import subprocess
from pathlib import Path

from export_reviewed_japanese_lyrics import export
from export_reviewed_lyrics import sha256

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "data/creative_projects/aya-canada-beyond-the-maples-20261006"
MEDIA_ID = "aya-canada-beyond-the-maples"
TITLE = "楓の向こうで · Beyond the Maples"
WAV = PROJECT / "sweep-v2/batch-100603-100604/57015997-7e24-ae2a-b0cc-6e9c0e81c8c9.wav"
ANALYSIS = ROOT / "data/runs/aya-canada-ja-100604"
REVIEW = ROOT / "ideas-and-inspirations/aya-canada-beyond-the-maples/reviewed-lyrics.json"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    review = read(REVIEW)
    sources = {}
    for name, entry in review["sources"].items():
        path = ROOT / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise ValueError(f"ASR evidence changed: {name}")
        sources[name] = read(path)
    corrected = PROJECT / "selected/lyrics"
    export(review, sources, WAV, corrected)
    selected = PROJECT / "selected"
    master = selected / f"{MEDIA_ID}-ja.wav"
    if master.exists() and sha256(master) != review["audioSha256"]:
        raise FileExistsError("Refusing to replace a different selected WAV")
    if not master.exists():
        shutil.copy2(WAV, master)
    mp3 = selected / f"{MEDIA_ID}-ja.mp3"
    if not mp3.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-n", "-i", str(master), "-map_metadata", "-1",
                        "-c:a", "libmp3lame", "-b:a", "320k", "-metadata", "artist=Musia",
                        "-metadata", f"title={TITLE}", str(mp3)], check=True)
    filename = f"{MEDIA_ID}-ja-seed100604-20261006.mp3"
    songs = ROOT.parent / "MusiaSongs"
    target = songs / "audio" / filename
    if target.exists() and sha256(target) != sha256(mp3):
        raise FileExistsError("Versioned public MP3 already contains another audio")
    if not target.exists():
        shutil.copy2(mp3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=songs, check=True)
    song_dir = ROOT / "website/data/songs" / MEDIA_ID
    vocal = review["vocalSet"]
    tracks = {}
    for code in ("ja", "en", "zh-Hans"):
        tracks[code] = read(corrected / f"{code}.json")
        write(song_dir / f"lyrics/{vocal}/{code}.json", tracks[code])
    cover = f"assets/covers/{MEDIA_ID}-16x9.png"
    shutil.copy2(PROJECT / "cover-16x9.png", ROOT / "website" / cover)
    from PIL import Image
    with Image.open(PROJECT / "cover-16x9.png") as image:
        width, height = image.size
    duration = review["duration"]
    beats = read(ANALYSIS / "analysis/beats.json")
    chords = read(ANALYSIS / "analysis/chords.json")["chords"]
    musical = {
        "key": "Unverified", "bpm": round(beats["tempo_bpm"], 3), "timeSignature": "4/4",
        "meterStatus": "estimate", "quality": "analysis",
        "chords": [{"start": round(c["start"], 3), "end": round(min(c["end"], duration), 3),
                    "name": c["chord"], "confidence": round(c["confidence"], 3)} for c in chords if c["start"] < duration],
        "beats": [{"index": b["index"], "time": round(b["time"], 3)} for b in beats["beats"] if b["time"] < duration],
        "chordSource": "Selected seed 100604 audio analysis; not a verified score",
        "beatSource": "Selected seed 100604 beat tracker; 4/4 is a production target, not verified notation",
    }
    asset = {"id": "aya-canada-ja-100604", "label": "日本語", "selectorLabel": "日本語",
             "role": "vocal", "languageCode": "ja", "languageLabel": "日本語", "lyricSetId": vocal,
             "src": "https://lazyingart.github.io/MusiaSongs/audio/" + filename, "mime": "audio/mpeg", "musical": musical}
    features = {"ja": ["active-vocal", "furigana", "word-highlight"],
                "en": ["translation", "rough-highlight"], "zh-Hans": ["translation", "pinyin", "rough-highlight"]}
    infos = [{**tracks[code]["language"], "features": features[code], "path": f"lyrics/{vocal}/{code}.json"} for code in tracks]
    description = "Aya sends autumn photographs from Canada. At home, a second coffee cup waits, and missing her becomes a wish that she takes her time and sees the world."
    url = "https://fun.lazying.art/#" + MEDIA_ID
    source_lines = tracks["ja"]["lines"]
    provenance = {
        "createdBy": "Musia", "aiGenerated": True, "model": "acestep-v15-xl-turbo", "selectedSeed": 100604,
        "modelRevision": "ca1e85fe9430179831e6bc6be790c332190a3866",
        "checkpointRevision": "d4a0b288b83ebb7e25a8c0b32c573c22e134e8ee",
        "audioSha256": sha256(master), "publicMp3Sha256": sha256(target),
        "generationProject": str(PROJECT.relative_to(ROOT)), "analysisRun": str(ANALYSIS.relative_to(ROOT)),
        "lyricCorrection": str(REVIEW.relative_to(ROOT)),
        "quality": {"audioHealth": "pass", "humanListeningApproved": False,
                    "timing": "Reviewed large-v3 word anchors; token subdivision and translation highlights are approximate",
                    "musicalAnalysis": "Estimated, not musician-verified"},
        "coverSource": "New built-in image generation: Canada maples, lake, travelling woman, snow mountains and glass/timber canopy; no text",
    }
    manifest = {
        "schema": "fun.lazying.media.manifest.v1", "version": 1, "id": MEDIA_ID, "kind": "song",
        "title": TITLE, "artist": "Musia", "localizedTitles": {"ja": "楓の向こうで", "en": "Beyond the Maples", "zh-Hans": "枫叶彼端"},
        "description": description, "caption": "帰り道、急がないで。おみやげは君の話。",
        "generationCredit": "AI-generated music", "duration": duration, "canonicalUrl": url,
        "publication": {"visibility": "public", "stage": "published", "listed": True},
        "share": {"title": TITLE + " | Musia", "description": description, "url": url, "image": cover, "siteName": "Fun Lazying Art"},
        "assets": {"primaryAudio": asset, "alternateAudio": [],
                   **{role: {"id": role, "label": TITLE, "role": role, "src": cover, "mime": "image/png", "width": width, "height": height}
                      for role in ("cover", "poster")}},
        "musical": musical, "textTracks": [], "lyricSets": [{"id": vocal, "label": "日本語", "languageCode": "ja", "tracks": infos}],
        "timeline": {"unit": "seconds", "lines": [{k: line[k] for k in ("id", "start", "end", "text")} for line in source_lines]},
        "provenance": provenance,
    }
    write(song_dir / "manifest.json", manifest)
    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read(catalog_path)
    item = {"id": MEDIA_ID, "kind": "song", "title": TITLE, "artist": "Musia", "summary": description,
            "manifest": f"data/songs/{MEDIA_ID}/manifest.json", "cover": cover, "visibility": "public",
            "releaseStage": "published", "category": "music", "languages": list(tracks),
            "tags": ["music", "Japanese", "J-pop", "Aya Chan", "Canada", "autumn", "longing", "chords"]}
    catalog["items"] = [item] + [entry for entry in catalog["items"] if entry["id"] != MEDIA_ID]
    write(catalog_path, catalog)
    write(selected / "manifest.json", {**provenance, "audio": str(master.relative_to(ROOT)), "mp3": str(mp3.relative_to(ROOT)),
                                       "lyrics": str(corrected.relative_to(ROOT)), "duration": duration, "reviewedLineCount": len(source_lines)})
    print(url)


if __name__ == "__main__":
    main()
