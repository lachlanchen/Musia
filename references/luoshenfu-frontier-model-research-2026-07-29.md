# 洛神赋级国风歌曲：前沿模型研究与 Musia 升级方案

日期：2026-07-29

## 目标

在不模仿或克隆具体歌手声线的前提下，追求《洛神赋》题材所需要的
古典、空灵、流动、摄人心魄和人神相隔的情感张力，并让中文咬字、
旋律、编曲、演唱和歌词覆盖率同时达到更高水平。

公开检索确认用户指的是乱徵在 2026 年发布的《洛神》，其歌词选取了
“翩若惊鸿，婉若游龙”“若轻云之蔽月，若流风之回雪”等《洛神赋》
原句。公开页面只能可靠确认歌名、歌手和歌词，若要逐段研究其唱腔、编曲
与动态，仍需用户提供合法的试听链接或本地参考音频。本方案只提炼
“古典文本、空灵女声、现代电影化层次、可记忆的原句反复”这些可复用
属性，不复制该表演的声线、旋律或具体编曲。

## 结论

Musia 不应按论文指标立刻替换 ACE-Step。完成同题实机 A/B 后，最佳升级
方式是增加一个受控候选与审核层：

1. `ACE-Step 1.5 XL Turbo` 继续作为已验证的生产基线。
2. `HeartMuLa-oss-3B-happy-new-year` 作为 Apache 2.0 的新质量挑战者。
3. `SongGeneration-v2-large / LeVo 2` 已加入本地 research-only 前沿对照。
4. `MOSS-Music + faster-whisper + HeartTranscriptor + APEX + 信号测量`
   构成多证据审核，不让单一模型决定“最好”。
5. 只有经过人工听感、ASR、歌词覆盖和音频健康检查的候选才能进入网站。

这比“模型越大就自动替换旧模型”更可靠。Musia 的历史结果已经证明，
ACE XL SFT 有时会比 XL Turbo 更容易产生无歌词、噪声或片尾话术；最终选择
必须服从具体歌曲的听感，而不是模型名称。

截至本次基准，LeVo 2 在 APEX 审美分数上略高于当前 ACE 结构基线，但古文
咬字更差、原始混音存在削波，且许可证禁止生产发布。它证明了新路线有价值，
却没有推翻 ACE 的生产默认。当前最稳妥的升级是：

```text
ACE 多 seed 生产候选
  + LeVo/HeartMuLa 本地研究挑战者
  + 独立盲 ASR 与审美排序
  + 人工终选
```

截至 2026-07-29 的最后一轮官方源复核还发现两个更晚的前沿方向：

- Qwen-Music 技术报告在 16 个客观指标中的 13 个报告了领先结果，并提出
  Melody-CoT、文本到歌曲和 cover 生成；但 Qwen 官方 Hugging Face 模型列表
  和 GitHub 组织当前都没有可下载的 Qwen-Music 权重或推理仓库。
- 2026-07 的全曲层级自回归 + FullDiT 论文展示了两级旋律控制，但同样没有
  公开可运行 checkpoint。

因此它们是最高优先级跟踪项，不是今天能“拉下来”的模型。把论文结果写成
已安装能力会误导使用者；Musia 只把完成权重校验和本机推理的模型标为
`installed`。

## 模型比较

