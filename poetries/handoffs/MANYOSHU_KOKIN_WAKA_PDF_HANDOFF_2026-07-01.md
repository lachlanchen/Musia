# Manyoshu And Kokin Wakashu Wikisource PDF Handoff - 2026-07-01

Use this handoff when another browser/download tool can successfully fetch
Wikisource PDF exports for `万葉集` and `古今和歌集`. The EPUB exports already
exist; this note is only for copying PDF files into the same archive folders.

## Target Files

| Work | Wikisource PDF export URL | Copy PDF to |
| --- | --- | --- |
| `万葉集` | `https://ws-export.wmcloud.org/?lang=ja&format=pdf&page=%E4%B8%87%E8%91%89%E9%9B%86` | `resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集-Wikisource.pdf` |
| `万葉集 (鹿持雅澄訓訂)` | `https://ws-export.wmcloud.org/?lang=ja&format=pdf&page=%E4%B8%87%E8%91%89%E9%9B%86+%28%E9%B9%BF%E6%8C%81%E9%9B%85%E6%BE%84%E8%A8%93%E8%A8%82%29` | `resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集 (鹿持雅澄訓訂)-Wikisource.pdf` |
| `万葉集 (奈良女子高等師範学校国語研究室編)` | `https://ws-export.wmcloud.org/?lang=ja&format=pdf&page=%E4%B8%87%E8%91%89%E9%9B%86+%28%E5%A5%88%E8%89%AF%E5%A5%B3%E5%AD%90%E9%AB%98%E7%AD%89%E5%B8%AB%E7%AF%84%E5%AD%A6%E6%A0%A1%E5%9B%BD%E8%AA%9E%E7%A0%94%E7%A9%B6%E5%AE%A4%E7%B7%A8%29` | `resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集 (奈良女子高等師範学校国語研究室編)-Wikisource.pdf` |
| `古今和歌集` | `https://ws-export.wmcloud.org/?lang=ja&format=pdf&page=%E5%8F%A4%E4%BB%8A%E5%92%8C%E6%AD%8C%E9%9B%86` | `resources/curated-books/japanese-poetry/kokin-wakashu/ja-wikisource-export/古今和歌集-Wikisource.pdf` |

## Copy Instructions

If the other tool downloads files into `/home/lachlan/Downloads`, copy them into
the targets above. Do not move or delete the originals.

Example:

```bash
cp -n "/home/lachlan/Downloads/万葉集-Wikisource.pdf" \
  "resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集-Wikisource.pdf"
```

Use `cp -n` first to avoid overwriting an existing valid PDF. If replacing a
known bad file, inspect it first and then overwrite intentionally.

## Validation

After copying, validate each file:

```bash
python3 - <<'PY'
from pathlib import Path
targets = [
    Path("resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集-Wikisource.pdf"),
    Path("resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集 (鹿持雅澄訓訂)-Wikisource.pdf"),
    Path("resources/curated-books/japanese-poetry/manyoshu/ja-wikisource-export/万葉集 (奈良女子高等師範学校国語研究室編)-Wikisource.pdf"),
    Path("resources/curated-books/japanese-poetry/kokin-wakashu/ja-wikisource-export/古今和歌集-Wikisource.pdf"),
]
for path in targets:
    data = path.read_bytes()[:4] if path.exists() else b""
    print(path, path.exists(), path.stat().st_size if path.exists() else 0, data)
    assert path.exists() and data == b"%PDF"
PY
```

If validation passes, update the matching `manifest.json` files under
`ja-wikisource-export/` so `pdf_status` says `ok, <bytes> bytes` instead of
`HTTP 503: Service Unavailable`.

## Context

The previous automated export run succeeded for EPUB but Wikisource PDF export
returned HTTP 503 for all four PDF attempts. Related audit document:
`references/MANYOSHU_KOKIN_WAKA_LIBGEN_WIKI_SYNC_2026-07-01.md`.
