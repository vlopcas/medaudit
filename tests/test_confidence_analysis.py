import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import patch

from medaudit.evaluation.confidence_analysis import (
    _distribution,
    _pairwise_rate,
    analyze_temporal_confidence,
)


class ConfidenceAnalysisTest(unittest.TestCase):
    answerable: ClassVar[list[dict[str, Any]]] = [
        {"signals": {"query_coverage": 0.8}},
        {"signals": {"query_coverage": 1.0}},
    ]
    unanswerable: ClassVar[list[dict[str, Any]]] = [
        {"signals": {"query_coverage": 0.4}}
    ]

    def test_summarizes_signal_distribution(self) -> None:
        result = _distribution(self.answerable, "query_coverage")

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["median"], 0.9)

    def test_computes_pairwise_separation_rate(self) -> None:
        rate = _pairwise_rate(
            self.answerable, self.unanswerable, "query_coverage"
        )

        self.assertEqual(rate, 1.0)

    def test_searches_only_selected_partition_cases(self) -> None:
        review = {
            "cases": [
                {
                    "candidate_id": case_id,
                    "category": "synthetic",
                    "difficulty": "medium",
                    "reasoning_type": "lookup",
                }
                for case_id in ("case-calibration", "case-holdout")
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / "snapshots"
            golden = root / "golden"
            snapshots.mkdir()
            golden.mkdir()
            (snapshots / "chunks-2026-01-01.local.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "reference_date": "2026-01-01",
                        "chunk": {
                            "chunk_id": "chunk-1",
                            "document_id": "doc-1",
                            "text": "synthetic evidence",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (golden / "retrieval-2026-01-01.local.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "reference_date": "2026-01-01",
                        "cases": [
                            {
                                "id": "case-calibration",
                                "question": "calibration query",
                                "category": "synthetic",
                                "relevant_document_ids": ["doc-1"],
                            },
                            {
                                "id": "case-holdout",
                                "question": "holdout query",
                                "category": "synthetic",
                                "relevant_document_ids": [],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "medaudit.evaluation.confidence_analysis.BM25Index.search",
                return_value=[],
            ) as search:
                report = analyze_temporal_confidence(
                    snapshots,
                    golden,
                    review,
                    top_k=5,
                    selected_case_ids={"case-calibration"},
                    partition="calibration",
                )

        search.assert_called_once_with("calibration query", top_k=5)
        self.assertEqual(report["case_count"], 1)
        self.assertEqual(report["partition"], "calibration")

    def test_empty_snapshot_abstains_without_searching_query(self) -> None:
        review = {
            "cases": [
                {
                    "candidate_id": "case-empty",
                    "category": "synthetic",
                    "difficulty": "medium",
                    "reasoning_type": "lookup",
                }
            ]
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
                                "id": "case-empty",
                                "question": "must not be searched",
                                "category": "synthetic",
                                "relevant_document_ids": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "medaudit.evaluation.confidence_analysis.BM25Index.search"
            ) as search:
                report = analyze_temporal_confidence(
                    snapshots,
                    golden,
                    review,
                    top_k=5,
                    selected_case_ids={"case-empty"},
                    partition="calibration",
                )

        search.assert_not_called()
        self.assertEqual(report["cases"][0]["signals"]["result_count"], 0)
