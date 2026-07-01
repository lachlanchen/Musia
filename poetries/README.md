# Musia Poetry Source Library

This folder stores source material and handoff notes for making Musia songs from
classical poetry. Keep the small metadata, handoff notes, and validation scripts
in git. Keep large PDFs, EPUBs, scanned books, and downloaded archives local.

## Current Source Sets

| Set | Works | Use for |
| --- | --- | --- |
| Japanese poetry | `万葉集`, `古今和歌集` | Waka songs, Japanese original-poem songs, JP master lyric research |
| Chinese classics | `詩經`, `楚辭`, `唐詩三百首` | Chinese poem songs, classical pronunciation checks, adapted lyric writing |

The original Books handoff notes are copied in `poetries/handoffs/`. The
Musia-local target paths are listed in `poetries/poetry_pdf_targets.json`.

## Local PDF Workflow

1. Download or copy the PDF into the target path from
   `poetries/poetry_pdf_targets.json`.
2. Use `cp -n` or `cp --update=none` first, so a valid existing PDF is not
   overwritten by a partial export.
3. Validate headers:

```bash
python3 poetries/scripts/validate_pdf_headers.py
```

Use strict mode when a pipeline requires all PDFs to exist:

```bash
python3 poetries/scripts/validate_pdf_headers.py --strict
```

## Song-Generation Rule

For every poem-song project:

1. Verify source text from one or more trusted sources.
2. Prepare pronunciation notes before generation, especially for classical
   Chinese polyphones, rare characters, and Japanese historical orthography.
3. Decide whether the song should be exact original-text, selected/repeated
   original-text, or adapted modern singable lyrics.
4. Generate with the best available model route.
5. Audit the rendered vocal with ASR plus manual listening.
6. Publish website lyrics that match the audio while preserving the source text
   whenever the sound is close and the source is more beautiful.

This folder is the source shelf. Generated songs, stems, website data, and
recorded videos stay in their existing Musia project locations.
