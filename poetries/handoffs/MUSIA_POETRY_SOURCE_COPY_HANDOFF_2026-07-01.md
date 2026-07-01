# Musia Poetry Source Copy Handoff - 2026-07-01

Use this handoff to populate Musia's local poetry shelf for song generation.
The authoritative target list is:

```text
poetries/poetry_pdf_targets.json
```

The original Books handoffs copied into this repo are:

```text
poetries/handoffs/MANYOSHU_KOKIN_WAKA_PDF_HANDOFF_2026-07-01.md
poetries/handoffs/SHIJING_CHUCI_TANG_PDF_HANDOFF_2026-07-01.md
```

## Copy Rule

Copy PDFs into the Musia paths below. Do not overwrite existing valid PDFs
unless replacing a known partial or bad export.

```bash
cp -n "/home/lachlan/Downloads/<downloaded-file>.pdf" \
  "/home/lachlan/ProjectsLFS/Musia/poetries/sources/<target>.pdf"
```

Validate after copying:

```bash
cd /home/lachlan/ProjectsLFS/Musia
python3 poetries/scripts/validate_pdf_headers.py
```

Use strict mode when a song-production workflow requires all source PDFs:

```bash
python3 poetries/scripts/validate_pdf_headers.py --strict
```

## Musia Targets

| Work | Language | Musia local target |
| --- | --- | --- |
| `万葉集` | Japanese | `poetries/sources/japanese/manyoshu/ja-wikisource-export/万葉集-Wikisource.pdf` |
| `万葉集 (鹿持雅澄訓訂)` | Japanese | `poetries/sources/japanese/manyoshu/ja-wikisource-export/万葉集 (鹿持雅澄訓訂)-Wikisource.pdf` |
| `万葉集 (奈良女子高等師範学校国語研究室編)` | Japanese | `poetries/sources/japanese/manyoshu/ja-wikisource-export/万葉集 (奈良女子高等師範学校国語研究室編)-Wikisource.pdf` |
| `古今和歌集` | Japanese | `poetries/sources/japanese/kokin-wakashu/ja-wikisource-export/古今和歌集-Wikisource.pdf` |
| `詩經` | Chinese | `poetries/sources/chinese/shijing/zh-wikisource-export/詩經-Wikisource.pdf` |
| `Classic of Poetry` | English | `poetries/sources/chinese/shijing/en-wikisource-export/Classic-of-Poetry-Wikisource.pdf` |
| `詩経` | Japanese | `poetries/sources/chinese/shijing/ja-wikisource-export/詩経-Wikisource.pdf` |
| `楚辭` | Chinese | `poetries/sources/chinese/chuci/zh-wikisource-export/楚辭-Wikisource.pdf` |
| `唐詩三百首` | Chinese | `poetries/sources/chinese/tang-poetry/zh-wikisource-export/唐詩三百首-Wikisource.pdf` |
| `The Jade Mountain` | English | `poetries/sources/chinese/tang-poetry/en-wikisource-export/The-Jade-Mountain-Wikisource.pdf` |

## Current Local Clues

At the time this handoff was written, `/home/lachlan/Downloads` had several
Chinese-classics PDFs such as `詩經.pdf`, `楚辭.pdf`, `唐詩三百首.pdf`,
`The Book Of Songs_ The Ancient Chinese Classic Of Poetry.pdf`, and
`The Songs of Chu_ An Anthology of Ancient Chinese Poetry by Qu Yuan and Others.pdf`.
Those are useful for manual reading and cross-checking, but only copy them into
the `*-wikisource-export` targets if they are actually the matching Wikisource
PDF exports. Otherwise place them in a separate local reading folder and keep
them out of git.

No obvious `万葉集` or `古今和歌集` PDF was present in `/home/lachlan/Downloads`
when checked. Use the Wikisource export URLs in the original handoff or copy
from the Books archive after a browser/download tool succeeds.

## Song-Production Use

Before generating a poetry song from these sources:

1. Create a per-song project note with the chosen poem text and source path.
2. Add pronunciation notes and risky-character readings.
3. Decide whether to use exact original text, selected/repeated original text,
   or a modern adapted lyric.
4. After generation, correct lyrics against ASR plus manual listening.
5. Update Fun Lazying Art website JSON only after the lyric correction pass.
