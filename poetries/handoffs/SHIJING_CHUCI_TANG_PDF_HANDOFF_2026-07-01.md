# Shijing, Chuci, And Tang Poetry Wikisource PDF Handoff - 2026-07-01

Use this handoff when another browser/download tool can successfully fetch
Wikisource PDF exports for `詩經`, `楚辭`, and `唐詩三百首`. EPUB exports and
raw/HTML Wikisource folders already exist; this note is only for copying
Wikisource PDF files into the same archive folders.

## Target Files

| Work | Language | Wikisource PDF export URL | Copy PDF to |
| --- | --- | --- | --- |
| `詩經` | Chinese | `https://ws-export.wmcloud.org/?lang=zh&format=pdf&page=%E8%A9%A9%E7%B6%93` | `resources/curated-books/chinese-classics/shijing/zh-wikisource-export/詩經-Wikisource.pdf` |
| `Classic of Poetry` | English | `https://ws-export.wmcloud.org/?lang=en&format=pdf&page=Classic+of+Poetry` | `resources/curated-books/chinese-classics/shijing/en-wikisource-export/Classic-of-Poetry-Wikisource.pdf` |
| `詩経` | Japanese | `https://ws-export.wmcloud.org/?lang=ja&format=pdf&page=%E8%A9%A9%E7%B5%8C` | `resources/curated-books/chinese-classics/shijing/ja-wikisource-export/詩経-Wikisource.pdf` |
| `楚辭` | Chinese | `https://ws-export.wmcloud.org/?lang=zh&format=pdf&page=%E6%A5%9A%E8%BE%AD` | `resources/curated-books/chinese-classics/chuci/zh-wikisource-export/楚辭-Wikisource.pdf` |
| `唐詩三百首` | Chinese | `https://ws-export.wmcloud.org/?lang=zh&format=pdf&page=%E5%94%90%E8%A9%A9%E4%B8%89%E7%99%BE%E9%A6%96` | `resources/curated-books/chinese-classics/tang-poetry/zh-wikisource-export/唐詩三百首-Wikisource.pdf` |
| `The Jade Mountain` | English | `https://ws-export.wmcloud.org/?lang=en&format=pdf&page=The+Jade+Mountain` | `resources/curated-books/chinese-classics/tang-poetry/en-wikisource-export/The-Jade-Mountain-Wikisource.pdf` |

## Copy Instructions

If the other tool downloads files into `/home/lachlan/Downloads`, copy them into
the target paths above. Do not move or delete the originals.

Example:

```bash
cp -n "/home/lachlan/Downloads/詩經-Wikisource.pdf" \
  "resources/curated-books/chinese-classics/shijing/zh-wikisource-export/詩經-Wikisource.pdf"
```

Use `cp -n` first to avoid overwriting a valid PDF. If a bad partial PDF already
exists, inspect it and overwrite intentionally.

## Validation

After copying, validate every file:

```bash
python3 - <<'PY'
from pathlib import Path
targets = [
    Path("resources/curated-books/chinese-classics/shijing/zh-wikisource-export/詩經-Wikisource.pdf"),
    Path("resources/curated-books/chinese-classics/shijing/en-wikisource-export/Classic-of-Poetry-Wikisource.pdf"),
    Path("resources/curated-books/chinese-classics/shijing/ja-wikisource-export/詩経-Wikisource.pdf"),
    Path("resources/curated-books/chinese-classics/chuci/zh-wikisource-export/楚辭-Wikisource.pdf"),
    Path("resources/curated-books/chinese-classics/tang-poetry/zh-wikisource-export/唐詩三百首-Wikisource.pdf"),
    Path("resources/curated-books/chinese-classics/tang-poetry/en-wikisource-export/The-Jade-Mountain-Wikisource.pdf"),
]
for path in targets:
    data = path.read_bytes()[:4] if path.exists() else b""
    print(path, path.exists(), path.stat().st_size if path.exists() else 0, data)
    assert path.exists() and data == b"%PDF"
PY
```

If validation passes, update
`references/SHIJING_CHUCI_TANG_WIKI_SYNC_2026-06-30.md` to say which
Wikisource PDFs are now present and where they are stored.

## Existing Non-Wikisource PDFs

Manual PDF copies for some editions already exist under language folders such
as `shijing/zh/`, `chuci/en/`, and `tang-poetry/zh/`. Do not overwrite those.
This handoff is only for Wikisource-export PDFs under `*-wikisource-export/`.

## Context

The previous automated export run succeeded for EPUB but Wikisource PDF export
returned HTTP 503 for all six PDF attempts. Related audit documents:

- `references/SHIJING_CHUCI_TANG_WIKI_SYNC_2026-06-30.md`
- `references/SHIJING_CHUCI_TANG_MANUAL_PDF_SYNC_2026-06-30.md`
