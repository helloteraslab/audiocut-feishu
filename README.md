# audiocut-tera

`audiocut-tera` is a Codex skill for editing podcast or spoken-word audio by combining:

- a Feishu/Lark transcript document
- existing document comments such as `删除` and `金句`
- the original local audio file

It is designed for workflows where you want to turn a rough spoken recording into cleaner podcast cuts such as:

- `v1`: remove obvious false starts
- `v2`: remove interruptions, long filler sections, and awkward pauses
- `v3`: aggressively compress pauses for a tighter, more produced result

## What this skill does

This skill helps Codex:

1. Read a Feishu transcript document with `lark-cli`
2. Read existing Feishu comments from that document
3. Map timestamped transcript text back to the source audio
4. Prepend `金句` clips to the beginning as a cold open
5. Remove `删除` clips from the main body
6. Optionally detect and compress long pauses from the waveform
7. Export edited `m4a` outputs and a short edit note

## Repository structure

```text
audiocut-tera/
├── README.md
├── SKILL.md
└── scripts/
    ├── analyze_silence.swift
    └── compose_audio.swift
```

## Requirements

Before using this skill, make sure you have:

- Codex with local skill support
- `lark-cli` installed and authorized
- access to the Feishu/Lark transcript doc
- a local source audio file
- macOS with `swift` and `AVFoundation`

This repository assumes the editing machine can run Swift scripts locally.

## Install

If this repository is public on GitHub, install it with:

```bash
npx skills add <YOUR_GITHUB_REPO_URL> -y -g
```

Example:

```bash
npx skills add https://github.com/<your-name>/audiocut-tera -y -g
```

## Typical usage

Ask Codex something like:

```text
Please use audiocut-tera to edit this podcast using the Feishu transcript doc and the original MP3.
```

Or more specifically:

```text
Use audiocut-tera. Read the Feishu doc, prepend all 金句 comments, remove all 删除 comments, and make an aggressive v3 cut.
```

## Recommended workflow

1. Prepare a Feishu transcript doc with speaker timestamps like `说话人 1 04:40`
2. Add comment markers such as:
   - `删除`
   - `金句`
3. Provide the original local audio path
4. Let Codex fetch the doc and comments
5. Generate one or more edited versions

## Scripts included

### `scripts/analyze_silence.swift`

Analyzes the source audio and prints long silence ranges:

```text
start_seconds<TAB>end_seconds<TAB>duration_seconds
```

This is useful for aggressive edits where pauses longer than 1 second should be shortened.

### `scripts/compose_audio.swift`

Builds a new audio file by:

- prepending selected quote ranges
- removing selected delete ranges from the body

Example shape:

```bash
swift scripts/compose_audio.swift '<INPUT>' '<OUTPUT>' '<INTRO_RANGES>' '<DELETE_RANGES>'
```

Where the ranges are passed as:

```text
12.0:18.5,65.2:71.0
```

## Known limitation

Feishu's public API does not reliably recreate the same fine-grained "selected text comment" behavior available in the editor UI for this kind of long transcript block.

This means:

- reading existing comments works well
- writing new comments with exact selection precision is not reliably supported

So this skill is best used for:

- reading and acting on existing review comments
- generating audio edits directly
- suggesting new cut points in plain text when needed

## Good fit

Use this skill when editing:

- podcasts
- interview recordings
- spoken essays
- transcript-first voice content

## Not a good fit

This skill is not intended for:

- music production
- multitrack editing
- EQ, compression, or mastering
- denoising or audio restoration

## Publishing notes

If you want to share this skill publicly:

1. Create a GitHub repository
2. Push this directory as the repository contents
3. Test installation from the GitHub URL using `npx skills add`
4. Share the repository URL

