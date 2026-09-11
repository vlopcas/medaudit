"""Profile private chunk lengths with the pinned embedding tokenizer."""

import argparse
import json
import math
from collections.abc import Sequence
from pathlib import Path
from statistics import mean
from typing import Any

from medaudit.evaluation.private_bm25 import write_private_report
from medaudit.retrieval import E5Embedder
from medaudit.retrieval.embedding_cache import load_unique_snapshot_chunks
from medaudit.retrieval.local_model import MODEL_ID, MODEL_REVISION


def summarize_token_lengths(lengths: list[int], maximum: int) -> dict[str, Any]:
    """Summarize tokenizer lengths without retaining private text."""
    if not lengths or any(length <= 0 for length in lengths):
        raise ValueError("token lengths must be positive and non-empty")
    if maximum <= 0:
        raise ValueError("maximum sequence length must be positive")
    ordered = sorted(lengths)
    truncated = sum(length > maximum for length in lengths)
    return {
        "schema_version": 1,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "chunk_count": len(lengths),
        "maximum_sequence_tokens": maximum,
        "length_tokens": {
            "min": ordered[0],
            "p50": _percentile(ordered, 0.50),
            "p95": _percentile(ordered, 0.95),
            "p99": _percentile(ordered, 0.99),
            "max": ordered[-1],
            "mean": mean(ordered),
        },
        "truncated_chunk_count": truncated,
        "truncated_chunk_rate": truncated / len(lengths),
    }


def _percentile(ordered: list[int], fraction: float) -> int:
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--model-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=256)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        chunks, snapshot_count = load_unique_snapshot_chunks(args.snapshots)
        lengths, maximum = E5Embedder(args.model_cache).passage_token_lengths(
            [chunk.text for chunk in chunks], batch_size=args.batch_size
        )
        report = summarize_token_lengths(lengths, maximum)
        report["snapshot_count"] = snapshot_count
        write_private_report(report, args.output)
    except (
        ImportError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "chunk_count": report["chunk_count"],
                "maximum_sequence_tokens": report["maximum_sequence_tokens"],
                "snapshot_count": report["snapshot_count"],
                "succeeded": True,
                "truncated_chunk_count": report["truncated_chunk_count"],
                "truncated_chunk_rate": report["truncated_chunk_rate"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
