#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def fmt(sec: float) -> str:
    mm = int(sec // 60)
    ss = sec - mm * 60
    return f"{mm:02d}:{ss:06.3f}"


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def build_speaker_aliases(turns):
    aliases = {}
    next_index = 0
    for turn in turns:
        speaker = turn["speaker"]
        if speaker not in aliases:
            aliases[speaker] = f"说话人 {chr(ord('A') + next_index)}"
            next_index += 1
    return aliases


def assign_speaker(seg, turns, aliases):
    best = None
    best_overlap = 0.0
    seg_start = float(seg["start"])
    seg_end = float(seg["end"])
    for turn in turns:
        ov = overlap(seg_start, seg_end, float(turn["start"]), float(turn["end"]))
        if ov > best_overlap:
            best_overlap = ov
            best = turn["speaker"]
    if best is None:
        return "说话人 A"
    return aliases[best]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--audio-path", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--diarization-json")
    parser.add_argument("--language")
    args = parser.parse_args()

    transcript = load_json(args.transcript_json)
    diarization = load_json(args.diarization_json) if args.diarization_json else None
    turns = diarization.get("turns", []) if diarization else []
    aliases = build_speaker_aliases(turns) if turns else {}

    lines = []
    lines.append(f"# {args.title}")
    lines.append("")
    lines.append("这是一份由本地 ASR 生成、可直接评论的飞书转写文稿。")
    if turns:
        lines.append("文稿已结合说话人分离结果，按 `说话人 A/B/...` 标注。")
    else:
        lines.append("当前文稿未附带说话人分离结果，默认按单说话人展示。")
    lines.append("建议直接在句子行上评论，例如：`删除`、`金句`、`修改`。")
    lines.append("")
    lines.append("## 基本信息")
    lines.append("")
    lines.append(f"- 音频文件：`{args.audio_path}`")
    lines.append(f"- 识别语言：`{args.language or transcript.get('language', 'unknown')}`")
    lines.append(f"- 音频时长：`{float(transcript.get('duration', 0.0)):.2f}s`")
    if turns:
        lines.append(f"- 说话人数：`{len(aliases)}`")
    lines.append("")
    lines.append("## 句级转写")
    lines.append("")

    for seg in transcript.get("segments", []):
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        idx = int(seg.get("index", 0)) + 1
        if turns:
            speaker = assign_speaker(seg, turns, aliases)
            lines.append(
                f"[{idx:04d}] {speaker} {fmt(float(seg['start']))} - {fmt(float(seg['end']))}"
            )
            lines.append(text)
        else:
            lines.append(f"[{idx:04d}] {fmt(float(seg['start']))} - {fmt(float(seg['end']))}  {text}")
        lines.append("")

    Path(args.output_md).write_text("\n".join(lines), encoding="utf-8")
    print(args.output_md)


if __name__ == "__main__":
    main()
