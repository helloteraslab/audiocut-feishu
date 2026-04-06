#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


PUNCT_RE = re.compile(r"[，,。.!！?？、；;：“”\"'‘’（）()\[\]\-—\s]+")


def normalize_token(text: str) -> str:
    return PUNCT_RE.sub("", text).lower()


def load_words(transcript_json: Path):
    data = json.loads(transcript_json.read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    rows = []
    for seg in segments:
        for word in seg.get("words", []):
            norm = normalize_token(word.get("word", ""))
            if not norm:
                continue
            rows.append(
                {
                    "segment_index": seg.get("index"),
                    "segment_start": seg.get("start"),
                    "segment_end": seg.get("end"),
                    "segment_text": seg.get("text", "").strip(),
                    "start": word.get("start"),
                    "end": word.get("end"),
                    "raw": word.get("word", ""),
                    "norm": norm,
                }
            )
    return rows


def phrases_match(words, a_start: int, b_start: int, phrase_len: int, max_gap: float) -> bool:
    if b_start + phrase_len > len(words):
        return False
    left = words[a_start : a_start + phrase_len]
    right = words[b_start : b_start + phrase_len]
    if [w["norm"] for w in left] != [w["norm"] for w in right]:
        return False
    if left[-1]["end"] is None or right[0]["start"] is None:
        return False
    return right[0]["start"] - left[-1]["end"] <= max_gap


def detect_strict_repetitions(words, max_gap: float, min_run: int, max_phrase_len: int = 3):
    results = []
    by_segment = {}
    for word in words:
        by_segment.setdefault(word["segment_index"], []).append(word)

    for segment_words in by_segment.values():
        i = 0
        while i < len(segment_words):
            best = None
            for phrase_len in range(max_phrase_len, 0, -1):
                if i + phrase_len * 2 > len(segment_words):
                    continue
                phrase = segment_words[i : i + phrase_len]
                char_len = sum(len(w["norm"]) for w in phrase)
                if phrase_len == 1 and char_len < 2:
                    # Avoid false positives like "拜拜" where a single Chinese
                    # character appears twice but forms one natural word.
                    continue

                repeats = 1
                while phrases_match(
                    segment_words,
                    i + (repeats - 1) * phrase_len,
                    i + repeats * phrase_len,
                    phrase_len,
                    max_gap,
                ):
                    repeats += 1
                if repeats >= min_run:
                    coverage = repeats * phrase_len
                    best = (phrase_len, repeats, coverage)
                    break

            if best is None:
                i += 1
                continue

            phrase_len, repeats, coverage = best
            run_words = segment_words[i : i + coverage]
            keep_start_index = i + (repeats - 1) * phrase_len
            delete_start = run_words[0]["start"]
            delete_until = segment_words[keep_start_index]["start"]
            phrase_text = "".join(w["raw"] for w in segment_words[i : i + phrase_len])
            if delete_start is not None and delete_until is not None and delete_until > delete_start:
                results.append(
                    {
                        "start": delete_start,
                        "end": delete_until,
                        "token": phrase_text,
                        "count": repeats,
                        "matched_words": [w["raw"] for w in run_words],
                        "segment_index": run_words[0]["segment_index"],
                        "segment_text": run_words[0]["segment_text"],
                        "reason": f"strict repetition: keep final '{phrase_text}' and trim leading duplicates",
                    }
                )
            i += coverage
    return results


def merge_ranges(ranges):
    if not ranges:
        return []
    ranges = sorted(ranges, key=lambda x: (x["start"], x["end"]))
    merged = [ranges[0].copy()]
    for cur in ranges[1:]:
        prev = merged[-1]
        if cur["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], cur["end"])
            prev.setdefault("reasons", [prev["reason"]])
            prev["reasons"].append(cur["reason"])
            prev.setdefault("tokens", [prev["token"]])
            prev["tokens"].append(cur["token"])
        else:
            merged.append(cur.copy())
    for item in merged:
        item.setdefault("reasons", [item["reason"]])
        item.setdefault("tokens", [item["token"]])
    return merged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--max-gap", type=float, default=0.35)
    parser.add_argument("--min-run", type=int, default=2)
    args = parser.parse_args()

    words = load_words(Path(args.transcript_json))
    ranges = detect_strict_repetitions(words, max_gap=args.max_gap, min_run=args.min_run)
    merged = merge_ranges(ranges)

    payload = {
        "transcript_json": args.transcript_json,
        "max_gap": args.max_gap,
        "min_run": args.min_run,
        "strict_repetition_ranges": merged,
    }
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(args.output_json)
    print("ranges=", len(merged))
    for item in merged:
        print(f"{item['start']:.3f}-{item['end']:.3f}\t{','.join(item['tokens'])}\t{item['segment_text']}")


if __name__ == "__main__":
    main()
