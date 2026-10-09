#!/usr/bin/env python3
"""Package a reviewed Japanese song from a release JSON; never push or generate."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from export_reviewed_japanese_lyrics import export
from export_reviewed_lyrics import sha256

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_unchanged(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and sha256(target) != sha256(source):
        raise FileExistsError(f"Refusing to replace a different asset: {target}")
    if not target.exists():
        shutil.copy2(source, target)


def prepare(config):
    media_id = config["mediaId"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", media_id):
        raise ValueError("Invalid media ID")
    project = ROOT / config["project"]
    wav = ROOT / config["audio"]
    review = read(ROOT / config["review"])
    if review["mediaId"] != media_id or review["title"] != config["title"]:
        raise ValueError("Release and reviewed lyrics describe different songs")
    sources = {}
    for name, entry in review["sources"].items():
        path = ROOT / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise ValueError(f"Changed ASR evidence: {name}")
        sources[name] = read(path)
    selected = project / "selected"
    corrected = selected / "lyrics"
    tracks = export(review, sources, wav, corrected)
    master = selected / f"{media_id}-ja.wav"
    copy_unchanged(wav, master)
    mp3 = selected / f"{media_id}-ja.mp3"
    if not mp3.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-n", "-i", str(master), "-map_metadata", "-1",
                        "-c:a", "libmp3lame", "-b:a", "320k", "-metadata", "artist=Musia",
                        "-metadata", f"title={config['title']}", str(mp3)], check=True)
    filename = config["publicFilename"]
    if Path(filename).name != filename or not filename.endswith(".mp3"):
        raise ValueError("publicFilename must be an MP3 basename")
    songs = ROOT.parent / "MusiaSongs"
    target = songs / "audio" / filename
    copy_unchanged(mp3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=songs, check=True)
    song_dir = ROOT / "website/data/songs" / media_id
    vocal = review["vocalSet"]
    for code in tracks:
        write(song_dir / f"lyrics/{vocal}/{code}.json", read(corrected / f"{code}.json"))
    cover = f"assets/covers/{media_id}-16x9.png"
    copy_unchanged(project / "cover-16x9.png", ROOT / "website" / cover)
    from PIL import Image
    with Image.open(project / "cover-16x9.png") as image:
        width, height = image.size
    if abs(width / height - 16 / 9) > 0.025:
        raise ValueError("Cover is not 16:9")
    duration = review["duration"]
    analysis = ROOT / config["analysis"]
    beats = read(analysis / "analysis/beats.json")
    chords = read(analysis / "analysis/chords.json")["chords"]
    musical = {
        "key": "Unverified", "bpm": round(beats["tempo_bpm"], 3), "timeSignature": "4/4",
        "meterStatus": "estimate", "quality": "analysis",
        "chords": [{"start": round(c["start"], 3), "end": round(min(c["end"], duration), 3),
                    "name": c["chord"], "confidence": round(c["confidence"], 3)} for c in chords if c["start"] < duration],
        "beats": [{"index": b["index"], "time": round(b["time"], 3)} for b in beats["beats"] if b["time"] < duration],
        "chordSource": "Selected audio analysis; not a musician-verified score",
        "beatSource": "Selected audio beat tracker; 4/4 is an unverified production target",
    }
    asset = {"id": config["assetId"], "label": "日本語", "selectorLabel": "日本語",
             "role": "vocal", "languageCode": "ja", "languageLabel": "日本語", "lyricSetId": vocal,
             "src": "https://lazyingart.github.io/MusiaSongs/audio/" + filename, "mime": "audio/mpeg", "musical": musical}
    features = {"ja": ["active-vocal", "furigana", "word-highlight"],
                "en": ["translation", "rough-highlight"], "zh-Hans": ["translation", "pinyin", "rough-highlight"]}
    infos = [{**read(corrected / f"{code}.json")["language"], "features": features[code],
              "path": f"lyrics/{vocal}/{code}.json"} for code in tracks]
    url = "https://fun.lazying.art/#" + media_id
    provenance = {**config["provenance"], "createdBy": "Musia", "aiGenerated": True,
                  "audioSha256": sha256(master), "publicMp3Sha256": sha256(target),
                  "generationProject": config["project"], "analysisRun": config["analysis"],
                  "lyricCorrection": config["review"]}
    manifest = {
        "schema": "fun.lazying.media.manifest.v1", "version": 1, "id": media_id, "kind": "song",
        "title": config["title"], "artist": "Musia", "localizedTitles": config["localizedTitles"],
        "description": config["description"], "caption": config["caption"],
        "generationCredit": "AI-generated music", "duration": duration, "canonicalUrl": url,
        "publication": {"visibility": "public", "stage": "published", "listed": True},
        "share": {"title": config["title"] + " | Musia", "description": config["description"],
                  "url": url, "image": cover, "siteName": "Fun Lazying Art"},
        "assets": {"primaryAudio": asset, "alternateAudio": [],
                   **{role: {"id": role, "label": config["title"], "role": role, "src": cover,
                             "mime": "image/png", "width": width, "height": height} for role in ("cover", "poster")}},
        "musical": musical, "textTracks": [], "lyricSets": [{"id": vocal, "label": "日本語", "languageCode": "ja", "tracks": infos}],
        "timeline": {"unit": "seconds", "lines": [{k: line[k] for k in ("id", "start", "end", "text")} for line in tracks["ja"]]},
        "provenance": provenance,
    }
    write(song_dir / "manifest.json", manifest)
    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read(catalog_path)
    item = {"id": media_id, "kind": "song", "title": config["title"], "artist": "Musia", "summary": config["description"],
            "manifest": f"data/songs/{media_id}/manifest.json", "cover": cover, "visibility": "public",
            "releaseStage": "published", "category": "music", "languages": list(tracks), "tags": config["tags"]}
    catalog["items"] = [item] + [entry for entry in catalog["items"] if entry["id"] != media_id]
    write(catalog_path, catalog)
    write(selected / "manifest.json", {**provenance, "audio": str(master.relative_to(ROOT)), "mp3": str(mp3.relative_to(ROOT)),
                                       "lyrics": str(corrected.relative_to(ROOT)), "duration": duration, "reviewedLineCount": len(tracks["ja"])})
    print(url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path)
    prepare(read(parser.parse_args().release))
