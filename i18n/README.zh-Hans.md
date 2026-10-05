[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musia

*AI 歌曲本地化：从歌曲中提取人声、分轨、歌词、节拍与和弦，并为可演唱的多语言重唱打基础。*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](../environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](../references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musia 是一个本地优先的 AI 音乐本地化研究原型。当前 MVP 接收一首输入歌曲，分离出 Demucs 的四个分轨 `bass`、`drums`、`vocals`、`other`，生成 `instrumental` 伴奏混音，把人声别名为 `human_sound`，并输出歌词转写、节拍和类似 Chordify 的和弦片段。

## Musia 应用

[![在 Google Play 下载 Musia](https://img.shields.io/badge/Google_Play-Download-00875F?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/apps/details?id=art.lazying.musia) · [打开网页版](https://musia.lazying.art)

Android 0.1.1 已上架，售价 **US$2.99**。通过聆听、节奏练习、吉他和弦指法图、保留音高的变速播放和乐句循环，逐步理解音乐。无需账号或订阅。

[![Google Play 公开商店页面，截图于 2026 年 10 月 5 日。各地区价格可能不同。](../store/assets/readme/google-play.png)](https://play.google.com/store/apps/details?id=art.lazying.musia)

*Google Play 公开商店页面，截图于 2026 年 10 月 5 日。各地区价格可能不同。*

### Android 应用实景

| 歌曲库 | 引导练习 |
| :---: | :---: |
| <img src="../store/assets/readme/android-library.png" width="260" alt="歌曲库"> | <img src="../store/assets/readme/android-practice.png" width="260" alt="引导练习"> |

已发布 Android 应用的真实截图，非界面模型图。

<details>
<summary>原生 macOS 预览（审核中）</summary>

原生 iOS 和 macOS 应用已提交审核，截至 2026 年 10 月 5 日尚未正式公开发布。

![原生 Mac 练习界面，包含歌词、播放速度和吉他指法](../store/assets/macos/03-song.png)

</details>

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 输出内容

```text
input song
-> source/input.wav
-> stems/bass.wav
-> stems/drums.wav
-> stems/vocals.wav
-> stems/other.wav
-> stems/instrumental.wav
-> stems/human_sound.wav
-> analysis/lyrics.json + lyrics.txt
-> analysis/beats.json + beats.csv
-> analysis/chords.json + chords.csv
-> manifest.json + REPORT.md
```

`instrumental.wav` 由 `bass + drums + other` 混合而成。`human_sound.wav` 是隔离后的人声 `vocals.wav`。

## 当前内容

| Path | Purpose |
| --- | --- |
| [`musia/`](../musia/) | 本地 Python 分析工具包。 |
| [`scripts/bootstrap_musia.sh`](../scripts/bootstrap_musia.sh) | 创建 conda 环境并安装本地栈。 |
| [`scripts/download_open_songs.py`](../scripts/download_open_songs.py) | 下载自由/开放测试歌曲。 |
| [`scripts/run_pipeline.py`](../scripts/run_pipeline.py) | 运行分轨、转写、节拍、和弦与报告生成。 |
| [`scripts/install_research_repos.sh`](../scripts/install_research_repos.sh) | 将可选研究仓库浅克隆到 `third_party/`。 |
| [`scripts/musia_lyricfit_openai.py`](../scripts/musia_lyricfit_openai.py) | 可选的 OpenAI 歌词适配辅助脚本。 |
| [`references/`](../references/) | 架构、深度研究和本地安装记录。 |
| [`TODO.md`](../TODO.md) | 构建清单与后续工程任务。 |

## 快速开始

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

结果会写入：

```text
data/runs/<run-name>/
```

生成音频、下载歌曲、模型权重和第三方克隆仓库不会提交到 git。

## 本地验证

在配有 NVIDIA RTX 4090 D 的机器上，使用 Wikimedia Commons 开放录音完成了本地烟雾测试：

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

记录结果：

- 四个分轨：`bass`、`drums`、`vocals`、`other`
- 额外音频：`instrumental`、`human_sound`
- 速度估计：`129.20 BPM`
- 节拍数：`257`
- 和弦片段：`132`
- 歌词状态：`ok`

见 [`references/local-setup-and-test-report.md`](../references/local-setup-and-test-report.md)。

## 架构方向

Musia 不只是翻译加 TTS。目标完整流程是：

```text
song upload
-> rights / ownership check
-> vocal + instrumental separation
-> lyrics transcription
-> word / phoneme timing
-> melody / pitch extraction
-> singable lyric adaptation
-> AI singing synthesis
-> optional voice/timbre conversion
-> mixing + mastering
-> music-player interface
```

当前仓库实现的是第一层本地分析。YingMusic-Singer-Plus、SoulX-Singer 等演唱合成模型会作为研究集成继续推进，因为它们需要更大的权重、许可检查和独立 GPU worker 封装。

## 引用

如果在研究中使用 Musia，请引用本仓库。GitHub 会读取 [`CITATION.cff`](../CITATION.cff)，并在仓库页面显示 **Cite this repository**。

```bibtex
@software{chen_musia_2026,
  author = {Chen, Lachlan},
  title = {Musia: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musia}
}
```

## 状态

Musia 仍是早期研究软件。本地流水线可以用于测试和生成分析产物，但和弦检测器仍是轻量基线，真正可演唱的重唱层尚未达到生产状态。请使用自有歌曲、公版歌曲、已授权歌曲或创作者上传的材料。
