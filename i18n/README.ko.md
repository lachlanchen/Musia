[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musia

*AI 노래 로컬라이제이션: 곡에서 사람 목소리, 스템, 가사, 비트, 코드를 추출하고, 부를 수 있는 다국어 재가창을 준비합니다.*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](../environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](../references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musia는 로컬 우선 AI 음악 로컬라이제이션 연구 프로토타입입니다. 현재 MVP는 입력 곡을 Demucs의 네 스템 `bass`, `drums`, `vocals`, `other`로 분리하고, `instrumental` 믹스를 만들며, 보컬을 `human_sound`로 별칭 저장하고, 가사 전사, 비트 추정, Chordify 스타일 코드 구간을 생성합니다.

## Musia 앱

[![Google Play에서 Musia 받기](https://img.shields.io/badge/Google_Play-Download-00875F?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/apps/details?id=art.lazying.musia) · [웹 앱 열기](https://musia.lazying.art)

Android 0.1.1을 **US$2.99**에 이용할 수 있습니다. 듣기, 리듬 연습, 기타 코드 다이어그램, 음정을 유지하는 속도 조절과 구간 반복으로 배워 보세요. 계정이나 구독은 필요하지 않습니다.

[![2026년 10월 5일에 촬영한 Google Play 공개 페이지입니다. 가격은 지역에 따라 다를 수 있습니다.](../store/assets/readme/google-play.png)](https://play.google.com/store/apps/details?id=art.lazying.musia)

*2026년 10월 5일에 촬영한 Google Play 공개 페이지입니다. 가격은 지역에 따라 다를 수 있습니다.*

### Android 앱 화면

| 노래 라이브러리 | 단계별 연습 |
| :---: | :---: |
| <img src="../store/assets/readme/android-library.png" width="260" alt="노래 라이브러리"> | <img src="../store/assets/readme/android-practice.png" width="260" alt="단계별 연습"> |

출시된 Android 앱의 실제 스크린샷이며 목업이 아닙니다.

<details>
<summary>네이티브 macOS 미리 보기 (심사 중)</summary>

네이티브 iOS 및 macOS 앱은 심사에 제출되었으며, 2026년 10월 5일 기준 아직 공개 출시되지 않았습니다.

![가사, 재생 속도 및 기타 운지법이 있는 네이티브 Mac 연습 화면](../store/assets/macos/03-song.png)

</details>

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## 출력

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

`instrumental.wav`는 `bass + drums + other`를 섞어 만듭니다. `human_sound.wav`는 분리된 보컬 스템 `vocals.wav`입니다.

## 현재 구성

| Path | Purpose |
| --- | --- |
| [`musia/`](../musia/) | 로컬 Python 분석 툴킷. |
| [`scripts/bootstrap_musia.sh`](../scripts/bootstrap_musia.sh) | conda 환경을 만들고 로컬 스택을 설치합니다. |
| [`scripts/download_open_songs.py`](../scripts/download_open_songs.py) | 자유/오픈 테스트 곡을 다운로드합니다. |
| [`scripts/run_pipeline.py`](../scripts/run_pipeline.py) | 분리, 전사, 비트, 코드, 리포트 생성을 실행합니다. |
| [`scripts/install_research_repos.sh`](../scripts/install_research_repos.sh) | 선택 연구 저장소를 `third_party/`에 shallow clone 합니다. |
| [`scripts/musia_lyricfit_openai.py`](../scripts/musia_lyricfit_openai.py) | 선택적 OpenAI 가사 적응 도우미. |
| [`references/`](../references/) | 아키텍처, 심층 조사, 로컬 설치 기록. |
| [`TODO.md`](../TODO.md) | 빌드 체크리스트와 다음 작업. |

## 빠른 시작

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

결과는 다음 위치에 저장됩니다:

```text
data/runs/<run-name>/
```

생성 오디오, 다운로드한 곡, 모델 가중치, 타사 클론은 git에서 제외됩니다.

## 로컬 검증

NVIDIA RTX 4090 D 머신에서 Wikimedia Commons 오픈 녹음으로 로컬 smoke test를 통과했습니다:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

기록된 결과:

- 네 스템: `bass`, `drums`, `vocals`, `other`
- 추가 오디오: `instrumental`, `human_sound`
- 템포 추정: `129.20 BPM`
- 비트 수: `257`
- 코드 구간: `132`
- 가사 상태: `ok`

자세한 내용은 [`references/local-setup-and-test-report.md`](../references/local-setup-and-test-report.md)를 보세요.

## 아키텍처 방향

Musia는 단순한 번역 + TTS가 아닙니다. 목표 전체 파이프라인은 다음과 같습니다:

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

이 저장소는 첫 번째 로컬 분석 계층을 구현합니다. YingMusic-Singer-Plus, SoulX-Singer 및 관련 모델을 통한 가창 합성은 큰 가중치, 라이선스 확인, 별도 GPU worker 패키징이 필요하므로 연구 통합 단계로 남겨 둡니다.

## 인용

연구에서 Musia를 사용한다면 이 저장소를 인용해 주세요. GitHub는 [`CITATION.cff`](../CITATION.cff)를 읽고 저장소 페이지에 **Cite this repository** 패널을 표시합니다.

```bibtex
@software{chen_musia_2026,
  author = {Chen, Lachlan},
  title = {Musia: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musia}
}
```

## 상태

Musia는 초기 연구 소프트웨어입니다. 로컬 파이프라인은 테스트와 산출물 생성에 사용할 수 있지만, 코드 감지기는 가벼운 기준선이며 부를 수 있는 재가창 계층은 아직 프로덕션 준비가 되지 않았습니다. 본인 소유, 퍼블릭 도메인, 라이선스가 있는 곡 또는 창작자가 업로드한 자료를 사용하세요.
