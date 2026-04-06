# audiocut-feishu

`audiocut-feishu` is a Codex skill for editing spoken-word audio through a transcript-first workflow:

1. generate a high-quality timestamped transcript locally
2. publish that transcript to a Feishu/Lark doc for review
3. let a human comment with edit intent such as `删除` and `金句`
4. cut the original source audio from those comments

This skill is designed for podcasts, interviews, voice notes, spoken essays, and other transcript-first editing workflows.

## What this skill can do

This skill helps Codex:

1. Transcribe a local audio file with a Whisper-family model
2. Generate fine-grained sentence timestamps
3. Create a commentable Feishu/Lark transcript doc
4. Read Feishu comments from that doc
5. Map `删除` and `金句` comments back to the source audio
6. Produce a `v1` rough cut or `v2` fine cut
7. Export an edited audio file plus an edit note

## Good fit

Use this skill for:

- podcasts
- interviews
- spoken essays
- transcript-first voice content

## Not a good fit

This skill is not intended for:

- music production
- multitrack editing
- EQ, compression, mastering, or restoration
- recreating exact Feishu editor comment-selection behavior through API alone

## Prerequisites

### Required for all users

- a Codex environment with local skill support
- Node.js with `npm` and `npx`
- `lark-cli`
- a Feishu account
- completed `lark-cli config init --new`
- completed `lark-cli auth login`
- a local source audio file such as `mp3`, `m4a`, or `wav`

### Required for the full transcript-generation workflow

- Python 3
- a local `faster-whisper` environment
- internet access for the first model download
- enough disk space for local Whisper model cache

### Recommended but optional

- `ffmpeg` for more reliable output transcoding, especially `mp3`
- `WhisperX` if you later want stronger alignment experiments

For this maintained setup, local `ffmpeg` has already been validated and can be used for reliable `mp3` export.

## Install

Install the skill from GitHub:

```bash
npx skills add https://github.com/helloteraslab/audiocut-feishu -y -g
```

Install `lark-cli`:

```bash
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
```

Initialize and authorize Feishu:

```bash
lark-cli config init --new
lark-cli auth login
```

## ASR setup

The recommended local ASR backend is `faster-whisper`.

Example installation:

```bash
python3 -m venv ~/.venvs/faster-whisper
source ~/.venvs/faster-whisper/bin/activate
pip install --upgrade pip
pip install faster-whisper
```

The recommended model is:

- `large-v3-turbo`

The first run will download the model automatically.

## Workflow

### Full mode

Use this when you start from audio and do not yet have a transcript doc.

1. Give Codex a local audio file.
2. Codex transcribes it locally with `faster-whisper`.
3. Codex creates a new Feishu doc containing sentence-level timestamps.
4. You review the doc and comment with labels such as:
   - `删除`
   - `金句`
   - `修改`
5. You come back to Codex and ask it to cut the audio from the reviewed doc.

### Simplified mode

Use this when you already have a transcript doc.

1. Give Codex the Feishu doc URL.
2. Give Codex the local audio file path.
3. Ask for `v1` or `v2`.

## Version definitions

### `v1` rough cut

`v1` performs only explicit human-comment actions:

- remove content marked with `删除`
- prepend clips marked with `金句`

It does **not** automatically remove filler words, repetitions, or long pauses.

### `v2` fine cut

`v2` includes everything in `v1`, plus automatic fine trimming:

- compress pauses longer than `1s`
- remove high-confidence filler / connector words with obvious air before or after
- remove strict repetitions

The repository also includes a helper for strict repetition detection:

- `scripts/detect_strict_repetition.py`
- `scripts/finalize_v2_plan.py`
- `scripts/render_audio_plan_ffmpeg.py`

It is designed to catch cases like `重复,重复,重复,重复学习` and preserve the final surviving copy that naturally connects into the real sentence.

