[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musia

*AI 歌曲在地化：從歌曲中提取人聲、分軌、歌詞、節拍與和弦，並為可演唱的多語言重唱打基礎。*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](../environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](../references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musia 是本地優先的 AI 音樂在地化研究原型。目前 MVP 接收一首輸入歌曲，分離出 Demucs 的四個分軌 `bass`、`drums`、`vocals`、`other`，生成 `instrumental` 伴奏混音，把人聲別名為 `human_sound`，並輸出歌詞轉寫、節拍和類似 Chordify 的和弦片段。

## Musia 應用程式

[![在 Google Play 下載 Musia](https://img.shields.io/badge/Google_Play-Download-00875F?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/apps/details?id=art.lazying.musia) · [開啟網頁版](https://musia.lazying.art)

Android 0.1.1 已上架，售價 **US$2.99**。透過聆聽、節奏練習、吉他和弦指法圖、保留音高的變速播放與樂句循環，逐步理解音樂。無需帳號或訂閱。

[![Google Play 公開商店頁面，截圖於 2026 年 10 月 5 日。各地區價格可能不同。](../store/assets/readme/google-play.png)](https://play.google.com/store/apps/details?id=art.lazying.musia)

*Google Play 公開商店頁面，截圖於 2026 年 10 月 5 日。各地區價格可能不同。*

### Android 應用實景

| 歌曲庫 | 引導練習 |
| :---: | :---: |
| <img src="../store/assets/readme/android-library.png" width="260" alt="歌曲庫"> | <img src="../store/assets/readme/android-practice.png" width="260" alt="引導練習"> |

已發布 Android 應用程式的真實截圖，非介面模型圖。

<details>
<summary>原生 macOS 預覽（審核中）</summary>

原生 iOS 和 macOS 應用程式已提交審核，截至 2026 年 10 月 5 日尚未正式公開發布。

![原生 Mac 練習介面，包含歌詞、播放速度與吉他指法](../store/assets/macos/03-song.png)

</details>

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 輸出內容

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

`instrumental.wav` 由 `bass + drums + other` 混合而成。`human_sound.wav` 是隔離後的人聲 `vocals.wav`。

## 目前內容

| Path | Purpose |
| --- | --- |
| [`musia/`](../musia/) | 本地 Python 分析工具包。 |
| [`scripts/bootstrap_musia.sh`](../scripts/bootstrap_musia.sh) | 建立 conda 環境並安裝本地堆疊。 |
| [`scripts/download_open_songs.py`](../scripts/download_open_songs.py) | 下載自由/開放測試歌曲。 |
| [`scripts/run_pipeline.py`](../scripts/run_pipeline.py) | 執行分軌、轉寫、節拍、和弦與報告生成。 |
| [`scripts/install_research_repos.sh`](../scripts/install_research_repos.sh) | 將可選研究倉庫淺克隆到 `third_party/`。 |
| [`scripts/musia_lyricfit_openai.py`](../scripts/musia_lyricfit_openai.py) | 可選的 OpenAI 歌詞適配輔助腳本。 |
| [`references/`](../references/) | 架構、深度研究和本地安裝記錄。 |
| [`TODO.md`](../TODO.md) | 構建清單與後續工程任務。 |

## 快速開始

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

結果會寫入：

```text
data/runs/<run-name>/
```

生成音訊、下載歌曲、模型權重和第三方克隆倉庫不會提交到 git。

## 本地驗證

在配有 NVIDIA RTX 4090 D 的機器上，使用 Wikimedia Commons 開放錄音完成了本地煙霧測試：

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

記錄結果：

- 四個分軌：`bass`、`drums`、`vocals`、`other`
- 額外音訊：`instrumental`、`human_sound`
- 速度估計：`129.20 BPM`
- 節拍數：`257`
- 和弦片段：`132`
- 歌詞狀態：`ok`

見 [`references/local-setup-and-test-report.md`](../references/local-setup-and-test-report.md)。

## 架構方向

Musia 不只是翻譯加 TTS。目標完整流程是：

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

目前倉庫實作的是第一層本地分析。YingMusic-Singer-Plus、SoulX-Singer 等演唱合成模型會作為研究整合繼續推進，因為它們需要更大的權重、授權檢查和獨立 GPU worker 封裝。

## 引用

如果在研究中使用 Musia，請引用本倉庫。GitHub 會讀取 [`CITATION.cff`](../CITATION.cff)，並在倉庫頁面顯示 **Cite this repository**。

```bibtex
@software{chen_musia_2026,
  author = {Chen, Lachlan},
  title = {Musia: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musia}
}
```

## 狀態

Musia 仍是早期研究軟體。本地流水線可以用於測試和生成分析產物，但和弦偵測器仍是輕量基線，真正可演唱的重唱層尚未達到生產狀態。請使用自有歌曲、公版歌曲、已授權歌曲或創作者上傳的材料。
