# 《洛神赋 · 原文选段》试听制作记录

## 范围

本轮把曹植《洛神赋》中已经核定的原文选段谱成一首全新歌曲。中文演唱层只使用
原文；允许分段、留白和重复，但没有加入现代汉语改写。这里的“原文选段”不是把
《洛神赋》全文全部塞入一首歌。

作品只使用公共领域文本，不复制乱徵《洛神》或其他现代录音的旋律、编曲、音色、
演唱方式与母带。

## 生成

- ACE-Step 1.5 commit: `6d467e4b5081`
- 主模型: `acestep-v15-xl-turbo`
- 对照模型: `acestep-v15-xl-sft`
- 候选总数: `10`
- 时长: `134-136` 秒
- 速度: `72 BPM`
- 调性: `D minor`
- 拍号: `4/4`
- 人声: 原创普通话女声，不模仿真人歌手

候选分成三路：

1. 四个 XL Turbo 原字候选；
2. 四个 XL Turbo 私有同音控制候选；
3. 两个 50-step XL SFT 对照候选。

入模同音控制只为处理 `秾、凫、靥、髣髴、飘飖、珥、琚、绡、裾、铅`
等字。网页与公开歌词始终恢复为核定原文。

## 终选

终选为原字路 seed `729403`：

```text
data/creative_projects/luoshenfu-original-excerpt-preview-20260729/
  selected/luoshenfu-original-excerpt-seed729403-master.wav
  selected/luoshenfu-original-excerpt-seed729403.mp3
```

健康检查无削波、无非有限采样、结尾自然。APEX 分数：

| 指标 | 分数 |
| --- | ---: |
| Coherence | 2.915 |
| Musicality | 2.800 |
| Memorability | 2.839 |
| Clarity | 2.666 |
| Naturalness | 2.571 |

MOSS-Music 独立分析认为它是结构完整、旋律流畅、女声清晰、气息稳定的慢板
新古典抒情歌；钢琴与弦乐层次自然，高潮有抬升，未发现明显噪声、爆音或突兀
剪切。

XL SFT 虽然自动审美分稍高，但分离人声出现无关/不可懂内容，且结尾仍处于高
响度，因此淘汰。不能因为步数更多或评分更高就代替歌词与信号事实。

## 歌词校正

本轮使用：

- 原文与人工核定发音；
- 整曲和 Demucs 分离人声的 faster-whisper large-v3；
- normal VAD 与 no-VAD 两套边界；
- MOSS-Music 盲转写；
- 逐段字数、顺序与重复结构复核。

最终 40 个演唱行全部得到时间区间。对于 `偏若/翩若`、`荣耀/荣曜`、
`春送/春松` 这类同音或近音识别差异，因字数、音节与上下文都支持原文，网页
保留曹植原句。ASR 用来发现真实漏唱、重复和结构变化，不用来把优美且音近的
古文降级为识别器猜词。

## 网站

媒体 ID：

```text
luoshenfu-original-excerpt-preview
```

直接试听：

```text
https://fun.lazying.art/?preview=1#luoshenfu-original-excerpt-preview
```

它使用 `visibility: unlisted`、`releaseStage: preview` 和
`category: preview`，不会进入默认歌单、搜索预览或自动播放队列。

公开音频由 `MusiaSongs` 托管；Fun 条目包含中文原文、拼音、英文/日文意义层、
逐词高亮、节拍、和弦和本曲专属 16:9 封面。

可重复构建命令：

```bash
PYTHONNOUSERSITE=1 conda run -n musia python \
  scripts/prepare_luoshenfu_original_preview_fun_item.py

node bin/musia.js fun-audit \
  --media-id luoshenfu-original-excerpt-preview \
  --strict
```
