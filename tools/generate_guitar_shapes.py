#!/usr/bin/env python3
"""Validate standard-tuning voicings and sync native/web source tables."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PITCH = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def validate(data):
    assert data["version"] == 1 and data["tuningMidi"] == [40, 45, 50, 55, 59, 64]
    rows = data["shapes"]
    assert {r["name"] for r in rows} == {root + suffix for root in PITCH for suffix in ("", "m")}
    assert len(rows) == 24
    for r in rows:
        frets, fingers = r["frets"], r["fingers"]
        assert len(frets) == len(fingers) == 6
        assert all(type(f) is int and -1 <= f <= 12 for f in frets)
        assert all(type(finger) is int for finger in fingers)
        assert all((finger == 0 if fret <= 0 else 1 <= finger <= 4) for fret, finger in zip(frets, fingers))
        minor = r["name"].endswith("m")
        root = PITCH[r["name"][:-1] if minor else r["name"]]
        expected = {(root + interval) % 12 for interval in (0, 3 if minor else 4, 7)}
        pitches = [(note + fret) % 12 for note, fret in zip(data["tuningMidi"], frets) if fret >= 0]
        assert set(pitches) == expected and pitches[0] == root, r["name"]
        start = 1 if max(frets) <= 4 else min(f for f in frets if f > 0)
        assert all(start <= f < start + 4 for f in frets if f > 0)
        for fret, first, last, finger in r["barres"]:
            assert all(type(value) is int for value in (fret, first, last, finger))
            assert 0 <= first < last <= 5 and 1 <= finger <= 4
            assert all(f >= fret for f in frets[first:last + 1])
            assert frets[first] == frets[last] == fret
            assert fingers[first] == fingers[last] == finger
        for finger in range(1, 5):
            positions = [i for i, f in enumerate(fingers) if f == finger]
            if len(positions) > 1:
                assert any(first <= min(positions) and last >= max(positions) and f == finger
                           for _, first, last, f in r["barres"]), r["name"]
    return {r["name"]: [r["frets"], r["fingers"], *r["barres"]] for r in rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = validate(json.loads((ROOT / "apps/shared/guitar-shapes.json").read_text()))
    swift = "    private static let shapes: [String: [[Int]]] = [\n" + "\n".join(
        f'        "{name}": {json.dumps(values)},' for name, values in rows.items()) + "\n    ]"
    kotlin = "private val shapes: Map<String, List<List<Int>>> = mapOf(\n" + "\n".join(
        f'    "{name}" to listOf(' + ", ".join("listOf(" + ", ".join(map(str, value)) + ")" for value in values) + "),"
        for name, values in rows.items()) + "\n)"
    js = "const shapes = " + json.dumps(rows, separators=(",", ":")) + ";"
    outputs = {"apps/ios/Musia/Core/GuitarShape.swift": swift,
               "apps/android/app/src/main/kotlin/art/lazying/musia/GuitarShapes.kt": kotlin,
               "apps/web/guitar-shapes.js": js}
    for relative, table in outputs.items():
        path = ROOT / relative
        source = path.read_text()
        rendered, count = re.subn(r"(?<=// BEGIN GENERATED SHAPES\n).*?(?=^[ \t]*// END GENERATED SHAPES)",
                                 lambda _: table + "\n", source, flags=re.S | re.M)
        assert count == 1, relative
        if args.check:
            assert source == rendered, f"Stale chord table: {relative}; run {parser.prog}"
        elif rendered != source:
            path.write_text(rendered)
    print("24 voicings: exact chord tones, root bass, fingers, barres, fret viewport and 3 client tables verified")


if __name__ == "__main__":
    main()
