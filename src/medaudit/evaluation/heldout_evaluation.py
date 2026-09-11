"""Evaluate a frozen confidence policy once on the held-out partition."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.confidence_policy import canonical_hash
from medaudit.evaluation.private_bm25 import (
    load_private_cases,
    load_private_chunks,
    write_private_report,
)
from medaudit.evaluation.split import validate_split
from medaudit.retrieval import BM25Index


def evaluate_heldout_policy(
    *,
    snapshots_directory: Path,
    golden_directory: Path,
    review: dict[str, Any],
    split: dict[str, Any],
    policy: dict[str, Any],
    calibration_report: dict[str, Any],
    top_k: int,
) -> dict[str, Any]:
    """Measure frozen-policy generalization without evaluating calibration IDs."""
    validate_split(split, review)
    _validate_policy(policy, calibration_report)
    heldout_ids = set(split["partitions"]["evaluation"])
    if not heldout_ids:
        raise ValueError("held-out partition is empty")
    threshold = float(policy["policy"]["threshold"])
    seen_ids: set[str] = set()
    details: list[dict[str, Any]] = []

    for cases_path in sorted(golden_directory.glob("retrieval-*.local.json")):
        suffix = cases_path.name.removeprefix("retrieval-").removesuffix(
            ".local.json"
        )
        cases, case_date = load_private_cases(cases_path)
        selected = [case for case in cases if case.case_id in heldout_ids]
        if not selected:
            continue
        chunks_path = snapshots_directory / f"chunks-{suffix}.local.jsonl"
        if chunks_path.stat().st_size:
            chunks, chunk_date = load_private_chunks(chunks_path)
            if chunk_date != case_date:
                raise ValueError("snapshot and golden set dates do not match")
            index: BM25Index | None = BM25Index(chunks)
        else:
            index = None

        for case in selected:
            if case.case_id in seen_ids:
                raise ValueError("duplicate held-out case id")
            seen_ids.add(case.case_id)
            results = index.search(case.question, top_k=top_k) if index else []
            top_score = results[0].score if results else 0.0
            accepted = top_score >= threshold
            relevant = case.relevant_chunk_ids or case.relevant_document_ids
            answerable = bool(relevant)
            retrieved = {
                result.chunk.chunk_id
                if case.relevant_chunk_ids
                else result.chunk.document_id
                for result in results
            }
            retrieval_hit = bool(retrieved.intersection(relevant)) if relevant else None
            details.append(
                {
                    "case_id": case.case_id,
                    "answerable": answerable,
                    "accepted": accepted,
                    "retrieval_hit": retrieval_hit,
                    "top_score": top_score,
                }
            )
    if seen_ids != heldout_ids:
        raise ValueError("held-out cases do not match golden sets")
    return _summarize(details, policy, top_k)


def _validate_policy(
    policy: dict[str, Any], calibration_report: dict[str, Any]
) -> None:
    if policy.get("schema_version") != 1 or policy.get("status") != "frozen":
        raise ValueError("confidence policy is not frozen")
    rule = policy.get("policy", {})
    if rule.get("signal") != "top_score" or rule.get("operator") != (
        "greater_than_or_equal"
    ):
        raise ValueError("unsupported confidence policy")
    if calibration_report.get("partition") != "calibration":
        raise ValueError("policy source is not a calibration report")
    expected_hash = policy.get("calibration", {}).get("source_sha256")
    if expected_hash != canonical_hash(calibration_report):
        raise ValueError("calibration report does not match frozen policy")


def _summarize(
    details: list[dict[str, Any]], policy: dict[str, Any], top_k: int
) -> dict[str, Any]:
    answerable = [case for case in details if case["answerable"]]
    unanswerable = [case for case in details if not case["answerable"]]
    if not answerable or not unanswerable:
        raise ValueError("held-out evaluation requires both answerability classes")
    accepted_answerable = [case for case in answerable if case["accepted"]]
    hits = [case for case in answerable if case["retrieval_hit"]]
    accepted_hits = [case for case in accepted_answerable if case["retrieval_hit"]]
    abstained_unanswerable = [case for case in unanswerable if not case["accepted"]]
    answerable_acceptance = len(accepted_answerable) / len(answerable)
    unanswerable_abstention = len(abstained_unanswerable) / len(unanswerable)
    return {
        "schema_version": 1,
        "partition": "evaluation",
        "policy_sha256": canonical_hash(policy),
        "top_k": top_k,
        "case_count": len(details),
        "answerable_case_count": len(answerable),
        "unanswerable_case_count": len(unanswerable),
        "metrics": {
            "answerable_acceptance": answerable_acceptance,
            "unanswerable_abstention": unanswerable_abstention,
            "balanced_accuracy": (
                answerable_acceptance + unanswerable_abstention
            )
            / 2,
            f"retrieval_hit_rate@{top_k}": len(hits) / len(answerable),
            "accepted_answerable_hit_rate": (
                len(accepted_hits) / len(accepted_answerable)
                if accepted_answerable
                else None
            ),
            "answerable_accepted_and_hit_rate": len(accepted_hits) / len(answerable),
            "unsafe_acceptance_rate": 1 - unanswerable_abstention,
        },
        "cases": details,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--golden-sets", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.output.exists():
            raise FileExistsError("held-out evaluation output already exists")
        inputs = [args.review, args.split, args.policy, args.calibration]
        review, split, policy, calibration = [
            json.loads(path.read_text(encoding="utf-8")) for path in inputs
        ]
        result = evaluate_heldout_policy(
            snapshots_directory=args.snapshots,
            golden_directory=args.golden_sets,
            review=review,
            split=split,
            policy=policy,
            calibration_report=calibration,
            top_k=args.top_k,
        )
        write_private_report(result, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "case_count": result["case_count"],
                "answerable_case_count": result["answerable_case_count"],
                "unanswerable_case_count": result["unanswerable_case_count"],
                "metrics": result["metrics"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