| 模型 | 本地状态 | 优点 | 局限 | Musia 角色 |
| --- | --- | --- | --- | --- |
| ACE-Step 1.5 XL Turbo/SFT | 已安装 | 快、结构完整、已有大量成功作品；Apache 2.0 | 中文歌词仍可能跳句；SFT 并非每首都优于 Turbo | 生产基线 |
| HeartMuLa HNY 3B + HeartCodec | 已安装并刷新 | 官方强调歌词控制和音质；多语言；Apache 2.0 | 单卡约占满 24GB；尚未像 ACE 一样积累大量 Musia 参数经验 | 新生产候选 |
| LeVo 2 / SongGeneration-v2-large | 已安装、校验并实跑 A/B | 4B、最长 4m30s、支持中英日；官方报告 PER 8.55%，可输出人声/伴奏双轨 | 当前许可仅限学术、研究、教育；古文咬字仍漂移；原始混音偏热；上游 GitHub 暂时返回 404 | 本地研究 A/B，不发布 |
| Qwen-Music | 仅论文，无官方可下载权重 | Melody-CoT、整首人声歌曲、text-to-music 与 cover；论文报告 13/16 客观指标领先 | 当前 Qwen 官方模型列表和代码组织均未发布对应模型 | 权重发布后优先盲测 |
| Shao（原 Khala） | 暂不下载 | 统一 64 层 RVQ 声学 token；公开代码与约 10GB 权重；中文团队的新路线 | 当前上游仍有公开音质问题，且依赖 Megatron/NGC/Apex/Transformer Engine，部署风险高 | 跟踪并等待上游修复 |
| Alibaba Fun-Music v1 | 云端限量预览 | 中文/英文整歌、自定义歌词、音色性别控制；官方称 v1 质量更高 | 闭源、北京区域限量预览，不能拉取权重，不是本地可复现模型 | 获得权限后做闭源盲测 |
| MOSS-Music 8B Thinking | 已安装 | 中文团队的音乐理解模型；歌词 ASR、时间戳、曲式、和弦和音乐问答 | 只做音频到文本理解，不生成歌曲 | 第三路独立 QA |
| APEX + MERT-v1-95M | 已安装、校验并修复本地兼容 | 从音频估计连贯性、音乐性、记忆度、清晰度和自然度 | 学习型排序信号，不懂歌词正确性，也不能替代人耳 | 候选排序辅助 |
| SegTune | 官方代码已发布，无现成官方 checkpoint | 段落级指令微调，可增强曲式与局部控制；Apache 2.0 | 需要基于 DiffRhythm 自行训练，不能作为即插即用成品；未证明当前成品听感超过 ACE/LeVo | 训练研究，不进入默认安装 |
| Muse | 未下载 | ACL 2026；代码、模型、训练数据和评估流程均公开；MIT | 当前证据偏向可复现性与段落控制，没有证明成品音乐性高于 LeVo 2 或 ACE | 后续研究候选 |
| YuE | 已安装最小中文路线 | 长篇歌词到完整歌曲；Apache 2.0 | 多段完整生成推荐 80GB 级显存，单卡量化会牺牲音乐性 | 重型备选 |
| SongBloom | 未纳入主线 | 长结构一致性和 DPO 版本；4090 可用 BF16 | 依赖 10 秒参考音频，许可需单独审查，整体早于 LeVo 2 | 暂不优先 |
| 2026-07 FullDiT 前沿论文 | 无公开可运行权重 | 两级旋律控制、全曲 flow matching，排行榜表现强 | 目前只有论文，不能“拉下来”投入本地生产 | 跟踪名单 |

## HeartMuLa 实机基准

本机已用最新版公开 3B 权重和 HeartCodec 生成 90 秒私有候选：

```text
data/creative_projects/luoshen-model-benchmark-20260729/
  heartmula/luoshen-heartmula-candidate-a.mp3
```

基础音频健康检查正常：

- 48 kHz 立体声，MP3 解码后 90.08 秒；
- 综合响度约 -15.8 LUFS；
- 真峰值约 -0.7 dBTP；
- 没有静音文件或纯数字噪声故障。

不过它没有尾部静音，最后 100 ms 仍约 `-20.35 dBFS`，存在硬切风险；
对照 ACE `seed 829102` 的最后 100 ms 已降到 `-57.69 dBFS` 并有 1.9 秒
自然尾静音。HeartMuLa 因此不能仅凭“无削波”通过完整性门槛。

但 `large-v3` 无 VAD 转写只可靠恢复到约 65 秒，后段歌词缺失，前段也有
明显发音漂移。该候选因此停留在 `review`，不能证明 HeartMuLa 已经超越
ACE。这个结果进一步说明：模型宣传中的“最好”不能替代同曲实机审核。

为排除 Whisper 对古文歌声的偏差，又用 MOSS-Music Thinking 对同一候选盲
转写。它完整恢复了 22.52-67.38 秒的主歌与第一遍副歌，但没有找到输入中
后续 Bridge、重复副歌和 Outro 的可辨歌词：

```text
heartmula/moss-thinking-lyrics.txt
```

因此 HeartMuLa 候选被降级并不是 Whisper 单路误判；和 ACE `seed 829102`
相比，它确实少唱了后半歌词。

