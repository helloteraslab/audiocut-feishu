# audiocut-tera

`audiocut-tera` is a Codex skill for editing podcast and other spoken-word audio from a Feishu/Lark transcript plus the original source file.

It is built for workflows where:

- the transcript lives in a Feishu/Lark doc
- existing comments such as `删除` and `金句` represent edit intent
- the source audio is local
- the desired output is one or more polished `m4a` cuts

Typical outputs include:

- `v1`: remove false starts and obvious junk
- `v2`: remove interruptions, filler segments, and awkward long pauses
- `v3`: aggressively tighten pacing by compressing long silences

## What this skill can do

This skill helps Codex:

1. Read a Feishu/Lark transcript document with `lark-cli`
2. Read existing Feishu comments from that document
3. Map timestamped transcript text back to the source audio
4. Prepend `金句` clips as a cold open
5. Remove `删除` clips from the main body
6. Detect long silence ranges from the waveform
7. Export edited `m4a` files and a short edit note

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
- EQ, compression, or mastering
- denoising or audio restoration

## Requirements

Before using this skill, make sure you have:

- Codex with local skill support
- `lark-cli` installed and authorized
- access to the Feishu/Lark transcript doc
- a local source audio file
- macOS with `swift` and `AVFoundation`

This repository assumes the editing machine can run Swift scripts locally.

## Install

Install directly from GitHub:

```bash
npx skills add https://github.com/helloteraslab/audiocut-feishu -y -g
```

## Quick start

Ask Codex something like:

```text
Please use audiocut-tera to edit this podcast using the Feishu transcript doc and the original local audio file.
```

Or more specifically:

```text
Use audiocut-tera. Read the Feishu doc, prepend all 金句 comments, remove all 删除 comments, and make an aggressive v3 cut.
```

## 中文使用说明

这个 skill 最适合这样的场景：

- 你已经有一份飞书转写文稿
- 文稿里最好已经有人加了 `删除` 或 `金句` 评论
- 你手上还有对应的原始音频文件

用户在调用这个 skill 时，通常需要提供：

1. 飞书文稿链接
2. 原始音频文件路径
3. 你希望输出什么版本
   - 例如：基础清理版、`v2` 精修版、`v3` 激进压缩版

如果只有文稿，没有音频，这个 skill 只能帮你分析和建议剪辑点，不能真正导出成片。

如果只有音频，没有文稿，这个 skill 只能做静音压缩或部分节奏优化，不能完整利用 `删除` / `金句` 这类评论驱动剪辑。

## 中文提示词模板

你可以直接把下面这段发给 Codex：

```text
请使用 audiocut-tera 帮我剪辑这期播客。

飞书文稿链接：
<在这里粘贴飞书文稿链接>

原始音频文件路径：
<在这里粘贴本地音频文件路径>

剪辑要求：
1. 读取文稿中的 删除 和 金句 评论
2. 把所有 金句 片段复制并放到开头
3. 删除所有 删除 片段
4. 再做一版 v2 精修 / v3 激进压缩（按你的需要二选一）
5. 输出成片音频，并附一份编辑说明
```

如果你想写得更短，也可以直接说：

```text
请使用 audiocut-tera，基于这个飞书文稿和原始音频，输出一版 v3 播客成片。
```

## Recommended workflow

1. Prepare a Feishu transcript doc with speaker timestamps such as `说话人 1 04:40`
2. Add comments such as:
   - `删除`
   - `金句`
3. Provide the original local audio path
4. Let Codex fetch the doc and comments
5. Generate one or more edited versions

## Repository structure

```text
audiocut-feishu/
├── README.md
├── SKILL.md
└── scripts/
    ├── analyze_silence.swift
    └── compose_audio.swift
```

## Scripts

### `scripts/analyze_silence.swift`

Analyzes the source audio and prints long silence ranges:

```text
start_seconds<TAB>end_seconds<TAB>duration_seconds
```

Useful for aggressive edits where pauses longer than 1 second should be shortened.

### `scripts/compose_audio.swift`

Builds a new audio file by:

- prepending selected quote ranges
- removing selected delete ranges from the body

Example:

```bash
swift scripts/compose_audio.swift '<INPUT>' '<OUTPUT>' '<INTRO_RANGES>' '<DELETE_RANGES>'
```

Where ranges are passed as:

```text
12.0:18.5,65.2:71.0
```

## Known limitation

Feishu's public API does not reliably reproduce the same fine-grained text selection behavior available in the editor UI for long transcript blocks.

In practice this means:

- reading existing comments works well
- writing new comments with exact selection precision is not reliably supported

So this skill is best used for:

- reading and acting on existing review comments
- generating audio edits directly
- suggesting new cut points in plain text when needed

## Privacy notes

This repository contains only:

- the Codex skill definition
- two Swift helper scripts

It does **not** need to include:

- source audio files
- transcript exports
- private Feishu document URLs
- local machine paths

## Publishing

To publish your own copy:

1. Create a GitHub repository
2. Push this directory as the repository contents
3. Test installation using `npx skills add`
4. Share the repository URL
