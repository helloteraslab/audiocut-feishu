# audiocut-feishu

`audiocut-feishu` is a Codex skill for transcript-first spoken-word editing:

1. generate a timestamped transcript locally
2. publish that transcript to a Feishu/Lark doc for review
3. let a human comment with edit intent such as `删除` and `金句`
4. cut the original audio from those comments

This skill is designed for podcasts, interviews, voice notes, spoken essays, and other transcript-first editing workflows.

## Two modes

### Base mode

This is the default mode and should feel simple:

1. give Codex an audio file
2. Codex transcribes it locally
3. Codex creates a commentable Feishu doc
4. you review the doc and add comments such as `删除` and `金句`
5. Codex exports a `v1` rough cut or `v2` fine cut

Base mode does **not** require speaker diarization.

### Optional multi-speaker mode

Use this only when you want the generated Feishu doc to distinguish different speakers.

In this mode, Codex additionally:

1. runs speaker diarization
2. labels transcript lines as `说话人 A` / `说话人 B` / ...
3. publishes a multi-speaker transcript doc for review

This mode is optional and should only be enabled when the user explicitly asks for speaker separation.

## What this skill can do

In base mode:

1. Transcribe a local audio file with a Whisper-family model
2. Generate fine-grained sentence timestamps
3. Create a commentable Feishu/Lark transcript doc
4. Read Feishu comments from that doc
5. Map `删除` and `金句` comments back to the source audio
6. Produce a `v1` rough cut or `v2` fine cut
7. Export an edited audio file plus an edit note

In optional multi-speaker mode:

1. Run speaker diarization for multi-speaker audio
2. Build a transcript doc with `说话人 A / B / ...` labels

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

### Required for base mode

- Python 3
- a local `faster-whisper` environment
- internet access for the first model download
- enough disk space for the local Whisper model cache

### Required only for optional multi-speaker mode

- `pyannote.audio`
- a Hugging Face token with access to `pyannote/speaker-diarization-community-1`
- accepted model terms for `pyannote/speaker-diarization-community-1` on Hugging Face

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

## Base mode setup

The recommended local ASR backend is `faster-whisper`.

Example installation:

```bash
python3 -m venv ~/.venvs/faster-whisper
source ~/.venvs/faster-whisper/bin/activate
pip install --upgrade pip
pip install faster-whisper
```

Recommended model:

- `large-v3-turbo`

The first run will download the model automatically.

## Optional multi-speaker setup

Only do this if you explicitly want the transcript doc to distinguish speakers.

1. Create a Hugging Face account
2. Accept the model terms on:
   - [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
3. Create a Hugging Face token
4. Set `HF_TOKEN` or `HUGGINGFACE_TOKEN`
5. Install a compatible `pyannote.audio` environment

The diarization step reads the token from `HF_TOKEN` or `HUGGINGFACE_TOKEN`.

## Workflow

### Base mode

Use this when you want the simplest flow.

1. Give Codex a local audio file.
2. Codex transcribes it locally with `faster-whisper`.
3. Codex creates a new Feishu doc containing sentence-level timestamps.
4. You review the doc and comment with labels such as:
   - `删除`
   - `金句`
   - `修改`
5. You come back to Codex and ask it to cut the audio from the reviewed doc.

### Optional multi-speaker mode

Use this only when you want the transcript doc to label speakers.

1. Give Codex a local audio file.
2. Explicitly ask for a multi-speaker transcript doc.
3. Codex transcribes the audio.
4. Codex runs speaker diarization.
5. Codex creates a Feishu doc with speaker labels.

Preferred layout:

```text
[0001] 说话人 A 00:01.060 - 00:03.960
Hello，这是一个测试文件

[0002] 说话人 B 00:03.960 - 00:08.320
第一步我要测试的关于停顿功能
```

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

The repository includes these helper scripts:

- `scripts/run_pyannote_diarization.py`
- `scripts/build_feishu_transcript_doc.py`
- `scripts/detect_strict_repetition.py`
- `scripts/finalize_v2_plan.py`
- `scripts/render_audio_plan_ffmpeg.py`

The intended `v2` execution order is:

1. explicit `删除` comment ranges
2. long-pause compression
3. high-confidence filler trimming
4. strict repetition trimming

For strict repetition, the maintained flow is:

1. detect repetition with `scripts/detect_strict_repetition.py`
2. merge those ranges into the final plan with `scripts/finalize_v2_plan.py`
3. render the result with `scripts/render_audio_plan_ffmpeg.py`

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
2. near-duplicate sentence repetition

Default behavior:

- strict repetition can be trimmed automatically
- near-duplicate sentence repetition should prefer explicit human comments

For strict repetition, preserve the last surviving copy when it connects naturally into the following valid phrase.

### Cut boundaries

Cuts should land on:

- semantic edges
- acoustic weak points
- natural listening boundaries

Default padding:

- before cut: about `0.03s - 0.08s`
- after cut: about `0.08s - 0.18s`

## Quick start

### English prompt

```text
Please use audiocut-feishu to turn this audio into a commentable Feishu transcript doc.
After I review the doc, I will come back and ask for a v1 or v2 cut.
```

### 中文使用说明

基础模式：

1. 先把原始音频发给 Codex
2. Codex 用本地模型转写，并生成带时间戳的句级文稿
3. Codex 自动把文稿发到飞书文档里
4. 你在飞书文档里评论：
   - `删除`
   - `金句`
5. 你再回到 Codex，要求它输出：
   - `V1 粗剪版`
   - 或 `V2 细剪版`

如果你明确想区分多个说话人，再额外说明：

```text
请生成一个带说话人区分的飞书转写文稿。
```