为修复官方示例在新版 `torchaudio` 上保存失败的问题，Musia 新增
`scripts/run_heartmula.py`，用 SoundFile 输出 24-bit 中间音频，再由
FFmpeg 编码 MP3，避免生成完成后因 TorchCodec/FFmpeg ABI 不匹配而丢失
结果。

HeartTranscriptor 权重也已安装，并对目前 ACE 长版中 ASR 最完整的
`seed 829102` 分离人声做了第二路转写：

```text
data/creative_projects/luoshen-model-benchmark-20260729/
  ace/reviews/seed829102-hearttranscriptor.json
```

HeartTranscriptor 与 faster-whisper large-v3 都确认该候选覆盖了大部分段落，
但也共同指出古文发音有明显漂移，桥段和末段存在压缩或漏唱。它因此只能
作为 ACE 基线候选，不能直接进入公开网站。

随后又以 24 行平衡歌词生成 `seed 829141-829144`。小模型初筛与
Demucs + large-v3 复核都显示：这批候选只稳定恢复了开头意象和部分第二段，
覆盖率显著低于 `seed 829102`。因此本轮明确淘汰，不因“新生成”而替换旧的
较优候选。当前 ACE 结构基线仍是：

```text
data/creative_projects/luoshen-model-benchmark-20260729/
  ace/outputs/372a2c23-b898-c8e7-7e42-b4d4c46fe0bc.wav
```

为验证“XL SFT 50 步是否必然优于 XL Turbo 8 步”，又使用相同歌词、
110 秒时长、76 BPM 和 D minor 生成 `seed 829151-829152`。两份 SFT
候选都在 110 秒边界仍保持约 `-12` 至 `-14 dBFS` 的高电平，动态范围仅
`2.6-3.1 LU`，并有轻微 DC 偏移；`small` ASR 也没有恢复出任何可辨歌词。
它们因此在第一轮自动门禁即被淘汰，不进入 MOSS 或人工终选。这个对照证明：
高步数 SFT 可以增加声学细节，但不会自动保证歌声、歌词或完整结尾；Musia
不得按模型名称或步数替代同曲实测。

MOSS-Music 8B Thinking 对该文件做盲转写后，完整找到了 13.82-96.83 秒的
全部主段、桥段和末副歌，并准确恢复了大部分古文：

```text
ace/reviews/seed829102-moss-thinking-lyrics.txt
```

它比 HeartTranscriptor 和 faster-whisper 更完整地证明了 `seed 829102` 的
歌词覆盖，但仍把若干音近古文识别成“若为若安”“静之难期”“若忘若怀”。
这些位置应结合原文保留“若危若安”“进止难期”“若往若还”，不能直接把
单路 ASR 当作事实。

同一个 MOSS 开放式分析声称存在轻微削波和突兀收尾。FFmpeg EBU R128 客观复核
则得到 `-12.5 LUFS`、`7.9 LU LRA`、`-1.0 dBFS` 真峰值；106 秒后波形连续
衰减到静音，没有数字削波证据。因此 MOSS 适合提供歌词与结构线索，响度、
削波、静音和截断判断仍必须由信号测量验证。

## LeVo 2 实机基准

本机已下载并逐文件核对 LeVo 2 的主模型和运行时权重。主模型
`model.pt` 为 `12,899,965,446` 字节，SHA-256 为：

```text
dc763aa9a76a22a87597c2faf9a51c24d13349ac754699b37e9068b483639def
```

其余约 14.7GB 的 tokenizer、VAE、ContentVec 和 Demucs 权重也全部与
Hugging Face 官方元数据的大小及 SHA-256 一致，目录中没有残留 `.aria2`
文件。本机 RTX 4090 D 以 low-memory 分层卸载模式成功生成 mixed、vocal、
bgm 三轨。

### Candidate A：电影化国风

```text
data/creative_projects/luoshen-model-benchmark-20260729/levo/
  outputs-a/audios/luoshen-levo-v2-a.flac
  outputs-a/audios/luoshen-levo-v2-a_vocal.flac
  outputs-a/audios/luoshen-levo-v2-a_bgm.flac
```

