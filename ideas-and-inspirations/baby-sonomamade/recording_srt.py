"""Export the reviewed Japanese words on the trimmed publication timeline."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACK = ROOT / "website/data/songs/baby-sonomamade/lyrics/ja/ja.json"


def stamp(t):
    m, ms = divmod(round(t * 1000), 60_000)
    return f"{m // 60:02}:{m % 60:02}:{ms // 1000:02},{ms % 1000:03}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--offset", type=float, required=True)
    args = parser.parse_args()
    lines = json.loads(TRACK.read_text())["lines"]
    assert all(args.offset <= l["start"] < l["end"] <= 184 for l in lines)
    cues = [f"{i}\n{stamp(l['start']-args.offset)} --> {stamp(l['end']-args.offset)}\n{l['text']}\n" for i, l in enumerate(lines, 1)]
    args.output.write_text("\n".join(cues), encoding="utf-8")
