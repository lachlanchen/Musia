[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musia

*Bản địa hóa bài hát bằng AI: trích xuất giọng người, stem, lời, nhịp và hợp âm từ một bài hát, rồi chuẩn bị đường đi tới hát lại đa ngôn ngữ có thể hát được.*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](../environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](../references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musia là một nguyên mẫu nghiên cứu local-first cho bản địa hóa âm nhạc bằng AI. MVP hiện tại nhận một bài hát đầu vào, tách thành bốn stem Demucs `bass`, `drums`, `vocals`, `other`, tạo bản trộn `instrumental`, đặt bí danh giọng hát là `human_sound`, chép lời, ước lượng nhịp và tạo các đoạn hợp âm kiểu Chordify.

## Ứng Dụng Musia

[![Tải Musia trên Google Play](https://img.shields.io/badge/Google_Play-Download-00875F?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/apps/details?id=art.lazying.musia) · [Mở ứng dụng web](https://musia.lazying.art)

Android 0.1.1 đã có mặt với giá **2,99 USD**. Học qua nghe nhạc, luyện nhịp, sơ đồ hợp âm guitar, điều chỉnh tốc độ mà giữ nguyên cao độ và lặp từng câu nhạc. Không cần tài khoản hay thuê bao.

[![Trang Google Play công khai, chụp ngày 5 tháng 10 năm 2026. Giá có thể khác theo khu vực.](../store/assets/readme/google-play.png)](https://play.google.com/store/apps/details?id=art.lazying.musia)

*Trang Google Play công khai, chụp ngày 5 tháng 10 năm 2026. Giá có thể khác theo khu vực.*

### Bên Trong Ứng Dụng Android

| Thư viện bài hát | Luyện tập có hướng dẫn |
| :---: | :---: |
| <img src="../store/assets/readme/android-library.png" width="260" alt="Thư viện bài hát"> | <img src="../store/assets/readme/android-practice.png" width="260" alt="Luyện tập có hướng dẫn"> |

Ảnh chụp thật của ứng dụng Android đã phát hành, không phải bản mô phỏng.

<details>
<summary>Xem trước ứng dụng macOS gốc (đang xét duyệt)</summary>

Ứng dụng iOS và macOS gốc đã được gửi xét duyệt, chưa phát hành công khai tính đến ngày 5 tháng 10 năm 2026.

![Không gian luyện tập Mac gốc với lời bài hát, tốc độ và thế bấm guitar](../store/assets/macos/03-song.png)

</details>

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Đầu Ra

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

`instrumental.wav` được trộn từ `bass + drums + other`. `human_sound.wav` là stem giọng hát đã tách `vocals.wav`.

## Nội Dung Hiện Có

| Path | Purpose |
| --- | --- |
| [`musia/`](../musia/) | Bộ công cụ phân tích Python chạy cục bộ. |
| [`scripts/bootstrap_musia.sh`](../scripts/bootstrap_musia.sh) | Tạo môi trường conda và cài stack cục bộ. |
| [`scripts/download_open_songs.py`](../scripts/download_open_songs.py) | Tải bài hát thử nghiệm miễn phí/mở. |
| [`scripts/run_pipeline.py`](../scripts/run_pipeline.py) | Chạy tách stem, chép lời, nhịp, hợp âm và báo cáo. |
| [`scripts/install_research_repos.sh`](../scripts/install_research_repos.sh) | Shallow-clone repo nghiên cứu tùy chọn vào `third_party/`. |
| [`scripts/musia_lyricfit_openai.py`](../scripts/musia_lyricfit_openai.py) | Trợ lý tùy chọn để thích nghi lời hát bằng OpenAI. |
| [`references/`](../references/) | Kiến trúc, nghiên cứu sâu và ghi chú cài đặt cục bộ. |
| [`TODO.md`](../TODO.md) | Danh sách việc cần làm và bước kỹ thuật tiếp theo. |

## Bắt Đầu Nhanh

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

Kết quả được ghi vào:

```text
data/runs/<run-name>/
```

Âm thanh sinh ra, bài hát tải về, trọng số mô hình và repo bên thứ ba được git bỏ qua.

## Kiểm Chứng Cục Bộ

Smoke test cục bộ trên một bản ghi mở từ Wikimedia Commons đã chạy thành công trên máy NVIDIA RTX 4090 D:

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

Kết quả ghi nhận:

- Bốn stem: `bass`, `drums`, `vocals`, `other`
- Âm thanh bổ sung: `instrumental`, `human_sound`
- Ước lượng tempo: `129.20 BPM`
- Số beat: `257`
- Đoạn hợp âm: `132`
- Trạng thái lời: `ok`

Xem [`references/local-setup-and-test-report.md`](../references/local-setup-and-test-report.md).

## Hướng Kiến Trúc

Musia không chỉ là dịch cộng TTS. Pipeline đầy đủ dự kiến là:

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

Repo này triển khai lớp phân tích cục bộ đầu tiên. Tổng hợp giọng hát với YingMusic-Singer-Plus, SoulX-Singer và các mô hình liên quan vẫn là tích hợp nghiên cứu vì cần trọng số lớn, kiểm tra giấy phép và đóng gói worker GPU riêng.

## Trích Dẫn

Nếu dùng Musia trong nghiên cứu, hãy trích dẫn repo này. GitHub đọc [`CITATION.cff`](../CITATION.cff) và hiển thị **Cite this repository** trên trang repo.

```bibtex
@software{chen_musia_2026,
  author = {Chen, Lachlan},
  title = {Musia: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musia}
}
```

## Trạng Thái

Musia là phần mềm nghiên cứu giai đoạn đầu. Pipeline cục bộ dùng được cho thử nghiệm và tạo artifact, nhưng bộ nhận diện hợp âm vẫn là baseline nhẹ và lớp hát lại có thể hát được chưa sẵn sàng cho sản xuất. Hãy dùng bài hát bạn sở hữu, bài public-domain, bài có giấy phép hoặc nội dung do creator tải lên.
