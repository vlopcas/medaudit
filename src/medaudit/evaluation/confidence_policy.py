"""Calibrate a simple retrieval abstention policy without using held-out cases."""

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.private_bm25 import write_private_report


def calibrate_top_score_policy(
    confidence_report: dict[str, Any], *, min_answerable_acceptance: float
) -> dict[str, Any]:
    """Select the safest threshold that satisfies an answerable-coverage floor."""
    if confidence_report.get("schema_version") != 1:
        raise ValueError("unsupported confidence report schema")
    if confidence_report.get("partition") != "calibration":
        raise ValueError("policy calibration requires the calibration partition")
    if not 0 < min_answerable_acceptance <= 1:
        raise ValueError("minimum answerable acceptance must be within zero and one")
    cases = confidence_report.get("cases", [])
    if not cases:
        raise ValueError("at least one calibration case is required")
    answerable_count = sum(bool(case["answerable"]) for case in cases)
    unanswerable_count = len(cases) - answerable_count
    if not answerable_count or not unanswerable_count:
        raise ValueError("calibration requires both answerability classes")

    scores = sorted({float(case["signals"]["top_score"]) for case in cases})
    candidates = [
        _evaluate_threshold(cases, threshold)
        for threshold in scores
    ]
    feasible = [
        candidate
        for candidate in candidates
        if candidate["answerable_acceptance"] >= min_answerable_acceptance
    ]
    if not feasible:
        raise ValueError("no threshold satisfies minimum answerable acceptance")
    selected = max(
        feasible,
        key=lambda candidate: (
            candidate["unanswerable_abstention"],
            candidate["balanced_accuracy"],
            -candidate["threshold"],
        ),
    )
    return {
        "schema_version": 1,
        "status": "frozen",
        "policy": {
            "signal": "top_score",
            "operator": "greater_than_or_equal",
            "threshold": selected["threshold"],
            "min_answerable_acceptance": min_answerable_acceptance,
        },
        "calibration": {
            "case_count": len(cases),
            "answerable_case_count": answerable_count,
            "unanswerable_case_count": unanswerable_count,
            "selected_metrics": {
                key: value for key, value in selected.items() if key != "threshold"
            },
            "candidate_threshold_count": len(candidates),
            "source_sha256": _canonical_hash(confidence_report),
        },
    }


def _evaluate_threshold(
    cases: list[dict[str, Any]], threshold: float
) -> dict[str, float]:
    answerable = [case for case in cases if case["answerable"]]
    unanswerable = [case for case in cases if not case["answerable"]]
    accepted_answerable = sum(
        float(case["signals"]["top_score"]) >= threshold for case in answerable
    )
    abstained_unanswerable = sum(
        float(case["signals"]["top_score"]) < threshold for case in unanswerable
    )
    acceptance = accepted_answerable / len(answerable)
    abstention = abstained_unanswerable / len(unanswerable)
    return {
        "threshold": threshold,
        "answerable_acceptance": acceptance,
        "unanswerable_abstention": abstention,
        "balanced_accuracy": (acceptance + abstention) / 2,
    }


def _canonical_hash(payload: dict[str, Any]) -> str:
    rendered = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(rendered.encode()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-answerable-acceptance", type=float, default=0.8)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        confidence: dict[str, Any] = json.loads(
            args.confidence.read_text(encoding="utf-8")
        )
        result = calibrate_top_score_policy(
            confidence,
            min_answerable_acceptance=args.min_answerable_acceptance,
        )
        write_private_report(result, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "policy": result["policy"],
                "selected_metrics": result["calibration"]["selected_metrics"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
