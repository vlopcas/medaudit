"""Profile private chunk JSONL using aggregate, content-free statistics."""

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path
from statistics import mean
from typing import Any


def profile_chunks(source: Path) -> dict[str, Any]:
    """Measure chunk volume and sizes without retaining or returning text."""
    lengths: list[int] = []
    by_media_type: Counter[str] = Counter()
    by_strategy: Counter[str] = Counter()
    media_lengths: defaultdict[str, list[int]] = defaultdict(list)
    with_page = 0
    with_section = 0

    with source.open(encoding="utf-8") as records:
        for line in records:
            payload = json.loads(line)
            if payload.get("schema_version") != 1:
                raise ValueError("unsupported chunk schema")
            chunk = payload["chunk"]
            document = payload["document"]
            length = len(chunk["text"])
            media_type = document.get("media_type", "unknown")
            strategy = chunk.get("metadata", {}).get("strategy", "unknown")
            lengths.append(length)
            media_lengths[media_type].append(length)
            by_media_type[media_type] += 1
            by_strategy[strategy] += 1
            with_page += chunk.get("page") is not None
            with_section += chunk.get("section") is not None

    return {
        "schema_version": 1,
        "chunk_count": len(lengths),
        "total_characters": sum(lengths),
        "length_characters": _distribution(lengths),
        "chunks_by_media_type": dict(sorted(by_media_type.items())),
        "length_by_media_type": {
            media_type: _distribution(values)
            for media_type, values in sorted(media_lengths.items())
        },
        "chunks_by_strategy": dict(sorted(by_strategy.items())),
        "chunks_with_page": with_page,
        "chunks_with_section": with_section,
    }


def _distribution(values: list[int]) -> dict[str, int | float]:
    if not values:
        return {"min": 0, "mean": 0.0, "p50": 0, "p95": 0, "max": 0}
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "mean": round(mean(ordered), 2),
        "p50": _percentile(ordered, 0.50),
        "p95": _percentile(ordered, 0.95),
        "max": ordered[-1],
    }


def _percentile(ordered: list[int], fraction: float) -> int:
    index = max(0, int(len(ordered) * fraction + 0.999999) - 1)
    return ordered[index]


def write_chunk_profile(report: dict[str, Any], output: Path) -> None:
    """Atomically write aggregate statistics to an ignored local report."""
    if not output.name.endswith(".local.json"):
        raise ValueError("chunk profile output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Write and print aggregate statistics only."""
    args = build_parser().parse_args(argv)
    try:
        report = profile_chunks(args.input)
        write_chunk_profile(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
