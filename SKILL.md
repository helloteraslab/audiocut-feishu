---
name: audiocut-feishu
description: Use this skill when the user wants to edit spoken-word audio by generating a high-quality timestamped transcript, publishing that transcript to a Feishu/Lark doc for human comments, and then cutting the source audio from those comments plus optional fine-trim rules.
---

# Audiocut Feishu

This skill is for a transcript-first spoken-audio editing workflow where:

- the user provides a local source audio file
- Codex generates a fine-grained transcript locally
- Codex runs speaker diarization when multiple people are present
- Codex publishes a commentable transcript doc to Feishu/Lark
- the user reviews that doc and comments with edit intent
- Codex returns to the commented doc and performs the cut

## When to use

Use this skill when the user asks to:

- create a commentable Feishu transcript doc from local audio
- create a commentable multi-speaker Feishu transcript doc from local audio
- cut audio from Feishu comments such as `删除` and `金句`
- produce a rough `v1` cut or a finer `v2` cut
- tighten spoken-word pacing by removing long pauses, strict repetitions, and high-confidence filler words

Do not use this skill for:

- music production
- multi-track mixing
- mastering, EQ, or denoising
- precise recreation of Feishu editor UI selection comments via API

## Required inputs

For full mode:

- local audio file path
- working `lark-cli` configuration
- user-authorized Feishu account
- local ASR runtime (`faster-whisper`)
- `pyannote.audio` and a Hugging Face token for multi-speaker diarization

For simplified mode:

- Feishu transcript doc URL
- local audio file path

## Workflow

### Phase 1: Create the transcript doc

1. User gives Codex a local audio file.
2. Codex runs a local Whisper-family ASR model and generates fine-grained timestamps.
3. Codex runs speaker diarization when the audio contains multiple speakers.
4. Codex creates a new Feishu doc and writes the transcript there in a comment-friendly layout.

Preferred transcript layout:

```text
[0001] 说话人 A 00:01.060 - 00:03.960
Hello,这是一个测试文件

[0002] 说话人 B 00:03.960 - 00:08.320
第一步我要测试的关于停顿功能
```

Each sentence should be on its own line so the user can comment directly on that line.

### Phase 2: Human review in Feishu

The user comments in Feishu with labels such as:

- `删除`
- `金句`
- `修改`

The skill is optimized for `删除` and `金句`.

### Phase 3: Edit execution

When the user says review is complete and asks for a cut, ask whether they want:

- `v1` rough cut
- `v2` fine cut

If the user already clearly asks for rough cut / fine cut / `v1` / `v2`, do not ask again.

## Version definitions

### `v1` rough cut

Execute only explicit human comments:

- remove content marked with `删除`
- prepend clips marked with `金句`

Do not apply automatic filler trimming or automatic pause compression in `v1`.

### `v2` fine cut

Start with all `v1` behavior, then additionally apply the editing rules below:

 - compress long pauses
 - remove high-confidence filler / connector words with long air before or after
 - remove strict repetitions

Use the strict repetition helper when available:

- `scripts/run_pyannote_diarization.py`
- `scripts/build_feishu_transcript_doc.py`
- `scripts/detect_strict_repetition.py`
- `scripts/finalize_v2_plan.py`
- `scripts/render_audio_plan_ffmpeg.py`

## Editing rules

### 1. Priority

1. Human Feishu comments override automatic rules.
2. If a segment is ambiguous, preserve it.
3. First decide *what* to cut, then decide *where the cut should land*.

### 2. Long pause rule

A long pause means:

- continuous no-voice region longer than `1.0s`

Default handling:

- keep about `0.30s`
- remove the rest

If a pause appears to carry emotional weight or dramatic timing, be conservative and keep more.

### 3. Filler / connector rule

Common filler candidates:

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

Delete a filler only when all of the following are true:

- it carries little semantic information
- deleting it does not break the sentence backbone
- it has obvious air around it

