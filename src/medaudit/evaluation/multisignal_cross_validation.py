"""Cross-validate multisignal abstention within the calibration partition."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.multisignal_policy import cross_validate_multisignal_policy
from medaudit.evaluation.private_bm25 import write_private_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-answerable-acceptance", type=float, default=0.8)
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument("--seed", default="medaudit-multisignal-cv-v1")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        confidence: dict[str, Any] = json.loads(
            args.confidence.read_text(encoding="utf-8")
        )
        report = cross_validate_multisignal_policy(
            confidence,
            min_answerable_acceptance=args.min_answerable_acceptance,
            fold_count=args.fold_count,
            seed=args.seed,
        )
        write_private_report(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "case_count": report["case_count"],
                "fold_count": report["fold_count"],
                "metrics": report["metrics"],
                "partition": report["partition"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
