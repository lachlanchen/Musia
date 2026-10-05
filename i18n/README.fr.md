[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)

[![LazyingArt banner](https://github.com/lachlanchen/lachlanchen/raw/main/figs/banner.png)](https://github.com/lachlanchen/lachlanchen/blob/main/figs/banner.png)

# Musia

*Localisation musicale par IA : extraire la voix humaine, les pistes, les paroles, les temps et les accords d'une chanson, puis préparer un re-chant multilingue chantable.*

[![Website](https://img.shields.io/badge/Website-lazying.art-0EA5E9?style=for-the-badge)](https://lazying.art)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](../environment.yml)
[![CUDA](https://img.shields.io/badge/CUDA-tested-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](../references/local-setup-and-test-report.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-lachlanchen-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/lachlanchen)

Musia est un prototype de recherche local-first pour la localisation musicale par IA. Le MVP actuel prend une chanson, la sépare en quatre pistes Demucs `bass`, `drums`, `vocals` et `other`, crée un mix `instrumental`, expose la voix comme `human_sound`, transcrit les paroles, estime les temps et produit des segments d'accords de type Chordify.

## L’Application Musia

[![Télécharger Musia sur Google Play](https://img.shields.io/badge/Google_Play-Download-00875F?style=for-the-badge&logo=googleplay&logoColor=white)](https://play.google.com/store/apps/details?id=art.lazying.musia) · [Ouvrir l’application web](https://musia.lazying.art)

Android 0.1.1 est disponible à **2,99 $US**. Apprenez grâce à l’écoute, aux exercices rythmiques, aux diagrammes d’accords de guitare, à la vitesse réglable sans modifier la hauteur et aux boucles de phrases. Aucun compte ni abonnement requis.

[![Fiche publique Google Play, capturée le 5 octobre 2026. Le prix peut varier selon la région.](../store/assets/readme/google-play.png)](https://play.google.com/store/apps/details?id=art.lazying.musia)

*Fiche publique Google Play, capturée le 5 octobre 2026. Le prix peut varier selon la région.*

### Dans l’Application Android

| Bibliothèque musicale | Pratique guidée |
| :---: | :---: |
| <img src="../store/assets/readme/android-library.png" width="260" alt="Bibliothèque musicale"> | <img src="../store/assets/readme/android-practice.png" width="260" alt="Pratique guidée"> |

Captures réelles de l’application Android publiée, et non des maquettes.

<details>
<summary>Aperçu natif macOS (en cours d’examen)</summary>

Les applications natives iOS et macOS ont été soumises à l’examen et ne sont pas encore publiques au 5 octobre 2026.

![Espace de pratique natif Mac avec paroles, vitesse et doigtés de guitare](../store/assets/macos/03-song.png)

</details>

| Donate | PayPal | Stripe |
| --- | --- | --- |
| [![Donate](https://img.shields.io/badge/Donate-LazyingArt-0EA5E9?style=for-the-badge&logo=kofi&logoColor=white)](https://chat.lazying.art/donate) | [![PayPal](https://img.shields.io/badge/PayPal-RongzhouChen-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/RongzhouChen) | [![Stripe](https://img.shields.io/badge/Stripe-Donate-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400) |

## Sorties

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

`instrumental.wav` est mélangé depuis `bass + drums + other`. `human_sound.wav` est la piste vocale isolée `vocals.wav`.

## Contenu Actuel

| Path | Purpose |
| --- | --- |
| [`musia/`](../musia/) | Boîte à outils locale d'analyse Python. |
| [`scripts/bootstrap_musia.sh`](../scripts/bootstrap_musia.sh) | Crée l'environnement conda et installe la pile locale. |
| [`scripts/download_open_songs.py`](../scripts/download_open_songs.py) | Télécharge des chansons de test libres/ouvertes. |
| [`scripts/run_pipeline.py`](../scripts/run_pipeline.py) | Lance séparation, transcription, temps, accords et rapport. |
| [`scripts/install_research_repos.sh`](../scripts/install_research_repos.sh) | Clone les dépôts de recherche optionnels dans `third_party/`. |
| [`scripts/musia_lyricfit_openai.py`](../scripts/musia_lyricfit_openai.py) | Assistant optionnel d'adaptation de paroles avec OpenAI. |
| [`references/`](../references/) | Architecture, recherche approfondie et notes d'installation locale. |
| [`TODO.md`](../TODO.md) | Liste de construction et prochaines étapes. |

## Démarrage Rapide

```bash
bash scripts/bootstrap_musia.sh
PYTHONNOUSERSITE=1 conda run -n musia python scripts/download_open_songs.py --id danny-boy-1917
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny --max-duration 45 --asr-model tiny
```

Les résultats sont écrits dans :

```text
data/runs/<run-name>/
```

Les audios générés, chansons téléchargées, poids de modèles et clones tiers sont ignorés par git.

## Validation Locale

Le test local sur un enregistrement ouvert de Wikimedia Commons a réussi sur une machine NVIDIA RTX 4090 D :

```bash
PYTHONNOUSERSITE=1 conda run -n musia python scripts/run_pipeline.py data/open_songs/danny-boy-1917/original.ogg --run-name smoke-danny-120-fixed --max-duration 120 --asr-model base.en --language en --demucs-device cuda
```

Résultat enregistré :

- Quatre pistes : `bass`, `drums`, `vocals`, `other`
- Audio supplémentaire : `instrumental`, `human_sound`
- Tempo estimé : `129.20 BPM`
- Temps : `257`
- Segments d'accords : `132`
- État des paroles : `ok`

Voir [`references/local-setup-and-test-report.md`](../references/local-setup-and-test-report.md).

## Direction Architecturale

Musia n'est pas seulement traduction plus TTS. Le flux complet visé est :

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

Ce dépôt implémente la première couche d'analyse locale. La synthèse chantée avec YingMusic-Singer-Plus, SoulX-Singer et des modèles associés reste une intégration de recherche, car elle exige de gros poids, des vérifications de licence et des workers GPU séparés.

## Citation

Si vous utilisez Musia en recherche, citez le dépôt. GitHub lit [`CITATION.cff`](../CITATION.cff) et affiche **Cite this repository** sur la page du dépôt.

```bibtex
@software{chen_musia_2026,
  author = {Chen, Lachlan},
  title = {Musia: Local-first AI song localization and music analysis},
  year = {2026},
  url = {https://github.com/lachlanchen/Musia}
}
```

## Statut

Musia est un logiciel de recherche précoce. La chaîne locale fonctionne pour les tests et les artefacts, mais le détecteur d'accords reste une base légère et la couche de re-chant chantable n'est pas encore prête pour la production. Utilisez des chansons que vous possédez, du domaine public, licenciées ou fournies par leurs créateurs.
