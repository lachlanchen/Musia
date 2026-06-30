# 云海之恋 Production Note

Date: 2026-06-30

## Request

Create a beautiful, spacious, deep-love song from the Chinese lyric idea
`云海之恋`: sky, sea, clouds, distance, flowing years, and a thousand-year love.
Generate Chinese first, then use Musia master-companion to create English and
Japanese female versions.

## Workflow Used

1. Polished the Chinese lyric into a cinematic ballad form.
2. Generated an ACE-Step Chinese master candidate.
3. Ran Musia analysis to extract stems, beats, chords, and ASR lyrics.
4. Ran `musia master-companion` from the Chinese master toward `en` and `ja`.
5. Rewrote EN/JP companion lyrics with quality-first constraints:
   short lines, rhyme/mora flow, no crammed phrases, and musical space.
6. Generated several ACE-Step companion candidates.
7. Reviewed every selected candidate with Musia song review and pipeline
   analysis.

## Important Quality Decision

Strict same-melody EN/JP generation was not used as the final route. The
Chinese master analysis produced only a sparse phrase map, and the available
same-score vocal route would likely reduce quality. This run follows the
Musia quality rule: preserve the feeling and production quality first, then
use same-melody control only when it does not harm pronunciation, phrasing, or
musicality.

## Best Current Candidate Set

Chinese master:

```text
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/yun-hai-zhi-lian-20260630/selected/yun-hai-zhi-lian-zh-master-v3.mp3
```

English companion candidates:

```text
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/yun-hai-zhi-lian-20260630/selected/yun-hai-zhi-lian-en-companion-v2-experimental.mp3
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/yun-hai-zhi-lian-20260630/selected/yun-hai-zhi-lian-en-companion-v4-alt-experimental.mp3
```

Japanese companion:

```text
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/yun-hai-zhi-lian-20260630/selected/yun-hai-zhi-lian-ja-companion-v2-experimental.mp3
```

Project summary:

```text
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/yun-hai-zhi-lian-20260630/SELECTED_VERSION.md
```

## Evidence

Chinese v3 review:

```text
/home/lachlan/ProjectsLFS/Musia/data/creative_projects/yun-hai-zhi-lian-20260630/reviews/20260630-171616/SONG_REVIEW.md
```

Chinese v3 quality gate: `pass`.

Chinese v3 pipeline transcript:

```text
我想你 相逢 落在你身边 云海之间 爱是一切 穿过流途该从 你想在眼前 千年以后
```

Chinese v3 melody/F0 guide:

```text
/home/lachlan/ProjectsLFS/Musia/data/runs/yun-hai-zhi-lian-20260630-20260630-171616-analysis/analysis/melody_f0.csv
/home/lachlan/ProjectsLFS/Musia/data/runs/yun-hai-zhi-lian-20260630-20260630-171616-analysis/analysis/melody_f0_summary.json
```

Japanese v2 pipeline transcript:

```text
風に乗せて 心 君のそばへ 届け 君へ続く
```

English remains experimental. The best recovered English transcript from the
candidate set is partial and not publish-grade.

## Publication Status

This song was not added to `fun.lazying.art` yet. Before public website or
music-platform publishing:

1. Listen to the selected Chinese master and choose whether the vocal/emotion is
   good enough.
2. Regenerate or manually correct EN/JP with a stronger controlled vocal route.
3. Create per-vocal website lyric JSON from each selected audio's own ASR and
   listening pass.
4. Add pinyin/furigana, cover art, manifest, and recordings only after the
   audio/lyric truth check passes.

## Current Best Next Step

Use the Chinese v3 master as the creative reference. For true EN/JP localized
versions, prefer a controlled SVS route such as SoulX/YingMusic with extracted
melody/F0, or regenerate independent ACE-Step versions and only publish the
ones whose active-language lyrics can be corrected confidently.
