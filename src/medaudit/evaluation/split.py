"""Create a deterministic calibration/evaluation split for reviewed cases."""

import argparse
import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def split_reviewed_cases(
    review: dict[str, Any],
    *,
    calibration_fraction: float,
    seed: str,
    forced_calibration_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Split approved IDs while keeping prior experiment cases in calibration."""
    if review.get("schema_version") != 1:
        raise ValueError("unsupported review schema")
    if review.get("review_status") != "reviewed":
        raise ValueError("review queue is not complete")
    if not 0 < calibration_fraction < 1:
        raise ValueError("calibration fraction must be between zero and one")
    if not seed.strip():
        raise ValueError("split seed must not be empty")

    strata: defaultdict[str, list[str]] = defaultdict(list)
    case_labels: dict[str, str] = {}
    for case in review.get("cases", []):
        if case.get("review_status") != "approved":
            raise ValueError("all split cases must be approved")
        case_id = case["candidate_id"]
        if case_id in case_labels:
            raise ValueError("duplicate reviewed case id")
        answerability = case["answerability"]
        if answerability not in {
            "answerable",
            "candidate_unanswerable",
            "insufficient_evidence",
        }:
            raise ValueError("unsupported answerability label")
        case_labels[case_id] = answerability
        stratum = "answerable" if answerability == "answerable" else "unanswerable"
        strata[stratum].append(case_id)
    if len(case_labels) < 2:
        raise ValueError("at least two reviewed cases are required")

    forced = forced_calibration_ids or set()
    if forced - set(case_labels):
        raise ValueError("forced calibration cases are absent from review")
    calibration: list[str] = sorted(forced)
    evaluation: list[str] = []
    for _label, case_ids in sorted(strata.items()):
        ranked = sorted(
            (case_id for case_id in case_ids if case_id not in forced),
            key=lambda value: _rank(seed, value),
        )
        if not ranked:
            continue
        calibration_count = _calibration_count(len(ranked), calibration_fraction)
        calibration.extend(ranked[:calibration_count])
        evaluation.extend(ranked[calibration_count:])

    manifest = {
        "schema_version": 1,
        "strategy": "sha256-answerability-stratified-v2",
        "seed": seed,
        "calibration_fraction": calibration_fraction,
        "source_case_count": len(case_labels),
        "source_fingerprint": _fingerprint(case_labels),
        "forced_calibration_case_count": len(forced),
        "partitions": {
            "calibration": sorted(calibration),
            "evaluation": sorted(evaluation),
        },
    }
    validate_split(manifest, review)
    return manifest


def validate_split(manifest: dict[str, Any], review: dict[str, Any]) -> None:
    """Reject overlap, omissions, unknown IDs and source drift."""
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported split schema")
    cases = review.get("cases", [])
    labels = {case["candidate_id"]: case["answerability"] for case in cases}
    if len(labels) != len(cases):
        raise ValueError("duplicate reviewed case id")
    calibration = manifest["partitions"]["calibration"]
    evaluation = manifest["partitions"]["evaluation"]
    if len(calibration) != len(set(calibration)) or len(evaluation) != len(
        set(evaluation)
    ):
        raise ValueError("duplicate case id within split partition")
    if set(calibration).intersection(evaluation):
        raise ValueError("split partitions overlap")
    if set(calibration).union(evaluation) != set(labels):
        raise ValueError("split partitions do not match reviewed cases")
    if manifest.get("source_case_count") != len(labels):
        raise ValueError("split source case count has drifted")
    if manifest.get("source_fingerprint") != _fingerprint(labels):
        raise ValueError("split source fingerprint has drifted")


def _calibration_count(size: int, fraction: float) -> int:
    if size == 1:
        return 1
    return min(size - 1, max(1, math.floor(size * fraction + 0.5)))


def _rank(seed: str, case_id: str) -> str:
    return hashlib.sha256(f"{seed}\0{case_id}".encode()).hexdigest()


def _fingerprint(labels: dict[str, str]) -> str:
    canonical = json.dumps(sorted(labels.items()), separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def write_split(manifest: dict[str, Any], output: Path) -> None:
    if not output.name.endswith(".local.json"):
        raise ValueError("split output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered + "\n", encoding="utf-8")
    temporary.replace(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--calibration-fraction", type=float, default=0.7)
    parser.add_argument("--seed", default="medaudit-evaluation-v1")
    parser.add_argument("--prior-review", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        review: dict[str, Any] = json.loads(args.review.read_text(encoding="utf-8"))
        forced_calibration_ids = (
            {
                case["candidate_id"]
                for case in json.loads(
                    args.prior_review.read_text(encoding="utf-8")
                )["cases"]
            }
            if args.prior_review
            else set()
        )
        manifest = split_reviewed_cases(
            review,
            calibration_fraction=args.calibration_fraction,
            seed=args.seed,
            forced_calibration_ids=forced_calibration_ids,
        )
        write_split(manifest, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "calibration_case_count": len(
                    manifest["partitions"]["calibration"]
                ),
                "evaluation_case_count": len(manifest["partitions"]["evaluation"]),
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
