# 《洛神赋 · 原文选段》制作与发布记录

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

## 首版选择

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

正式页面：

```text
https://fun.lazying.art/#luoshenfu-original-excerpt-preview
```

2026-07-30 经用户确认，原字首版和读音优化 V2 一起从 Unlisted Preview
提升为正式发布。条目进入正常曲库、搜索和播放队列；V2 是默认音频，原字首版
作为同一作品内的可切换版本保留。

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

## 读音优化第二版

2026-07-30 在不覆盖首版的前提下，把同种子 `729403` 的读音优化版本加入同一
作品；两版先完成 A/B 试听，随后一起正式发布：

- `Source A / 原字首版`：首版原字输入；
- `Pronunciation V2 / 读音优化 V2`：只对首版已证明唱错的难字使用私有
  同音易字控制。

模型仍为 `acestep-v15-xl-turbo`，没有切换到朗诵、SoulX 或低质量迁移路线。
V2 的公开歌词恢复曹植原字；模型内部使用的 `仿佛、飘摇、荣耀、飞浮` 等
控制字不冒充原文。V2 独立保存 41 行时间轴，其中包括音频结尾实际多唱的一次
`飘飖兮`，不复用首版 timing。

V2 交叉证据包括整曲与 Demucs 人声轨的 faster-whisper large-v3
normal/no-VAD，以及 MOSS-Music 独立盲转写。两条路线均恢复了
`fang-fu-xi`，MOSS 两次完整识别为：

```text
仿佛兮若轻云之蔽月
飘摇兮若流风之回雪
```

公开音频：

```text
https://lazyingart.github.io/MusiaSongs/audio/luoshenfu-original-excerpt-pronunciation-v2-zh-Hans-ace-xl-turbo-seed729403-20260730.mp3
```

可重复构建仍使用同一兼容脚本；它现在会同时生成两个正式音频版本、两套歌词
与两套音乐分析：

```bash
PYTHONNOUSERSITE=1 conda run -n musia python \
  scripts/prepare_luoshenfu_original_preview_fun_item.py
```