Suggested high-confidence threshold:

- leading air `>= 0.18s`, or
- trailing air `>= 0.18s`, or
- combined air `>= 0.30s`

Do not delete a filler if it functions as real emphasis, reply logic, or object reference.

### 4. Repetition rule

#### Strict repetition

Examples:

- `明显明显`
- `我我觉得`
- `重复,重复,重复`

Default behavior:

- trim it down to a single surviving copy

Operational rule:

- if a repeated fragment is immediately followed by valid content that reuses the final copy, preserve that final copy and trim only the leading duplicates

Example:

- `重复,重复,重复,重复学习的最好的方法`
  - trim the leading redundant `重复`
  - preserve the last `重复` so the sentence remains `重复学习的最好的方法`

#### Near-duplicate sentence repetition

Examples:

- the same sentence is immediately said again
- the same meaning is restated in a very short time window

Default behavior:

- if human comments explicitly marked it, follow the comment
- otherwise do not automatically delete whole sentences unless confidence is very high

### 5. Cut-boundary rule

Cuts should be decided in three layers:

1. Semantic boundary
   - prefer sentence edges, repetition edges, or filler edges
2. Acoustic boundary
   - prefer weak-energy regions or short silences
3. Listening boundary
   - do not chop off word endings or initials

Default cut padding:

- before a removed fragment: keep about `0.03s - 0.08s`
- after a removed fragment: keep about `0.08s - 0.18s`

If a word ends with a clearly audible tail, favor more post-cut air.

### 6. Quote-prepend rule

For `金句`:

- copy the quote to the beginning
- keep the original body occurrence unless the user says otherwise
- leave a short trailing breath after the prepended quote, usually `0.12s - 0.20s`

## Standard operating sequence

### A. If no transcript doc exists yet

1. Transcribe the audio locally with `faster-whisper`
2. If the audio contains multiple speakers, run diarization with `scripts/run_pyannote_diarization.py`
3. Save a machine-readable timestamp file locally
4. Build the Feishu-ready markdown with `scripts/build_feishu_transcript_doc.py`
5. Create a Feishu doc from the timestamped transcript
6. Give the doc link to the user for comment review

### B. If the user already reviewed the doc

1. Fetch the Feishu doc comments
2. Match comment quotes against the locally generated timestamped transcript
3. Build `intro_ranges` from `金句`
4. Build `delete_ranges` from `删除`
5. If user wants `v2`, add:
   - long-pause compression ranges
   - high-confidence filler trims
   - strict repetition trims from `scripts/detect_strict_repetition.py`
   - merge those repetition trims into the final `delete_ranges` with `scripts/finalize_v2_plan.py`
6. Export the cut
7. Save an edit note

Recommended `v2` merge order:

1. explicit comment deletions
2. long-pause compression
3. high-confidence filler trims
4. strict repetition trims

Apply strict repetition after the comment-driven plan is known, so repeated filler text that survives comments can still be tightened automatically.

Use `scripts/render_audio_plan_ffmpeg.py` for stable `wav` / `mp3` export from the finalized plan.

## Output expectations

Always produce:

- the edited audio file
- a plain-text edit note beside it

The note should include:

- source doc URL
- source audio path
- intro quote ranges
- delete ranges
- whether long-pause compression was applied
- whether filler trimming was applied
- whether any cut was estimated conservatively

## Tooling notes

Recommended local ASR:

- `faster-whisper` with `large-v3-turbo`

Recommended export path:

- prefer `mp3` if a reliable local encoder is available
- otherwise fall back to `wav` and explain why

In the maintained local setup for this skill, `ffmpeg` is available and validated for `mp3` export.

## Known limitations

- Feishu API comment anchoring is weaker than the editor UI for exact text-selection recreation.
- ASR and Feishu text can differ slightly in punctuation, spacing, script style, or wording.
- Fine trimming of short fillers still benefits from conservative thresholds and human review.
