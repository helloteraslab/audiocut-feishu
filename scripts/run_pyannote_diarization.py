#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


def fail(message: str, code: int = 1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--token-env", default="HF_TOKEN")
    parser.add_argument("--pipeline-name", default="pyannote/speaker-diarization-community-1")
    parser.add_argument("--num-speakers", type=int)
    parser.add_argument("--min-speakers", type=int)
    parser.add_argument("--max-speakers", type=int)
    args = parser.parse_args()

    token = os.getenv(args.token_env) or os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        fail(
            f"Missing Hugging Face token. Set {args.token_env} or HUGGINGFACE_TOKEN before running diarization."
        )

    try:
        from pyannote.audio import Pipeline
    except Exception as exc:  # pragma: no cover - environment dependent
        fail(
            "pyannote.audio is not installed in the current Python environment. "
            "Install it with `pip install pyannote.audio` first.\n"
            f"Original import error: {exc}"
        )

    pipeline = Pipeline.from_pretrained(args.pipeline_name, token=token)

    kwargs = {}
    if args.num_speakers is not None:
        kwargs["num_speakers"] = args.num_speakers
    if args.min_speakers is not None:
        kwargs["min_speakers"] = args.min_speakers
    if args.max_speakers is not None:
        kwargs["max_speakers"] = args.max_speakers

    diarization = pipeline(args.audio, **kwargs)
    exclusive = getattr(diarization, "exclusive_speaker_diarization", None)

    turns = []
    speaker_order = []
    seen_speakers = set()

    track_source = exclusive if exclusive is not None else diarization
    for turn, _, speaker in track_source.itertracks(yield_label=True):
        turns.append(
            {
                "start": round(float(turn.start), 3),
                "end": round(float(turn.end), 3),
                "speaker": speaker,
            }
        )
        if speaker not in seen_speakers:
            seen_speakers.add(speaker)
            speaker_order.append(speaker)

    payload = {
        "audio": args.audio,
        "pipeline_name": args.pipeline_name,
        "exclusive": exclusive is not None,
        "speakers": speaker_order,
        "turns": turns,
    }
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output_json)
    print("speakers=", len(speaker_order))
    print("turns=", len(turns))


if __name__ == "__main__":
    main()