- 149.28 秒，48 kHz 立体声；
- `-8.4 LUFS`，`8.6 LU LRA`，真峰值约 `+1.0 dBFS`；
- 约 `0.020%` 采样触及削波阈值，原始混音不能直接发布；
- MOSS、faster-whisper 和 HeartTranscriptor 都找到了目标段落与末副歌；
- 但“罗袜”“进止难期”“芙蕖”等古文出现明显音近漂移；
- 中段有约 30 秒器乐/无词吟唱，曲式有呼吸感，但比输入的
  `[inst-short]` 展开得更长。

### Candidate B：古典跨界抒情

```text
data/creative_projects/luoshen-model-benchmark-20260729/levo/
  outputs-b/audios/luoshen-levo-v2-b.flac
  outputs-b/audios/luoshen-levo-v2-b_vocal.flac
  outputs-b/audios/luoshen-levo-v2-b_bgm.flac
```

- 181.16 秒，48 kHz 立体声；
- `-10.3 LUFS`，`11.8 LU LRA`，真峰值约 `+0.5 dBFS`；
- 约 `0.014%` 采样触及削波阈值；
- APEX 的音乐性和记忆度略高于 A；
- 模型自行扩展了较多副歌和尾段重复，古文偏音也更多，服从歌词不如 A。

为让人工盲听不受响度差异误导，另生成统一到 `-14 LUFS / -1.5 dBTP`
的本地试听副本：

```text
data/creative_projects/luoshen-model-benchmark-20260729/listen/
  01-ace-seed829102-production-reference.mp3
  02-levo-v2-a-research-preview.mp3
  03-levo-v2-b-research-preview.mp3
```

这些 LeVo 文件只能本地研究，不得上传 Fun、交给 LazyEdit 或商业发布。
响度归一化只能避免播放音量误导，不能恢复原始削波已经丢失的峰值形状。

## APEX 审美排序

APEX 以 MERT 音乐表征估计五个 1-5 分维度。它不读取期望歌词，适合补充
“旋律和整体听感”证据，但不能判断古文是否唱对。结果如下：

| 候选 | 连贯性 | 音乐性 | 记忆度 | 清晰度 | 自然度 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ACE `seed 829102` | 2.86 | 2.66 | 2.80 | 2.56 | 2.50 |
| ACE `1617555a...` | 2.90 | 2.75 | 2.85 | 2.64 | 2.56 |
| HeartMuLa A | 2.89 | 2.71 | 2.85 | 2.57 | 2.55 |
| LeVo 2 A | 2.98 | 2.71 | 2.84 | 2.61 | 2.60 |
| LeVo 2 B | 2.96 | 2.73 | 2.88 | 2.60 | 2.57 |

ACE `1617555a...` 的审美分略高于 `seed 829102`，但三路歌词识别显示其
古文准确度明显更低；`seed 829102` 仍是更平衡的结构基线。这个例子说明
APEX 只能排序“值得听”的候选，不能单独执行终选。

本地集成还修复了两个上游兼容问题：

1. APEX 外层 checkpoint 在新版 Transformers 中会把构造器已加载的嵌套
   MERT 权重重新初始化为零；Musia 在加载 APEX 头后显式重载已校验的 MERT。
2. MERT 针对 Transformers 4.24 的全 1 attention mask 在新 Hubert 编码器中
   会从第一层产生 NaN；固定长度段不需要这个 mask，Musia 将其关闭，并在
   任一输出非有限时让命令失败。

## 为什么 LeVo 2 值得测试

LeVo 2 使用分层语言模型负责全曲结构，再用扩散渲染器补足音色与声学细节。
官方给出的 v2-large 指标包括：

- 4B 参数；
- 最长 4 分 30 秒；
- 中文、英文、日文等多语言歌词；
- 无参考音频约 22GB 显存，有参考音频约 28GB；
- 歌词音素错误率 PER 8.55%；
- 可生成混音、纯伴奏、纯人声或分离的人声/伴奏。

它正好针对 Musia 目前最痛的两个问题：优美旋律与歌词不丢失之间的矛盾，
以及整曲结构与局部音质之间的矛盾。

但其许可证明确要求只用于学术、研究和教育，禁止商业或生产用途。因此：

- 可以在本机生成 A/B 研究候选；
- 不得默认加入 Fun 公开目录；
- 不得交给 LazyEdit、Shipinhao Music 或其他商业发布链；
- 未来只有上游许可证变化或取得单独授权后才能解除限制。

