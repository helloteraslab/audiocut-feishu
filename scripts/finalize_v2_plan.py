#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def merge_delete_ranges(ranges):
    normalized = []
    for item in ranges:
        start = float(item["start"])
        end = float(item["end"])
        if end <= start:
            continue
        normalized.append(
            {
                "start": start,
                "end": end,
                "reasons": list(item.get("reasons", [])) or [item.get("reason", "unspecified")],
            }
        )

    if not normalized:
        return []

    normalized.sort(key=lambda x: (x["start"], x["end"]))
    merged = [normalized[0]]
    for current in normalized[1:]:
        prev = merged[-1]
        if current["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], current["end"])
            for reason in current["reasons"]:
                if reason not in prev["reasons"]:
                    prev["reasons"].append(reason)
        else:
            merged.append(current)
    return merged


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-plan-json", required=True)
    parser.add_argument("--strict-repetition-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--source-duration-sec", type=float)
    args = parser.parse_args()

    base_plan = load_json(args.base_plan_json)
    repetition_payload = load_json(args.strict_repetition_json)

    strict_ranges = []
    for item in repetition_payload.get("strict_repetition_ranges", []):
        strict_ranges.append(
            {
                "start": item["start"],
                "end": item["end"],
                "reasons": [
                    f"strict repetition: {item.get('segment_text', '').strip() or item.get('reason', 'trim leading duplicates')}"
                ],
            }
        )

    base_plan["strict_repetition_ranges"] = strict_ranges
    base_plan["delete_ranges"] = merge_delete_ranges(base_plan.get("delete_ranges", []) + strict_ranges)
    if args.source_duration_sec is not None:
        base_plan["source_duration_sec"] = args.source_duration_sec

    Path(args.output_json).write_text(json.dumps(base_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output_json)
    print("strict_ranges=", len(strict_ranges))
    print("delete_ranges=", len(base_plan["delete_ranges"]))


if __name__ == "__main__":
    main()
