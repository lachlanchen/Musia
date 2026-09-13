#!/usr/bin/env python3
"""Prepare the independently audited ACE Changfeng rendition; never push or generate.

The selected manifest binds the audio, corrected lyrics, and analysis by hash.
MiniMax remains a separate, playable item with its original media ID.
"""

from pathlib import Path
import json
import shutil
import subprocess

from prepare_ban_qu_chang_an_fun_item import read_json, write_json, digest

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "data/creative_projects/ban-qu-chang-an-ace-changfeng-20260914"
MEDIA_ID = "ban-qu-chang-an-ace-changfeng"
TITLE = "半曲长安 · ACE · 长风"
LANGUAGES = ("zh-Hans", "en", "ja")


def main():
    selected = read_json(PROJECT / "selected/manifest.json")
    audio = ROOT / selected["audio"]
    mp3 = ROOT / selected["mp3"]
    lyrics = ROOT / selected["lyrics"]
    analysis = ROOT / selected["analysis"]
    seed = selected["seed"]
    audio_hash = digest(audio)
    if audio_hash != selected["audioSha256"]:
        raise ValueError("Selected WAV changed after lyric review")
    if digest(mp3) != selected["mp3Sha256"]:
        raise ValueError("Selected MP3 changed after packaging")
    tracks = {code: read_json(lyrics / f"{code}.json") for code in LANGUAGES}
    source = tracks["zh-Hans"]["lines"]
    if len(source) != selected["reviewedLineCount"]:
        raise ValueError("Reviewed lyric coverage changed")
    lyric_set = f"zh-ace-{seed}"
    song_dir = ROOT / "website/data/songs" / MEDIA_ID
    for code, track in tracks.items():
        if track["mediaId"] != MEDIA_ID or track["provenance"]["audioSha256"] != audio_hash:
            raise ValueError(f"Wrong vocal evidence: {code}")
        if [(x["id"], x["start"], x["end"]) for x in track["lines"]] != [(x["id"], x["start"], x["end"]) for x in source]:
            raise ValueError(f"Translation timing/line mismatch: {code}")
        track["provenance"].update(releaseStage="published")
        write_json(song_dir / f"lyrics/{lyric_set}/{code}.json", track)

    filename = f"{MEDIA_ID}-zh-seed{seed}-20260914.mp3"
    songs_repo = ROOT.parent / "MusiaSongs"
    target = songs_repo / "audio" / filename
    if target.exists() and digest(target) != digest(mp3):
        raise FileExistsError("Versioned public filename already contains another render")
    if not target.exists():
        shutil.copy2(mp3, target)
    subprocess.run(["node", "scripts/build-audio-json.js"], cwd=songs_repo, check=True)
    cover_path = f"assets/covers/{MEDIA_ID}-16x9.png"
    shutil.copy2(PROJECT / "cover-16x9.png", ROOT / "website" / cover_path)
    from PIL import Image
    with Image.open(PROJECT / "cover-16x9.png") as image:
        width, height = image.size
    duration = selected["duration"]
    beats = read_json(analysis / "analysis/beats.json")
    chords = read_json(analysis / "analysis/chords.json")["chords"]
    musical = {
        "key": "Unverified", "bpm": round(beats["tempo_bpm"], 3),
        "timeSignature": "4/4", "meterStatus": "estimate", "quality": "analysis",
        "chords": [{"start": round(c["start"], 3), "end": round(min(c["end"], duration), 3),
                    "name": c["chord"], "confidence": round(c["confidence"], 3)}
                   for c in chords if c["start"] < duration],
        "beats": [{"index": b["index"], "time": round(b["time"], 3)}
                  for b in beats["beats"] if b["time"] < duration],
        "chordSource": "Exact-render audio analysis; estimates, not a verified score",
        "beatSource": "Exact-render beat tracking; meter is a production target, not verified notation",
    }
    asset = {"id": f"{MEDIA_ID}-zh", "label": "中文", "selectorLabel": "中文",
             "publicRoleLabel": "中文", "role": "vocal", "languageCode": "zh-Hans",
             "languageLabel": "中文", "lyricSetId": lyric_set,
             "src": "https://lazyingart.github.io/MusiaSongs/audio/" + filename,
             "mime": "audio/mpeg", "musical": musical}
    features = {"zh-Hans": ["active-vocal", "pinyin", "word-highlight"],
                "en": ["translation", "rough-highlight"],
                "ja": ["translation", "furigana", "rough-highlight"]}
    track_infos = [{**tracks[code]["language"], "features": features[code],
                    "path": f"lyrics/{lyric_set}/{code}.json"} for code in LANGUAGES]
    description = "Half a melody waits in Chang'an. Across the Yellow River and red mountains, a rider carries the promise of playing it again beside the one she loves."
    url = "https://fun.lazying.art/#" + MEDIA_ID
    manifest = {
        "schema": "fun.lazying.media.manifest.v1", "version": 1, "id": MEDIA_ID,
        "kind": "song", "title": TITLE, "artist": "Musia",
        "localizedTitles": {"zh-Hans": TITLE, "en": "The Melody I Left in Chang'an · ACE · Long Wind",
                            "ja": "長安に残した調べ · ACE · 遥かな風"},
        "description": description, "caption": "黄河再宽，隔不断想念；风沙再大，认得你的眼。",
        "generationCredit": "AI-generated music · ACE-Step XL Turbo",
        "duration": duration, "canonicalUrl": url,
        "publication": {"visibility": "public", "stage": "published", "listed": True},
        "share": {"title": TITLE + " | Musia", "description": description,
                  "url": url, "image": cover_path, "siteName": "Fun Lazying Art"},
        "assets": {"primaryAudio": asset, "alternateAudio": [],
                   **{role: {"id": role, "label": TITLE, "role": role,
                              "src": cover_path, "mime": "image/png", "width": width, "height": height}
                      for role in ("cover", "poster")}},
        "musical": musical, "textTracks": [],
        "lyricSets": [{"id": lyric_set, "label": "中文", "languageCode": "zh-Hans", "tracks": track_infos}],
        "timeline": {"unit": "seconds", "lines": [{k: row[k] for k in ("id", "start", "end", "text")} for row in source]},
        "provenance": {"createdBy": "Musia", "model": "acestep-v15-xl-turbo", "aiGenerated": True,
                       "selectedSeed": seed, "modelRevision": selected["aceCommit"],
                       "audioSha256": audio_hash, "publicMp3Sha256": digest(target),
                       "generationProject": str(PROJECT.relative_to(ROOT)),
                       "analysisRun": str(analysis.relative_to(ROOT)),
                       "lyricCorrection": selected["lyricCorrection"],
                       "quality": {"audioHealth": "pass", "humanListeningApproved": False,
                                   "timing": "ASR-derived word anchors, approximate musical analysis"},
                       "coverSource": "Built-in image generation; fresh song-specific long-wind/Chang'an artwork"},
    }
    write_json(song_dir / "manifest.json", manifest)
    catalog_path = ROOT / "website/data/catalog.json"
    catalog = read_json(catalog_path)
    for entry in catalog["items"]:
        if entry["id"] == "ban-qu-chang-an":
            entry["title"] = "半曲长安 · MiniMax"
    old_path = ROOT / "website/data/songs/ban-qu-chang-an/manifest.json"
    old = read_json(old_path)
    old["title"] = "半曲长安 · MiniMax"
    old["localizedTitles"] = {"zh-Hans": old["title"], "en": "The Melody I Left in Chang'an · MiniMax", "ja": "長安に残した調べ · MiniMax"}
    old["share"]["title"] = old["title"] + " | Musia"
    write_json(old_path, old)
    entry = {"id": MEDIA_ID, "kind": "song", "title": TITLE, "artist": "Musia",
             "summary": description, "manifest": f"data/songs/{MEDIA_ID}/manifest.json",
             "cover": cover_path, "visibility": "public", "releaseStage": "published", "category": "music",
             "languages": list(LANGUAGES),
             "tags": ["music", "Mandarin", "guofeng", "pop-rock", "Aya Chan", "Chang'an", "Yellow River", "homecoming", "chords"]}
    catalog["items"] = [entry] + [x for x in catalog["items"] if x["id"] != MEDIA_ID]
    write_json(catalog_path, catalog)
    print(url)


if __name__ == "__main__":
    main()