## 《洛神赋》质量升级流程

### 1. 先做文学与发音准备

- 从曹植原文中选取最有音乐性的意象，不强塞整篇赋文。
- 重点候选包括“翩若惊鸿，婉若游龙”“轻云蔽月，流风回雪”
  “凌波微步，罗袜生尘”等。
- 建立古汉语多音字、罕见字和专名读音表。
- 公开歌词优先保留原文之美；模型内部可以使用发音控制，但不能污染网站歌词。

### 2. 制作统一 producer brief

- 情感弧线：惊见 -> 靠近 -> 心动 -> 人神相隔 -> 回望洛水。
- 演唱：清晰、有气息层次的女性或中性高音，不模仿真实歌手。
- 编曲：古琴/箫/埙/弦乐与现代 cinematic art-pop，避免廉价“古风模板感”。
- 旋律：主歌流动含蓄，副歌出现可记忆的上行长线，尾声留下水面般余韵。
- 负面要求：不朗诵、不堆字、不夹片尾话术、不削波、不埋人声、不突然截尾。

### 3. 同一歌词包做模型 A/B

- ACE XL Turbo：6-10 个 seed，沿用 Musia 成功参数。
- HeartMuLa HNY：3-5 个采样温度/CFG 组合。
- LeVo 2：2-4 个 research-only 候选，优先 `--low_mem`、无参考音频。
- 不用受版权保护的歌曲作为音频提示；需要风格参考时使用自有或开放素材。

### 4. 三轮质量门

第一轮，自动健康检查：

- 有可听清的歌声；
- LUFS、峰值和动态范围正常；
- 无长段噪声、爆音、数字破裂或片尾闲聊；
- 歌曲结构完整且结尾自然。

统一执行：

```bash
PYTHONNOUSERSITE=1 conda run -n musia python \
  scripts/audio_health_report.py song.wav review/audio-health
```

报告同时保存机器可读 JSON 与 Markdown，MOSS 等理解模型关于削波、爆音和硬切
的描述只能作为待查线索，不能覆盖这份客观报告。

第二轮，歌词与发音：

- 分离人声后做至少两次 ASR；
- 对重要候选增加 MOSS-Music Thinking 盲转写，不把参考歌词喂给第一遍 ASR；
- 对照输入歌词逐行查漏、查重复、查错序；
- ASR 与原文音近时保留更美、更合理的原文；
- 音数、结构和声音都明显不同时才按实际演唱修正；
- 手工检查开头、段落间隙和最后的弱尾音。

第三轮，音乐审美：

- 旋律是否有真正可记住的主题；
- 副歌是否比主歌自然抬升；
- 留白是否让情绪呼吸；
- 人声是否始终站在编曲前景；
- 全曲是否从第一段到结尾都保持质量，而非只有十秒高光。

### 5. 选择与发布

盲听评分建议：

```text
30% 旋律与情感
20% 演唱自然度
15% 编曲与结构
15% 中文咬字和歌词覆盖
10% 音质与动态
10% 重听欲望
```

只有许可证允许且通过全部质量门的候选，才进入歌词校正、网站 JSON、封面、
和录制发布流程。LeVo 2 候选即使听感第一，也只能保留在本地研究目录。

## 本机安装

HeartMuLa 刷新：

```bash
bash scripts/download_quality_backends.sh heartmula
bash scripts/install_quality_envs.sh heartmula
```

可靠运行：

```bash
PYTHONNOUSERSITE=1 conda run -p .conda/heartmula \
  python scripts/run_heartmula.py \
  --lyrics path/to/lyrics.txt \
  --tags path/to/tags.txt \
  --output path/to/candidate.mp3
```

LeVo 2 research-only：

```bash
MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE=1 \
  bash scripts/download_quality_backends.sh songgeneration-v2

bash scripts/install_quality_envs.sh songgeneration-v2
```

运行：

```bash
MUSIA_ACCEPT_SONGGENERATION_RESEARCH_LICENSE=1 \
  scripts/run_songgeneration_v2.sh input.jsonl output-dir
```

默认使用低显存模式且不启用 Flash Attention。确认环境可用后，可安装
Flash Attention 并传 `--flash-attn`。

