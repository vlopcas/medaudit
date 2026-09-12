"""Calibrate a conservative one- or two-signal abstention policy."""

import argparse
import hashlib
import itertools
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.confidence_policy import canonical_hash
from medaudit.evaluation.private_bm25 import write_private_report

SIGNALS = (
    "top_score",
    "normalized_margin",
    "query_coverage",
    "rare_query_coverage",
)


def cross_validate_multisignal_policy(
    confidence_report: dict[str, Any],
    *,
    min_answerable_acceptance: float,
    fold_count: int = 5,
    seed: str = "medaudit-multisignal-cv-v1",
) -> dict[str, Any]:
    """Estimate policy stability using stratified folds inside calibration."""
    cases = confidence_report.get("cases", [])
    if confidence_report.get("partition") != "calibration":
        raise ValueError("cross-validation requires the calibration partition")
    if fold_count < 2:
        raise ValueError("cross-validation requires at least two folds")
    if not seed.strip():
        raise ValueError("cross-validation seed must not be empty")
    identifiers = [case["case_id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate calibration case id")
    strata = {
        True: [case for case in cases if case["answerable"]],
        False: [case for case in cases if not case["answerable"]],
    }
    if any(len(items) < fold_count for items in strata.values()):
        raise ValueError("each answerability class must cover every fold")
    fold_ids: list[set[str]] = [set() for _ in range(fold_count)]
    for items in strata.values():
        ranked = sorted(
            items,
            key=lambda case: hashlib.sha256(
                f"{seed}\0{case['case_id']}".encode()
            ).hexdigest(),
        )
        for index, case in enumerate(ranked):
            fold_ids[index % fold_count].add(case["case_id"])

    folds: list[dict[str, Any]] = []
    all_predictions: list[tuple[bool, bool]] = []
    for index, validation_ids in enumerate(fold_ids):
        training = [case for case in cases if case["case_id"] not in validation_ids]
        validation = [case for case in cases if case["case_id"] in validation_ids]
        training_report = {
            "schema_version": 1,
            "partition": "calibration",
            "cases": training,
        }
        candidate = calibrate_multisignal_policy(
            training_report,
            min_answerable_acceptance=min_answerable_acceptance,
        )
        conditions = candidate["policy"]["conditions"]
        predictions = [
            (bool(case["answerable"]), _accepts(case, conditions))
            for case in validation
        ]
        all_predictions.extend(predictions)
        folds.append(
            {
                "fold": index,
                "training_case_count": len(training),
                "validation_case_count": len(validation),
                "condition_count": len(conditions),
                "metrics": _prediction_metrics(predictions),
            }
        )
    return {
        "schema_version": 1,
        "partition": "calibration",
        "strategy": "sha256-stratified-k-fold-v1",
        "seed": seed,
        "fold_count": fold_count,
        "case_count": len(cases),
        "metrics": _prediction_metrics(all_predictions),
        "folds": folds,
        "source_sha256": canonical_hash(confidence_report),
    }


def calibrate_multisignal_policy(
    confidence_report: dict[str, Any], *, min_answerable_acceptance: float
) -> dict[str, Any]:
    """Select the simplest conjunction that maximizes safe abstention."""
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

    thresholds = {
        signal: sorted({float(case["signals"][signal]) for case in cases})
        for signal in SIGNALS
    }
    candidates: list[dict[str, Any]] = []
    for signal in SIGNALS:
        candidates.extend(
            _evaluate(cases, [(signal, threshold)])
            for threshold in thresholds[signal]
        )
    for first, second in itertools.combinations(SIGNALS, 2):
        candidates.extend(
            _evaluate(cases, [(first, left), (second, right)])
            for left in thresholds[first]
            for right in thresholds[second]
        )
    feasible = [
        candidate
        for candidate in candidates
        if candidate["answerable_acceptance"] >= min_answerable_acceptance
    ]
    if not feasible:
        raise ValueError("no rule satisfies minimum answerable acceptance")
    selected = max(
        feasible,
        key=lambda candidate: (
            candidate["unanswerable_abstention"],
            candidate["balanced_accuracy"],
            -len(candidate["conditions"]),
            json.dumps(candidate["conditions"], sort_keys=True),
        ),
    )
    return {
        "schema_version": 1,
        "status": "candidate",
        "policy": {
            "operator": "all",
            "conditions": selected["conditions"],
            "min_answerable_acceptance": min_answerable_acceptance,
        },
        "calibration": {
            "case_count": len(cases),
            "answerable_case_count": answerable_count,
            "unanswerable_case_count": unanswerable_count,
            "selected_metrics": {
                "answerable_acceptance": selected["answerable_acceptance"],
                "unanswerable_abstention": selected["unanswerable_abstention"],
                "balanced_accuracy": selected["balanced_accuracy"],
            },
            "candidate_rule_count": len(candidates),
            "maximum_condition_count": 2,
            "source_sha256": canonical_hash(confidence_report),
        },
    }


def _evaluate(
    cases: list[dict[str, Any]], conditions: list[tuple[str, float]]
) -> dict[str, Any]:
    serialized = [
        {
            "signal": signal,
            "operator": "greater_than_or_equal",
            "threshold": threshold,
        }
        for signal, threshold in conditions
    ]
    predictions = [
        (bool(case["answerable"]), _accepts(case, serialized)) for case in cases
    ]
    metrics = _prediction_metrics(predictions)
    return {
        "conditions": serialized,
        **metrics,
    }


def _accepts(case: dict[str, Any], conditions: list[dict[str, Any]]) -> bool:
    return all(
        condition["operator"] == "greater_than_or_equal"
        and float(case["signals"][condition["signal"]])
        >= float(condition["threshold"])
        for condition in conditions
    )


def _prediction_metrics(
    predictions: list[tuple[bool, bool]],
) -> dict[str, float]:
    answerable = [accepted for expected, accepted in predictions if expected]
    unanswerable = [accepted for expected, accepted in predictions if not expected]
    if not answerable or not unanswerable:
        raise ValueError("metrics require both answerability classes")
    acceptance = sum(answerable) / len(answerable)
    abstention = sum(not accepted for accepted in unanswerable) / len(unanswerable)
    return {
        "answerable_acceptance": acceptance,
        "unanswerable_abstention": abstention,
        "balanced_accuracy": (acceptance + abstention) / 2,
    }


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
        result = calibrate_multisignal_policy(
            confidence, min_answerable_acceptance=args.min_answerable_acceptance
        )
        write_private_report(result, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "condition_count": len(result["policy"]["conditions"]),
                "selected_metrics": result["calibration"]["selected_metrics"],
                "status": result["status"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
