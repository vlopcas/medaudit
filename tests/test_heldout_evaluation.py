import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from medaudit.evaluation.confidence_policy import canonical_hash
from medaudit.evaluation.heldout_evaluation import evaluate_heldout_policy


class HeldoutEvaluationTest(unittest.TestCase):
    def test_searches_only_heldout_and_applies_frozen_policy(self) -> None:
        review = {
            "schema_version": 1,
            "review_status": "reviewed",
            "cases": [
                {
                    "candidate_id": case_id,
                    "answerability": label,
                    "review_status": "approved",
                }
                for case_id, label in (
                    ("calibration", "answerable"),
                    ("heldout-answerable", "answerable"),
                    ("heldout-unanswerable", "insufficient_evidence"),
                )
            ],
        }
        split = {
            "schema_version": 1,
            "source_case_count": 3,
            "source_fingerprint": self._fingerprint(review),
            "partitions": {
                "calibration": ["calibration"],
                "evaluation": ["heldout-answerable", "heldout-unanswerable"],
            },
        }
        calibration = {"partition": "calibration"}
        policy = {
            "schema_version": 1,
            "status": "frozen",
            "policy": {
                "signal": "top_score",
                "operator": "greater_than_or_equal",
                "threshold": 1.0,
            },
            "calibration": {"source_sha256": canonical_hash(calibration)},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / "snapshots"
            golden = root / "golden"
            snapshots.mkdir()
            golden.mkdir()
            (snapshots / "chunks-2026-01-01.local.jsonl").touch()
            (golden / "retrieval-2026-01-01.local.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "reference_date": "2026-01-01",
                        "cases": [
                            {
                                "id": "calibration",
                                "question": "must not run",
                                "category": "synthetic",
                                "relevant_document_ids": ["doc-1"],
                            },
                            {
                                "id": "heldout-answerable",
                                "question": "empty answerable",
                                "category": "synthetic",
                                "relevant_document_ids": ["doc-1"],
                            },
                            {
                                "id": "heldout-unanswerable",
                                "question": "empty unanswerable",
                                "category": "synthetic",
                                "relevant_document_ids": [],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch("medaudit.retrieval.BM25Index.search") as search:
                result = evaluate_heldout_policy(
                    snapshots_directory=snapshots,
                    golden_directory=golden,
                    review=review,
                    split=split,
                    policy=policy,
                    calibration_report=calibration,
                    top_k=5,
                )

        search.assert_not_called()
        self.assertEqual(result["case_count"], 2)
        self.assertEqual(result["metrics"]["unanswerable_abstention"], 1.0)

    @staticmethod
    def _fingerprint(review: dict[str, Any]) -> str:
        from medaudit.evaluation.split import _fingerprint

        return _fingerprint(
            {
                case["candidate_id"]: case["answerability"]
                for case in review["cases"]
            }
        )