`run_songgeneration_v2.sh` 会先调用
`scripts/validate_songgeneration_v2_input.py`，严格检查 LeVo 的段落格式和
官方推荐标签。若确实需要研究开放词汇，可以设置
`MUSIA_SONGGEN_ALLOW_OPEN_TAGS=1`，但默认不放宽，因为自然语言式长提示会
降低上游所声明的稳定性。

包装脚本还会强制 `PYTHONNOUSERSITE=1`。本机预检发现，若允许
`~/.local/lib/python3.10/site-packages` 介入，旧 `torchaudio` 会覆盖 LeVo
环境中的 PyTorch 2.6 配套版本并产生未定义符号错误。隔离用户 site-packages
后，48 kHz 双声道 FLAC 的实际保存测试已通过，避免推理完成后才丢失音频。

镜像仓库中的 `tools/new_auto_prompt.pt` 原本只是 127 字节 Git LFS 指针，
而镜像 LFS 服务没有真实对象。下载器现在从腾讯官方 Hugging Face Space 的
固定 revision 获取同一对象，并以指针声明的 `14,959,842` 字节和
`616dbe27...34e7` SHA-256 校验后才替换。运行器每次推理前也会复核该资产，
防止把文本指针误当成 PyTorch checkpoint。

LeVo 的旧 OpenAI CLIP 依赖仍导入 `pkg_resources`，而 setuptools 81+ 已移除
它。`scripts/install_quality_envs.sh songgeneration-v2` 因此固定
`setuptools<81`；运行器会在昂贵采样开始前做导入预检。

下载器支持断点续传。大文件在未完成时可能已经显示最终逻辑大小，不能只用
`ls` 判断；必须确认没有相邻的 `.aria2` 控制文件，并运行官方元数据校验：

```bash
PYTHONNOUSERSITE=1 conda run -n musia python \
  scripts/verify_hf_artifacts.py \
  lglg666/SongGeneration-v2-large \
  third_party/SongGeneration-v2/checkpoints/SongGeneration-v2-large \
  model.pt --sha256
```

运行时权重也应以同一脚本按仓库相对路径校验。`--sha256` 会读取全部大文件，
速度较慢，但首次安装和迁移机器后必须执行。Musia 下载器现在会在 LeVo、
HeartTranscriptor、APEX 和 MERT 下载结束时自动执行对应的完整 SHA-256
校验；这里保留手工命令，便于迁移后复核和故障定位。

下载器会对 Hugging Face 大文件的临时签名过期做最多五轮续传。每轮都重新
访问稳定的 `resolve/main/...` 地址以取得新签名，同时保留 `.aria2` 的已下载
分块；不能手工删除 `.aria2`，否则会失去可靠的断点状态。

MOSS-Music 独立审核：

```bash
PYTHONNOUSERSITE=1 conda run -p .conda/moss-music \
  python scripts/run_moss_music_analysis.py \
  path/to/song-or-vocal.flac \
  path/to/review/moss-thinking-lyrics.txt \
  --model thinking --task lyrics
```

第一遍必须保持盲转写；不能把期望歌词写进 prompt，否则会把“模型听见了什么”
和“模型根据文本补全了什么”混为一谈。之后才用公开原文、发音控制文本和另外两路
ASR 做交叉校正。

APEX 审美辅助：

```bash
bash scripts/download_quality_backends.sh apex-music
bash scripts/install_quality_envs.sh apex-music

scripts/run_apex_music_quality.sh \
  path/to/song.wav \
  path/to/review/apex.json
```

APEX 与 MERT 权重都必须先用 `scripts/verify_hf_artifacts.py --sha256` 校验。
输出用于候选排序，不得替代歌词审计、信号测量和人工听感。

## 正式原创验证：《洛水照影》

在模型基准完成后，又用同一质量门制作了一首生产许可清晰的原创中文候选
《洛水照影》。作品只借鉴洛水、人神相隔、轻云回雪等公共文化意象，不复制
乱徵《洛神》或其他现代录音的旋律、编曲、声线与具体表达。

本轮以 108 秒、74 BPM、D minor 的紧凑歌词生成 12 个 ACE XL Turbo 候选。
整曲 ASR 一度把音乐性较好的候选误判成通用片尾话术；Demucs 分离人声后，
large-v3 与 MOSS-Music 均恢复了实际歌词。这证明高质量歌曲不能只凭混音
轨 ASR 淘汰，正式门禁应为：

