[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musia

*AI-локализация песен: извлечение человеческого голоса, stems, текста, битов и аккордов из песни и подготовка пути к исполнимому многоязычному перепеву.*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](../environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](../references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musia — локальный исследовательский прототип для AI-локализации музыки. Текущий MVP принимает песню, разделяет ее на четыре Demucs-stems `bass`, `drums`, `vocals` и `other`, создает микс `instrumental`, сохраняет вокал как `human_sound`, транскрибирует текст, оценивает биты и создает сегменты аккордов в стиле Chordify.

## Приложение Musia

[![Скачать Musia в Google Play](https://img.shields.io/badge/Google_Play-Download-00875F?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/apps/details?id=art.lazying.musia) · [Открыть веб-приложение](https://musia.lazying.art)

Android 0.1.1 доступен за **2,99 доллара США**. Учитесь с помощью прослушивания, упражнений на ритм, схем гитарных аккордов, изменения скорости без изменения высоты тона и повторения фраз. Учётная запись и подписка не нужны.

[![Публичная страница Google Play, снимок от 5 октября 2026 года. Цена может различаться по регионам.](../store/assets/readme/google-play.png)](https://play.google.com/store/apps/details?id=art.lazying.musia)

*Публичная страница Google Play, снимок от 5 октября 2026 года. Цена может различаться по регионам.*

### Внутри Android-приложения

| Библиотека песен | Практика с подсказками |
| :---: | :---: |
| <img src="../store/assets/readme/android-library.png" width="260" alt="Библиотека песен"> | <img src="../store/assets/readme/android-practice.png" width="260" alt="Практика с подсказками"> |

Настоящие скриншоты опубликованного Android-приложения, не макеты.

<details>
<summary>Нативная версия macOS (на рассмотрении)</summary>

Нативные приложения для iOS и macOS отправлены на проверку и ещё не опубликованы по состоянию на 5 октября 2026 года.

![Нативный экран практики Mac с текстом песни, скоростью и аппликатурами гитары](../store/assets/macos/03-song.png)

</details>

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Что Создается

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

`instrumental.wav` смешивается из `bass + drums + other`. `human_sound.wav` — это изолированный вокальный stem `vocals.wav`.

## Текущее Содержимое

| Path | Purpose |
| --- | --- |
| [`musia/`](../musia/) | Локальный Python-набор для анализа. |
| [`scripts/bootstrap_musia.sh`](../scripts/bootstrap_musia.sh) | Создает conda-окружение и устанавливает локальный стек. |
| [`scripts/download_open_songs.py`](../scripts/download_open_songs.py) | Загружает свободные/открытые тестовые песни. |
| [`scripts/run_pipeline.py`](../scripts/run_pipeline.py) | Запускает разделение, транскрипцию, биты, аккорды и отчет. |
| [`scripts/install_research_repos.sh`](../scripts/install_research_repos.sh) | Shallow-clone опциональных исследовательских репозиториев в `third_party/`. |
| [`scripts/musia_lyricfit_openai.py`](../scripts/musia_lyricfit_openai.py) | Опциональный помощник адаптации текста с OpenAI. |
| [`references/`](../references/) | Архитектура, глубокое исследование и локальные заметки установки. |
| [`TODO.md`](../TODO.md) | Список задач и следующие инженерные шаги. |

## Быстрый Старт

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

Результаты записываются в:

```text
data/runs/<run-name>/
```

Сгенерированное аудио, загруженные песни, веса моделей и сторонние клоны игнорируются git.

## Локальная Проверка

Локальный smoke test на открытой записи Wikimedia Commons успешно прошел на машине с NVIDIA RTX 4090 D:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

Зафиксированный результат:

- Четыре stems: `bass`, `drums`, `vocals`, `other`
- Дополнительное аудио: `instrumental`, `human_sound`
- Оценка темпа: `129.20 BPM`
- Биты: `257`
- Сегменты аккордов: `132`
- Статус текста: `ok`

См. [`references/local-setup-and-test-report.md`](../references/local-setup-and-test-report.md).

## Архитектурное Направление

Musia — это не просто перевод плюс TTS. Целевой полный поток:

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

Этот репозиторий реализует первый локальный аналитический слой. Синтез пения через YingMusic-Singer-Plus, SoulX-Singer и родственные модели остается исследовательской интеграцией, потому что требует больших весов, проверки лицензий и отдельных GPU workers.

## Цитирование

Если вы используете Musia в исследовании, цитируйте этот репозиторий. GitHub читает [`CITATION.cff`](../CITATION.cff) и показывает **Cite this repository** на странице репозитория.

```bibtex
@software{chen_musia_2026,
  author = {Chen, Lachlan},
  title = {Musia: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musia}
}
```

## Статус

Musia — раннее исследовательское ПО. Локальный pipeline работает для тестов и артефактов, но детектор аккордов остается легкой базовой версией, а слой исполнимого re-singing еще не готов к production. Используйте собственные песни, public-domain, лицензированные песни или материалы, загруженные авторами.
