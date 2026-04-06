#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


TARGET_RATE = 44100
TARGET_LAYOUT = "stereo"


def load_plan(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compute_keep_ranges(duration: float, delete_ranges):
    keep = []
    cursor = 0.0
    for item in sorted(delete_ranges, key=lambda x: (x["start"], x["end"])):
        start = max(0.0, float(item["start"]))
        end = min(duration, float(item["end"]))
        if start > cursor:
            keep.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < duration:
        keep.append((cursor, duration))
    return keep


def build_filter(plan):
    duration = float(plan["source_duration_sec"])
    delete_ranges = plan.get("delete_ranges", [])
    intro_ranges = plan.get("intro_ranges", [])
    intro_tail = float(plan.get("intro_tail_silence_sec", 0.0) or 0.0)
    keep_ranges = compute_keep_ranges(duration, delete_ranges)

    parts = []
    labels = []
    stream_index = 0

    for item in intro_ranges:
        label = f"s{stream_index}"
        stream_index += 1
        parts.append(
            f"[0:a]atrim=start={float(item['start']):.6f}:end={float(item['end']):.6f},"
            f"asetpts=PTS-STARTPTS,"
            f"aformat=sample_fmts=s16:sample_rates={TARGET_RATE}:channel_layouts={TARGET_LAYOUT}"
            f"[{label}]"
        )
        labels.append(f"[{label}]")

    if intro_ranges and intro_tail > 0:
        label = f"s{stream_index}"
        stream_index += 1
        parts.append(
            f"anullsrc=r={TARGET_RATE}:cl={TARGET_LAYOUT},atrim=duration={intro_tail:.6f}"
            f"[{label}]"
        )
        labels.append(f"[{label}]")

    for start, end in keep_ranges:
        label = f"s{stream_index}"
        stream_index += 1
        parts.append(
            f"[0:a]atrim=start={start:.6f}:end={end:.6f},"
            f"asetpts=PTS-STARTPTS,"
            f"aformat=sample_fmts=s16:sample_rates={TARGET_RATE}:channel_layouts={TARGET_LAYOUT}"
            f"[{label}]"
        )
        labels.append(f"[{label}]")

    concat_label = f"s{stream_index}"
    parts.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[{concat_label}]")
    return ";".join(parts), concat_label


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--output-wav", required=True)
    parser.add_argument("--output-mp3")
    parser.add_argument("--ffmpeg-bin", required=True)
    args = parser.parse_args()

    plan = load_plan(args.plan_json)
    filter_complex, final_label = build_filter(plan)

    input_path = plan["input"]
    output_wav = Path(args.output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    wav_cmd = [
        args.ffmpeg_bin,
        "-y",
        "-i",
        input_path,
        "-filter_complex",
        filter_complex,
        "-map",
        f"[{final_label}]",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    run(wav_cmd)

    if args.output_mp3:
        run(
            [
                args.ffmpeg_bin,
                "-y",
                "-i",
                str(output_wav),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                args.output_mp3,
            ]
        )


if __name__ == "__main__":
    main()
