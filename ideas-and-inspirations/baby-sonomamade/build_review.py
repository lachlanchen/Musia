"""Reproduce the lyric decisions for the selected 112601 performance only."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = Path("data/creative_projects/baby-sonomamade-20261126")
R = P / "review/112601"


def load(path):
    return json.loads(path.read_text())


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


window = load(ROOT / R / "stem-windows.json")["windows"][0]
segments = window["segments"]
evidence = R / "stem-continuous.json"
save(ROOT / evidence, {"status": "ok", "language": "ja", "segments": segments})
draft = load(HERE / "meaning-reference.json")["lines"]
rows = []


def s(i, first=0, end=None):
    return (i, first, len(segments[i]["words"]) if end is None else end)


def line(ref, *spans, edits=(), override=None):
    ja, en, zh = override or draft[ref]
    words = [w["word"].strip() for i, a, b in spans for w in segments[i]["words"][a:b]]
    changes = [{"words": [a, b], "source": "".join(words[a:b]), "text": text,
                "reason": reason} for a, b, text, reason in edits]
    for change in reversed(changes):
        a, b = change["words"]
        words[a:b] = [change["text"]]
    assert "".join(words) == ja, ("".join(words), ja)
    rows.append({"ja": ja, "en": en, "zh-Hans": zh,
                 "anchors": [{"source": "stem", "segment": i, "words": [a, b]} for i, a, b in spans],
                 "replacements": changes})


orth = "Reading unchanged; use the written lyric's Japanese spelling."
close = "Use the draft for the sound-close, contextually supported reading."
baby = (0, 1, "ベイビー", orth)
lift = ("ベイビー顔上げて", "Baby, lift your head", "宝贝，抬起头来")
sing = ("歌おうよ", "Let's sing", "一起唱吧")
line(0, s(0))
line(None, s(1), override=("好きなシャツなら混ぜてみよう", "Mix and match those shirts you love", "把喜欢的衬衫搭配起来吧"))
line(2, s(2))
line(3, s(3))
line(4, s(4, 0, 8), edits=[(6, 8, "はかれない", orth)])
line(3, s(4, 8))
line(4, s(5, 0, 8), edits=[(6, 8, "はかれない", orth)])
line(5, s(5, 8))
line(6, s(6, 0, 5), edits=[baby])
line(7, s(6, 5))
line(8, s(7, 0, 8))
line(9, s(7, 8))
line(None, s(8, 0, 5), edits=[baby], override=lift)
line(None, s(8, 5, 9), override=sing)
line(12, s(8, 9, 16))
line(None, s(8, 16), override=("抱きしめて", "Hold it close", "紧紧拥抱吧"))
line(14, s(9), edits=[(3, 4, "すみ", orth)])
line(15, s(10), edits=[(6, 8, "おいで", close)])
line(16, s(11, 0, 8))
line(17, s(11, 9), s(12))
line(18, s(13, 0, 11), edits=[(9, 11, "いい", close)])
line(19, s(13, 11), s(14, 0, 8), edits=[(0, 4, "好きだと", close)])
line(20, s(14, 8))
line(21, s(15), edits=[(0, 1, "となり", orth)])
line(22, s(16), edits=[(3, 6, "ものさし", orth)])
line(23, s(17))
line(24, s(18), edits=[baby])
line(25, s(19))
line(26, s(20))
line(27, s(21))
line(None, s(22, 0, 4), edits=[baby, (1, 3, "顔上げ", close)], override=lift)
line(None, s(22, 4), override=sing)
line(None, s(23, 0, 6), override=("誰かになるためじゃ", "Not to become somebody else…", "不是为了变成别人……"))
line(30, s(24))
line(31, s(25))
line(32, s(26), edits=[baby])
line(33, s(27), edits=[(3, 5, "味方", close)])
line(34, s(28))
line(35, s(29), edits=[(0, 4, "ありのまま", close)])
wav = next((ROOT / P / "candidates/batch-112601").glob("*.wav"))
save(HERE / "reviewed-lyrics.json", {
    "mediaId": "baby-sonomamade", "title": "ベイビー、そのままで · Baby, Just as You Are",
    "vocalSet": "ja", "vocalLanguage": "ja", "audioSha256": digest(wav),
    "duration": 184, "releaseStage": "preview", "reviewStatus": "Corrected using Whisper large-v3 mix and isolated-vocal ASR, with a separate MOSS-Music transcription.",
    "timingStatus": "large-v3 vocal word spans; subdivisions approximate",
    "notes": "Retains the repeated pre-chorus lines and the restarted final-chorus phrase. Shortened phrases follow the vocal. Some soft syllables are uncertain; translations follow the selected performance.",
    "sources": {"stem": {"path": str(evidence), "sha256": digest(ROOT / evidence)}},
    "lines": rows})
