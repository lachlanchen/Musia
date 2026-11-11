#!/usr/bin/env python3
"""Build a time-shifted reviewed SRT and immutable publication input receipt."""

import hashlib
import json
import argparse
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
START = 17.136
DURATION = 184 - START


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(seconds):
    millis = round(max(0, seconds) * 1000)
    seconds, millis = divmod(millis, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", type=int)
    args = parser.parse_args()
    song = ROOT / "website/data/songs/im-a-spy"
    lyric_path = song / "lyrics/en-vocal/en.json"
    lines = json.loads(lyric_path.read_text())["lines"]
    assert len(lines) == 49
    audio = ROOT / "data/creative_projects/im-a-spy-20261111/selected/im-a-spy-en.mp3"
    assert digest(audio) == "77ff438fbc13308ce10408cdf44401a1da230caa020daf71e132346a28a9461a"
    output = ROOT / "recorded_videos/im-a-spy"
    output.mkdir(parents=True, exist_ok=True)
    cues = []
    for index, line in enumerate(lines, 1):
        assert START <= line["start"] < line["end"] <= 184
        cues.append(f"{index}\n{timestamp(line['start'] - START)} --> "
                    f"{timestamp(line['end'] - START)}\n{line['text']}\n")
    srt = output / "im-a-spy-recording-reviewed.en.srt"
    srt.write_text("\n".join(cues), encoding="utf-8")
    receipt = {
        "mediaId": "im-a-spy", "title": "我是间谍 · I'm a Spy",
        "audio": str(audio), "audioSha256": digest(audio),
        "lyrics": str(lyric_path), "lyricsSha256": digest(lyric_path),
        "lineCount": len(lines), "sourceStart": START, "duration": DURATION,
        "authoritativeSrt": str(srt), "srtSha256": digest(srt),
        "videoPlatforms": ["shipinhao", "instagram", "youtube", "douyin"],
        "musicPlatforms": ["shipinhao_music"],
        "burnSubtitles": False, "portraitBlurFill": False,
        "layout": "player-current-trilingual-lyrics-chords-guitar",
        "website": "https://fun.lazying.art/#im-a-spy",
    }
    (output / "publication-inputs.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.video_id:
        with urlopen("http://127.0.0.1:18787/api/ui-settings/logo_settings", timeout=20) as response:
            logo = json.load(response)["value"]
        assert Path(logo["logoPath"]).is_file()
        logo.update(enabled=True, position="top-right", heightRatio=0.028)
        options = {
            "burnSubtitles": False, "translationLanguages": [],
            "authoritativeSubtitles": True, "autoCorrectSubtitles": False,
            "usePolishedSubtitles": True, "subtitleSourceVersion": "polished",
            "publicationMode": "override", "persistSettings": False,
            "publishCategory": "musia", "logo": logo,
            "burnLayout": {"portraitBlurFill": {"enabled": False}},
        }
        context = (ROOT / "handoff/lazyedit/im-a-spy/listener-context.md").read_text()
        process = dict(options, **{
            "async": True,
            "steps": ["keyframes", "burn", "metadata_zh", "metadata_en", "metadata_ja", "cover"],
            "metadataPrompt": context, "notes": context,
        })
        publish = {
            "platforms": {name: True for name in receipt["videoPlatforms"]},
            "options": dict(options, metadataPrompt="", notes="", useCorrectionPromptForMetadata=False),
            "persistSettings": False,
        }
        for name, payload in [("process", process), ("publish", publish)]:
            (output / f"lazyedit-{args.video_id}-{name}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(srt)


if __name__ == "__main__":
    main()
