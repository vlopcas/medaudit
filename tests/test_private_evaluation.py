import json
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

from medaudit.documents import Chunk
from medaudit.evaluation.private_bm25 import (
    PrivateEvaluationCase,
    evaluate_private,
    load_private_chunks,
    validate_private_references,
    write_private_report,
)


class PrivateEvaluationTest(unittest.TestCase):
    chunks: ClassVar[list[Chunk]] = [
        Chunk("c1", "d1", "synthetic authorization code PX-101"),
        Chunk("c2", "d2", "synthetic billing rule"),
    ]

    def test_evaluates_document_level_relevance_and_abstention(self) -> None:
        cases = [
            PrivateEvaluationCase(
                "answerable",
                "PX-101",
                "exact_lookup",
                relevant_document_ids=frozenset({"d1"}),
            ),
            PrivateEvaluationCase("missing", "ZQ-999", "missing_evidence"),
        ]

        report = evaluate_private(self.chunks, cases, top_k=1, min_score=0.0)

        self.assertEqual(report["metrics"]["hit_rate@1"], 1.0)
        self.assertEqual(report["metrics"]["abstention_accuracy"], 1.0)
        self.assertNotIn("question", json.dumps(report))

    def test_case_cannot_mix_relevance_levels(self) -> None:
        with self.assertRaisesRegex(ValueError, "not both"):
            PrivateEvaluationCase(
                "mixed",
                "synthetic",
                "invalid",
                frozenset({"c1"}),
                frozenset({"d1"}),
            )

    def test_rejects_unknown_document_reference_without_exposing_id(self) -> None:
        cases = [
            PrivateEvaluationCase(
                "case", "synthetic", "lookup", relevant_document_ids=frozenset({"x"})
            )
        ]

        with self.assertRaisesRegex(ValueError, "unknown documents") as caught:
            validate_private_references(self.chunks, cases)

        self.assertNotIn("x", str(caught.exception))

    def test_loads_private_jsonl(self) -> None:
        record = {
            "schema_version": 1,
            "reference_date": "2026-09-08",
            "chunk": {
                "chunk_id": "c1",
                "document_id": "d1",
                "text": "synthetic",
                "page": 1,
                "section": None,
                "metadata": {},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chunks.local.jsonl"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")

            chunks, reference_date = load_private_chunks(path)

        self.assertEqual(chunks[0].chunk_id, "c1")
        self.assertEqual(reference_date, "2026-09-08")

    def test_report_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_private_report({}, Path(directory) / "report.json")
