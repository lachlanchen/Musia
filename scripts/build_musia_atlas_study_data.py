#!/usr/bin/env python3
"""Build Musia Atlas study data for public Fun music items.

The output is intentionally evidence-labeled. Corrected lyrics come from the
website JSON tracks. Chords and beats are analysis-grade unless they were
already marked differently in the source manifest.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"
CATALOG = WEBSITE / "data" / "catalog.json"
RUNS = ROOT / "data" / "runs"
SONG_KINDS = {"song", "localized-song"}
LANGUAGE_RUN_TOKENS = {
    "en": {"en", "eng", "english"},
    "ja": {"ja", "jp", "jpn", "japanese"},
    "zh": {"zh", "zho", "cn", "mandarin", "chinese", "hans", "hant"},
    "yue": {"yue", "cantonese"},
}
ALL_LANGUAGE_TOKENS = set().union(*LANGUAGE_RUN_TOKENS.values())
GENERIC_MATCH_TOKENS = {
    "song",
    "music",
    "mixed",
    "mix",
    "vocal",
    "audio",
    "full",
    "normal",
    "original",
    "poem",
    "version",
    "trilingual",
    "localized",
    "localization",
    "generated",
    "selected",
    "analysis",
    "deep",
    "clean",
    "draft",
    "demo",
    "legacy",
    "ace",
    "sft",
    "xl",
    "turbo",
    "seed",
    "route",
    "diffrhythm",
    "dr",
    "zh",
    "en",
    "ja",
    "jp",
    "yue",
    "hans",
    "hant",
}
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KEY_ROOTS = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}
MAJOR_JIANPU = {
    0: "1",
    1: "#1",
    2: "2",
    3: "b3",
    4: "3",
    5: "4",
    6: "#4",
    7: "5",
    8: "b6",
    9: "6",
    10: "b7",
    11: "7",
}


def slug_tokens(value: str) -> set[str]:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return {token for token in text.split() if len(token) >= 2}


def numeric_bpm(value: Any) -> float:
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(value or ""))
    return float(match.group(1)) if match else 0.0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def midi_note_name(midi: float) -> str:
    value = int(round(midi))
    return f"{NOTE_NAMES[value % 12]}{value // 12 - 1}"


def key_root_pc(key: str) -> int:
    match = re.search(r"\b([A-G](?:#|b|♯|♭)?)", str(key or ""))
    if not match:
        return 0
    root = match.group(1).replace("♯", "#").replace("♭", "b")
    return KEY_ROOTS.get(root, 0)


def jianpu_for_midi(midi: float, key: str) -> str:
    value = int(round(midi))
    root = key_root_pc(key)
    degree = MAJOR_JIANPU[(value - root) % 12]
    root_reference = 60 + root
    while root_reference - value > 6:
        root_reference -= 12
    while value - root_reference > 17:
        root_reference += 12
    octave_delta = int((value - root_reference) // 12)
    if octave_delta > 0:
        degree += "'" * min(2, octave_delta)
    elif octave_delta < 0:
        degree += "," * min(2, abs(octave_delta))
    return degree


def parse_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result else None


def public_audio_assets(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any], str]]:
    assets = manifest.get("assets") or {}
    result: list[tuple[str, dict[str, Any], str]] = []
    primary = assets.get("primaryAudio")
    if isinstance(primary, dict):
        result.append(("assets.primaryAudio", primary, primary.get("id") or "primary-audio"))
    for index, asset in enumerate(assets.get("alternateAudio") or []):
        if isinstance(asset, dict):
            result.append((f"assets.alternateAudio[{index}]", asset, asset.get("id") or f"alternate-audio-{index}"))
    return result


def manifest_track_infos(manifest: dict[str, Any], asset: dict[str, Any]) -> list[dict[str, Any]]:
    lyric_sets = manifest.get("lyricSets") or []
    set_id = asset.get("lyricSetId")
    language_code = asset.get("languageCode")
    chosen = None
    for item in lyric_sets:
        if set_id and item.get("id") == set_id:
            chosen = item
            break
    if not chosen and language_code:
        for item in lyric_sets:
            if item.get("languageCode") == language_code:
                chosen = item
                break
    if chosen:
        return list(chosen.get("textTracks") or chosen.get("tracks") or [])
    return list(manifest.get("textTracks") or [])


def lyric_summary(manifest_dir: Path, manifest: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    tracks = []
    for info in manifest_track_infos(manifest, asset):
        path_text = info.get("path")
        if not path_text:
            continue
        path = manifest_dir / path_text
        if not path.exists():
            tracks.append({
                "code": info.get("code"),
                "path": path_text,
                "status": "missing"
            })
            continue
        data = read_json(path)
        lines = [line for line in data.get("lines") or [] if line.get("role", "lyric") != "instrumental"]
        starts = [float(line["start"]) for line in lines if isinstance(line.get("start"), (int, float))]
        ends = [float(line["end"]) for line in lines if isinstance(line.get("end"), (int, float))]
        tracks.append({
            "code": data.get("language", {}).get("code") or info.get("code"),
            "nativeLabel": data.get("language", {}).get("nativeLabel") or info.get("nativeLabel"),
            "path": path_text,
            "lineCount": len(lines),
            "firstLyricStart": round(min(starts), 3) if starts else None,
            "lastLyricEnd": round(max(ends), 3) if ends else None,
            "correction": (data.get("provenance") or {}).get("correction", "")
        })
    active = next((track for track in tracks if track.get("code") == asset.get("languageCode")), None) or (tracks[0] if tracks else None)
    return {
      "lyricSetId": asset.get("lyricSetId") or "",
      "activeLanguageCode": active.get("code") if active else asset.get("languageCode") or "",
      "activeTrackPath": active.get("path") if active else "",
      "trackCount": len(tracks),
      "tracks": tracks
    }


def active_track_data(manifest_dir: Path, manifest: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any] | None:
    infos = manifest_track_infos(manifest, asset)
    if not infos:
        return None
    language_code = asset.get("languageCode")
    chosen = None
    for info in infos:
        if info.get("code") == language_code:
            chosen = info
            break
    chosen = chosen or infos[0]
    path_text = chosen.get("path")
    if not path_text:
        return None
    path = manifest_dir / path_text
    if not path.exists():
        return None
    data = read_json(path)
    data["__path"] = str(path.relative_to(ROOT))
    return data


def sung_tokens(line: dict[str, Any]) -> list[dict[str, Any]]:
    tokens = line.get("tokens") if isinstance(line.get("tokens"), list) else []
    result = []
    for token in tokens:
        text = str(token.get("text") or "")
        if not text.strip() or re.fullmatch(r"[,，、。.!?？；;：:\s]+", text):
            continue
        start = parse_float(token.get("start"))
        end = parse_float(token.get("end"))
        if start is None or end is None or end <= start:
            continue
        result.append({"text": text, "start": start, "end": end})
    if result:
        return result

    text = str(line.get("singableText") or line.get("text") or "").strip()
    start = parse_float(line.get("start"))
    end = parse_float(line.get("end"))
    if not text or start is None or end is None or end <= start:
        return []
    parts = [part for part in re.split(r"\s+", text) if part]
    if len(parts) <= 1:
        parts = [char for char in text if not re.fullmatch(r"[,，、。.!?？；;：:\s]+", char)]
    if not parts:
        return []
    slot = (end - start) / len(parts)
    return [
        {"text": part, "start": start + slot * index, "end": start + slot * (index + 1)}
        for index, part in enumerate(parts)
    ]


def load_run_melody(record: dict[str, Any] | None) -> tuple[list[dict[str, Any]], str]:
    if not record or not record.get("melody"):
        return [], ""
    path = record["melody"]
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            time = parse_float(row.get("time"))
            midi = parse_float(row.get("midi"))
            f0 = parse_float(row.get("f0_hz"))
            voiced = str(row.get("voiced") or "").lower() == "true"
            if time is None or midi is None or not voiced:
                continue
            rows.append({
                "time": time,
                "midi": midi,
                "f0": f0 or 0.0,
                "note": row.get("note") or midi_note_name(midi),
            })
    return rows, str(path.relative_to(ROOT))


def active_chord_name(chords: list[dict[str, Any]], time: float) -> str:
    for chord in chords:
        if float(chord.get("start", -1)) <= time < float(chord.get("end", -1)):
            return str(chord.get("name") or "")
    previous = [chord for chord in chords if float(chord.get("end", -1)) <= time]
    return str(previous[-1].get("name") or "") if previous else ""


def build_melody_map(
    record: dict[str, Any] | None,
    manifest_dir: Path,
    manifest: dict[str, Any],
    asset: dict[str, Any],
    key: str,
    chords: list[dict[str, Any]],
) -> dict[str, Any]:
    samples, source = load_run_melody(record)
    track = active_track_data(manifest_dir, manifest, asset)
    if not samples or not track:
        return {
            "confidence": "unavailable",
            "source": source,
            "key": key,
            "notation": "jianpu/simple numbered notes",
            "lines": [],
        }

    lines = []
    for line in track.get("lines") or []:
        if line.get("role", "lyric") == "instrumental":
            continue
        line_notes = []
        for token in sung_tokens(line):
            values = [sample["midi"] for sample in samples if token["start"] <= sample["time"] < token["end"]]
            if len(values) < 2:
                continue
            midi = round(median(values), 1)
            midpoint = (token["start"] + token["end"]) / 2.0
            line_notes.append({
                "text": token["text"],
                "start": round(token["start"], 3),
                "end": round(token["end"], 3),
                "midi": midi,
                "note": midi_note_name(midi),
                "jianpu": jianpu_for_midi(midi, key),
                "chord": active_chord_name(chords, midpoint),
            })
        if line_notes:
            lines.append({
                "lineId": line.get("id"),
                "start": round(float(line.get("start", line_notes[0]["start"])), 3),
                "end": round(float(line.get("end", line_notes[-1]["end"])), 3),
                "key": key,
                "confidence": "analysis",
                "source": source,
                "summary": " ".join(note["jianpu"] for note in line_notes),
                "tokens": line_notes,
            })

    return {
        "confidence": "analysis" if lines else "unavailable",
        "source": source,
        "key": key,
        "notation": "jianpu/simple numbered notes",
        "description": "Token-level median vocal F0 converted to Western note names and numbered jianpu degrees. Analysis-grade, not human-transcribed sheet music.",
        "lines": lines,
    }


def normalize_chords(chords: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for item in chords or []:
        start = item.get("start")
        end = item.get("end")
        name = item.get("name") or item.get("chord")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or not name:
            continue
        chord = {
            "start": round(float(start), 3),
            "end": round(float(end), 3),
            "name": str(name)
        }
        if item.get("degree"):
            chord["degree"] = item.get("degree")
        if isinstance(item.get("confidence"), (int, float)):
            chord["confidence"] = round(float(item["confidence"]), 4)
        result.append(chord)
    return result


def normalize_beats(beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for index, item in enumerate(beats or []):
        time = item.get("time")
        if not isinstance(time, (int, float)):
            continue
        result.append({
            "index": int(item.get("index", index)),
            "time": round(float(time), 3)
        })
    return result


def infer_bpm_from_beats(beats: list[dict[str, Any]]) -> float:
    times = [float(beat["time"]) for beat in beats if isinstance(beat.get("time"), (int, float))]
    if len(times) < 3:
        return 0.0
    intervals = [b - a for a, b in zip(times, times[1:]) if 0.15 <= b - a <= 3.0]
    if not intervals:
        return 0.0
    intervals.sort()
    median = intervals[len(intervals) // 2]
    return round(60.0 / median, 3) if median else 0.0


def run_index() -> list[dict[str, Any]]:
    records = []
    if not RUNS.exists():
        return records
    for analysis_dir in RUNS.glob("*/analysis"):
        run_dir = analysis_dir.parent
        beats = analysis_dir / "beats.json"
        chords = analysis_dir / "chords.json"
        melody = analysis_dir / "melody_f0.csv"
        if not beats.exists() and not chords.exists() and not melody.exists():
            continue
        records.append({
            "run": run_dir.name,
            "runPath": str(run_dir.relative_to(ROOT)),
            "tokens": slug_tokens(run_dir.name),
            "beats": beats if beats.exists() else None,
            "chords": chords if chords.exists() else None,
            "melody": melody if melody.exists() else None
        })
    return records


def source_stem(src: str) -> str:
    if not src:
        return ""
    parsed = urlparse(src)
    name = Path(parsed.path or src).stem
    return name


def content_tokens(value: str) -> set[str]:
    return slug_tokens(value) - ALL_LANGUAGE_TOKENS - GENERIC_MATCH_TOKENS


def language_family(code: str) -> str:
    value = str(code or "").lower()
    if value.startswith("zh"):
        return "zh"
    if value.startswith("yue"):
        return "yue"
    if value.startswith("ja"):
        return "ja"
    if value.startswith("en"):
        return "en"
    return value


def score_run(record: dict[str, Any], media_id: str, title: str, asset: dict[str, Any]) -> int:
    run = record["run"].lower()
    asset_id = str(asset.get("id") or "").lower()
    media = media_id.lower()
    stem = source_stem(asset.get("src", "")).lower()
    language = language_family(asset.get("languageCode") or "")
    score = 0
    if asset_id and asset_id in run:
        score += 140
    if media and media in run:
        score += 120
    if stem and stem in run:
        score += 100
    record_content = set(record["tokens"]) - ALL_LANGUAGE_TOKENS
    for key in (media, asset_id, stem, title):
        score += 8 * len(record_content & content_tokens(key))
    lexical_score = score
    if language and language != "mul":
        own_tokens = LANGUAGE_RUN_TOKENS.get(language, {language})
        other_tokens = set().union(*[
            tokens for family, tokens in LANGUAGE_RUN_TOKENS.items()
            if family != language
        ])
        if lexical_score and record["tokens"] & own_tokens:
            score += 60
        if record["tokens"] & other_tokens:
            score -= 90
    if not lexical_score:
        return -999
    return score


def choose_run(index: list[dict[str, Any]], media_id: str, title: str, asset: dict[str, Any]) -> dict[str, Any] | None:
    ranked = sorted(
        ((score_run(record, media_id, title, asset), record) for record in index),
        key=lambda item: item[0],
        reverse=True,
    )
    if not ranked or ranked[0][0] < 40:
        return None
    return ranked[0][1]


def load_run_chords(record: dict[str, Any] | None) -> tuple[list[dict[str, Any]], str]:
    if not record or not record.get("chords"):
        return [], ""
    data = read_json(record["chords"])
    return normalize_chords(data.get("chords") or []), str(record["chords"].relative_to(ROOT))


def load_run_beats(record: dict[str, Any] | None) -> tuple[list[dict[str, Any]], float, str]:
    if not record or not record.get("beats"):
        return [], 0.0, ""
    data = read_json(record["beats"])
    beats = normalize_beats(data.get("beats") or [])
    bpm = numeric_bpm(data.get("tempo_bpm")) or infer_bpm_from_beats(beats)
    return beats, bpm, str(record["beats"].relative_to(ROOT))


def unique_chords(chords: list[dict[str, Any]], limit: int = 8) -> list[str]:
    seen = []
    for chord in chords:
        name = chord.get("name")
        if name and name not in seen:
            seen.append(name)
        if len(seen) >= limit:
            break
    return seen


def build_study_for_item(item: dict[str, Any], index: list[dict[str, Any]]) -> tuple[Path, dict[str, Any]]:
    manifest_path = WEBSITE / item["manifest"]
    manifest = read_json(manifest_path)
    manifest_dir = manifest_path.parent
    media_id = manifest.get("id") or item["id"]
    title = manifest.get("title") or item.get("title") or media_id
    manifest_musical = manifest.get("musical") or {}
    manifest_chords = normalize_chords(manifest_musical.get("chords") or [])
    manifest_bpm = numeric_bpm(manifest_musical.get("bpm"))
    manifest_beats = normalize_beats(manifest_musical.get("beats") or [])
    assets: dict[str, Any] = {}

    for source_path, asset, asset_id in public_audio_assets(manifest):
        asset_musical = asset.get("musical") or {}
        asset_chords = normalize_chords(asset_musical.get("chords") or [])
        asset_beats = normalize_beats(asset_musical.get("beats") or [])
        asset_bpm = numeric_bpm(asset_musical.get("bpm"))
        selected_run = choose_run(index, media_id, title, asset)
        run_chords, run_chord_source = load_run_chords(selected_run)
        run_beats, run_bpm, run_beat_source = load_run_beats(selected_run)

        chords = asset_chords or manifest_chords or run_chords
        if asset_chords:
            chord_source = f"manifest:{source_path}.musical.chords"
        elif manifest_chords:
            chord_source = "manifest:musical.chords"
        else:
            chord_source = run_chord_source

        beats = asset_beats or manifest_beats or run_beats
        if asset_beats:
            beat_source = f"manifest:{source_path}.musical.beats"
        elif manifest_beats:
            beat_source = "manifest:musical.beats"
        else:
            beat_source = run_beat_source

        bpm = asset_bpm or manifest_bpm or run_bpm or infer_bpm_from_beats(beats)
        key = (
            asset_musical.get("key")
            or manifest_musical.get("key")
            or manifest.get("key")
            or "C major"
        )
        melody = build_melody_map(selected_run, manifest_dir, manifest, asset, key, chords)
        assets[asset_id] = {
            "label": asset.get("label") or asset.get("languageLabel") or asset_id,
            "languageCode": asset.get("languageCode") or "",
            "src": asset.get("src") or "",
            "bpm": round(float(bpm), 3) if bpm else 0,
            "key": key,
            "timeSignature": asset_musical.get("timeSignature") or manifest_musical.get("timeSignature") or "4/4",
            "beatConfidence": "analysis" if beats else "estimated",
            "beatSource": beat_source or ("estimated from BPM" if bpm else ""),
            "beats": beats,
            "chordConfidence": "analysis" if chords else "estimated",
            "chordSource": chord_source or "",
            "chords": chords,
            "melodyConfidence": melody.get("confidence", "unavailable"),
            "melodySource": melody.get("source", ""),
            "melody": melody,
            "lyricEvidence": lyric_summary(manifest_dir, manifest, asset),
            "practice": {
                "beginnerFocus": unique_chords(chords),
                "counting": "Count quarter-note pulses first, then add one strum at each chord change.",
                "warning": "Atlas chord and beat maps are analysis-grade unless separately marked verified; use listening before formal teaching."
            }
        }

    payload = {
        "schema": "https://fun.lazying.art/schemas/musia-atlas-study.v1.json",
        "version": 1,
        "toolName": "Musia Atlas",
        "mediaId": media_id,
        "title": f"{title} Atlas",
        "summary": "Detailed practice data for corrected lyrics, chord changes, beat timing, and guitar display.",
        "defaultAssetId": next(iter(assets), ""),
        "dataPolicy": [
            "Lyrics use corrected Fun website timing JSON for each active vocal.",
            "Chord and beat maps are analysis-grade unless explicitly marked verified.",
            "Capo, transpose, and simplify are display-only helpers; source audio is unchanged.",
            "Instrumental spans are UI state only and are not encoded as lyric lines."
        ],
        "assets": assets,
        "lesson": {
            "name": "Atlas first pass",
            "goal": "Help a beginner follow lyrics, chord changes, and beat entry without needing to sing first.",
            "steps": [
                "Listen once and tap the beat lane.",
                "Loop one phrase and speak the lyric rhythmically.",
                "Play one strum per displayed chord change.",
                "Only add a fuller strumming pattern after the lyric and chord entry feel stable."
            ]
        }
    }
    return manifest_dir / "study.json", payload


def write_atlas_redirect(media_id: str) -> None:
    path = WEBSITE / "atlas" / media_id / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=../../?mode=atlas&amp;media={media_id}">
  <title>Musia Atlas - {media_id}</title>
  <script>
    window.location.replace("../../?mode=atlas&media={media_id}");
  </script>
</head>
<body>
  <p><a href="../../?mode=atlas&amp;media={media_id}">Open Musia Atlas</a></p>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media-id", action="append", default=[], help="Build only this media id. Can repeat.")
    parser.add_argument("--all", action="store_true", help="Build all public song/localized-song catalog items.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without writing files.")
    args = parser.parse_args()

    catalog = read_json(CATALOG)
    wanted = set(args.media_id)
    items = [
        item for item in catalog.get("items", [])
        if item.get("manifest") and item.get("kind") in SONG_KINDS and (args.all or item.get("id") in wanted)
    ]
    if not items:
        raise SystemExit("No matching catalog music items. Use --all or --media-id.")

    index = run_index()
    built = []
    for item in items:
        out_path, payload = build_study_for_item(item, index)
        if not args.dry_run:
            write_json(out_path, payload)
            write_atlas_redirect(payload["mediaId"])
        built.append((payload["mediaId"], out_path, len(payload["assets"])))

    for media_id, path, asset_count in built:
        print(f"{media_id}: {asset_count} asset(s) -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
