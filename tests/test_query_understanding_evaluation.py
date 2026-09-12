import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from medaudit.evaluation.query_understanding import (
    QueryUnderstandingCase,
    evaluate_query_understanding,
    load_cases,
    verify_input,
)
from medaudit.query_understanding import QueryIntent


class QueryUnderstandingEvaluationTest(unittest.TestCase):
    def test_evaluates_exact_and_per_field_accuracy(self) -> None:
        cases = [
            QueryUnderstandingCase(
                case_id="synthetic-1",
                query="Compare a regra A com a regra B.",
                intent=QueryIntent.COMPARISON,
                reference_date=None,
                procedure=None,
                requires_external_data=False,
                requires_decomposition=True,
            )
        ]

        report = evaluate_query_understanding(cases)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["accuracy_by_field"]["intent"], 1.0)
        self.assertTrue(report["cases"][0]["all_fields_correct"])

    def test_loader_rejects_duplicate_ids(self) -> None:
        payload = {
            "schema_version": 1,
            "cases": [
                {
                    "id": "duplicate",
                    "query": "Regra sintética?",
                    "intent": "document_lookup",
                    "reference_date": None,
                    "procedure": None,
                    "requires_external_data": False,
                    "requires_decomposition": False,
                },
                {
                    "id": "duplicate",
                    "query": "Outra regra sintética?",
                    "intent": "document_lookup",
                    "reference_date": None,
                    "procedure": None,
                    "requires_external_data": False,
                    "requires_decomposition": False,
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicate case id"):
                load_cases(path)

    def test_verifies_frozen_dataset_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text("{}", encoding="utf-8")
            digest = hashlib.sha256(b"{}").hexdigest()

            self.assertEqual(verify_input(path, digest), digest)
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                verify_input(path, "0" * 64)
