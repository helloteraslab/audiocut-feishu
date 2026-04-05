---
name: audiocut-tera
description: Use this skill when the user wants to edit a podcast or spoken-word audio file by combining a Feishu/Lark transcript document with the original audio file. This skill is for workflows that read Feishu doc content and comments via lark-cli, map transcript timestamps back to audio, prepend highlighted quote segments, remove delete-marked segments, and optionally do aggressive pause compression based on waveform-detected silences.
---

# Audiocut Tera

This skill is for a podcast-editing workflow where:

- source audio is a local file, usually MP3
- transcript lives in a Feishu/Lark doc
- comments such as `删除` and `金句` act as edit instructions
- output is one or more edited `m4a` versions plus a short edit note

## When to use

Use this skill when the user asks to:

- cut a podcast from a Feishu transcript doc
- prepend `金句` clips to the beginning
- delete `删除` clips from the body
- tighten pacing by compressing long pauses
- produce multiple edit passes such as `v1`, `v2`, `v3`

Do not use this skill for:

- musical editing
- multi-track mixing
- noise reduction / EQ / mastering
- precise in-doc comment authoring via Feishu UI selection ranges

## What is already proven to work

This workflow has already been validated locally:

1. Read Feishu doc content with `lark-cli docs +fetch`
2. Read Feishu comments with `lark-cli api GET /open-apis/drive/v1/files/<token>/comments`
3. Map comment quotes back to transcript timestamps
4. Export edited audio locally with Swift + `AVFoundation`
5. Analyze long silences from the original audio waveform
6. Generate tighter edit passes by combining:
   - explicit delete ranges
   - quote-prepend ranges
   - silence-compression ranges

## Important limitation

Feishu's open API does not reliably support the same precise "hand-selected text comment" behavior as the editor UI for this long transcript format.

You may be able to create block-anchored comments, but do not assume you can accurately recreate the user's exact in-document text selection. If precision matters, prefer:

- reading existing comments from the doc
- reporting suggested new cuts in plain text
- proceeding with audio editing directly

## Inputs you need

- Feishu doc URL
- local audio file path
- user intent:
  - comment-driven cut
  - pause compression
  - quote-first cold open
  - conservative or aggressive pacing

## Standard workflow

### 1. Fetch transcript and comments

Run:

```bash
export PATH="$HOME/.local/node/bin:$PATH"
lark-cli docs +fetch --doc '<DOC_URL>' --format json
lark-cli api GET /open-apis/drive/v1/files/<DOC_TOKEN>/comments --params '{"file_type":"docx","page_size":100}'
```

Persist them locally if you need repeatable processing.

### 2. Extract timestamped utterances

The transcript format uses lines like:

```text
说话人 1 04:40
```

Parse `MM:SS` and treat each speaker block as an utterance span until the next timestamp.

Use this to:

- locate `删除` comment quotes
- locate `金句` comment quotes
- estimate subranges inside long utterances

### 3. Build explicit ranges

Create three classes of ranges:

- `intro_ranges`
  - quote-worthy clips to prepend at the beginning
- `delete_ranges`
  - explicit removals from comments or user instructions
- `silence_ranges`
  - the removable tail of long pauses

For aggressive versions:

- detect waveform silences longer than 1 second
- keep roughly 0.3 seconds of each long pause
- remove the rest

For conservative versions:

- keep more pause, usually 0.5 to 0.8 seconds

### 4. Export the edit

Use the bundled scripts:

- [`compose_audio.swift`](scripts/compose_audio.swift)
- [`analyze_silence.swift`](scripts/analyze_silence.swift)

Typical export pattern:

```bash
swift scripts/compose_audio.swift '<INPUT>' '<OUTPUT>' '<INTRO_RANGES>' '<DELETE_RANGES>'
```

Range syntax is:

```text
start1:end1,start2:end2,start3:end3
```

in seconds.

### 5. Produce versions

Recommended naming:

- `_去掉开头试录`
- `_按飞书评论`
- `_v2`
- `_v3`

Use `v2` for additional manual tightening. Use `v3` for aggressive pause compression.

### 6. Write a short edit note

Always save a plain-text note beside the output file that includes:

- prepended quote ranges
- deleted ranges
- whether pause compression was applied
- whether timing inside long utterances was estimated

## Heuristics

### Good `删除` candidates

- obvious false starts
- setup chatter before the real opening
- repeated question setup
- "等一下", "我查一下", "我那个飞书哪去了"
- bodily interruption / recording interruption
- repeated filler with long air before and after

### Good `金句` candidates

- strong thesis statements
- emotionally vivid lines
- concise worldview lines
- clips that still work when heard before the main body

Avoid quote-prepending clips that need too much context.

## Scripts

### `scripts/analyze_silence.swift`

Detects long silences from the source audio and prints:

```text
start_seconds<TAB>end_seconds<TAB>duration_seconds
```

### `scripts/compose_audio.swift`

Builds a new audio file by:

1. prepending `intro_ranges`
2. appending the source body with `delete_ranges` removed

The output format is `m4a`.

## Validation

After export:

- check file exists
- run `afinfo '<OUTPUT>'`
- compare duration against the prior version
- summarize what changed

## Default behavior

If the user asks for a more polished podcast cut and does not specify otherwise:

- preserve `金句` cold open
- remove explicit `删除` ranges
- do one additional tightening pass on obvious interruptions
- compress long pauses only if the user asks for a more aggressive edit