In the maintained `v2` flow, run strict repetition detection first, then use `scripts/finalize_v2_plan.py` to merge those ranges into the final `delete_ranges` before export.

For stable `wav` / `mp3` export in the maintained setup, render the finalized plan with `scripts/render_audio_plan_ffmpeg.py`.

The intended `v2` execution order is:

1. explicit `删除` comment ranges
2. long-pause compression
3. high-confidence filler trimming
4. strict repetition trimming

## Editing rules

### Long pauses

Default long-pause rule:

- a no-voice pause longer than `1.0s`

Default handling:

- preserve about `0.30s`
- remove the rest

### Filler and connector words

Typical candidates:

- `然后`
- `然后呢`
- `就是`
- `那个`
- `这个`
- `呢`
- `呀`
- `对`
- `嗯`
- `呃`
- `啊`

A filler is only removed when:

- it carries little semantic information
- deleting it does not break the sentence backbone
- it has clearly audible air before or after it

Suggested high-confidence threshold:

- leading air `>= 0.18s`, or
- trailing air `>= 0.18s`, or
- combined air `>= 0.30s`

### Repetition

Two kinds are distinguished:

1. strict repetition
   - examples: `明显明显`, `我我觉得`, `重复,重复,重复`
2. near-duplicate sentence repetition
   - the same meaning is immediately said again

Default behavior:

- strict repetition can be trimmed automatically
- near-duplicate sentence repetition should prefer explicit human comments

For strict repetition, the intended behavior is:

- remove the leading repeated copies
- preserve the last copy when it connects naturally into the following valid phrase

### Cut boundaries

Cuts should land on:

- semantic edges
- acoustic weak points
- natural listening boundaries

Default padding:

- before cut: about `0.03s - 0.08s`
- after cut: about `0.08s - 0.18s`

This is especially important for not chopping off the ends of words.

## Quick start

### English prompt

```text
Please use audiocut-feishu to turn this audio into a commentable Feishu transcript doc.
After I review the doc, I will come back and ask for a v1 or v2 cut.
```

### 中文使用说明

这个 skill 的新流程是：

1. 你先把原始音频发给 Codex
2. Codex 用本地 Whisper 模型转写，并生成带细粒度时间戳的句级文稿
3. Codex 自动把这份文稿发到飞书文档里
4. 你在飞书文档里评论，比如：
   - `删除`
   - `金句`
5. 你再回到 Codex，要求它输出：
   - `V1 粗剪版`
   - 或 `V2 细剪版`

### 中文提示词模板

先建文稿时：

```text
请使用 audiocut-feishu，基于这个音频文件生成一篇可评论的飞书转写文档，并把文档链接发给我。
```

评论完成后：

```text
请使用 audiocut-feishu，基于这篇飞书文档的评论剪辑原始音频。
请告诉我你要输出 v1 粗剪版，还是 v2 细剪版。
```

如果你已经知道要哪个版本，也可以直接说：

```text
请使用 audiocut-feishu，基于这篇飞书文档的评论输出 v2 细剪版。
```

## Output format

Preferred output:

- `mp3`

Fallback output:

- `wav`

If `ffmpeg` is available, Codex should prefer `mp3`.
If `mp3` export is unavailable on the local machine, Codex should explain why and fall back to a working format.

## Repository structure

```text
audiocut-feishu/
├── README.md
├── SKILL.md
└── scripts/
    ├── analyze_silence.swift
    └── compose_audio.swift
```

## Known limitations

- Feishu API comment anchoring is weaker than the editor UI for exact selection replay.
- ASR text and Feishu comment text may differ slightly in punctuation or wording.
- `mp3` output depends on a working local encoder such as `ffmpeg`.
- In this local workflow, `ffmpeg` has been installed and validated for `mp3` export.

## Privacy notes

This repository should include only:

- the skill definition
- helper scripts
- documentation

It should not include:

- source audio files
- private Feishu doc URLs
- local machine paths
- model cache files