```text
整曲信号健康
  -> APEX 粗排
  -> Demucs 分离人声
  -> large-v3 + MOSS 双路盲转写
  -> 音乐优先 / 歌词优先双候选
  -> 真人完整试听终选
```

当前保留两份统一到约 `-14 LUFS / -1.5 dBTP` 的本地试听副本：

```text
data/creative_projects/luoshui-zhaoying-20260729/selected/
  01-luoshui-zhaoying-music-first-seed829213.mp3
  02-luoshui-zhaoying-lyric-first-seed812401.mp3
```

音乐优先版原始 WAV 为 `ce775df6...`：APEX 音乐性 `2.82`、记忆度
`2.88`，MOSS 判断女声、钢琴弦乐层次和副歌抬升完整；信号健康检查为
`-12.5 LUFS`、`-0.8 dBFS` 真峰值、无削波、自然收尾。歌词优先版原始
WAV 为 `02e3a8ba...`：分离人声 large-v3 的歌词重合度由前者的 `0.714`
提高到 `0.782`，并恢复了完整段落结构，但 APEX 音乐性与记忆度略低。

因此不能伪造一个“机器唯一最佳版”。01 是当前审美证据更强的主候选，02 是
歌词完整性更强的保底候选；必须由真人完整听完后再进入歌词逐词校正、网站、
封面与发布流程。详细证据保存在私有项目的 `SELECTION.md`。

## 本机状态与注意事项

- 本轮代码版本固定为 ACE-Step 1.5 `6d467e4b5081`、HeartMuLa
  `3783bdb8441f`、LeVo 2 镜像 `df835fa0e847`、MOSS-Music
  `ad107c7ddaa0`；模型权重不进入 Git。
- 完成 LeVo、APEX 和 MERT 下载后，项目盘仍有约 500GB 可用空间。
- 系统检测到 RTX 4090 D；PyTorch CUDA 可用并能看到一张 GPU。
- LeVo 环境实测显存总量 23.52 GiB、启动前可用 23.14 GiB；默认低显存模式并
  启用 PyTorch expandable segments，降低解码阶段的显存碎片风险。
- `nvidia-smi` 当前报告 NVML 用户态库与内核驱动版本不一致，但 PyTorch CUDA
  初始化成功。此问题不阻塞初步推理；系统方便重启时再统一驱动状态。
- 权重、环境、缓存和第三方仓库都位于 Git 忽略目录，不进入 Musia 仓库。

## 主要来源

- ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5
- ACE-Step 1.5 paper: https://arxiv.org/abs/2602.00744
- HeartMuLa: https://github.com/HeartMuLa/heartlib
- HeartMuLa model: https://huggingface.co/HeartMuLa/HeartMuLa-oss-3B-happy-new-year
- LeVo 2 demo: https://levo-demo.github.io/levo_v2_demo/
- LeVo 2 paper: https://arxiv.org/abs/2606.30642
- LeVo 2 checkpoint: https://huggingface.co/lglg666/SongGeneration-v2-large
- Qwen-Music report: https://arxiv.org/abs/2607.11699
- Qwen official models: https://huggingface.co/Qwen/models
- Shao: https://github.com/Shao-Music-AI/Shao
- Shao paper: https://arxiv.org/abs/2605.01790
- Alibaba Fun-Music: https://www.alibabacloud.com/help/en/model-studio/fun-music/
- MOSS-Music: https://github.com/OpenMOSS/MOSS-Music
- APEX model: https://huggingface.co/amaai-lab/apex
- APEX paper: https://arxiv.org/abs/2605.03395
- MERT-v1-95M: https://huggingface.co/m-a-p/MERT-v1-95M
- SegTune: https://github.com/KlingAIResearch/SegTune
- SegTune paper: https://arxiv.org/abs/2606.02638
- Muse: https://github.com/yuhui1038/Muse
- Muse paper: https://arxiv.org/abs/2601.03973
- YuE: https://github.com/multimodal-art-projection/YuE
- Full-song frontier paper: https://arxiv.org/abs/2607.20253
- 乱徵《洛神》歌词索引（仅用于确认作品与文本）:
  https://www.hifiti.com/thread-136515.htm
