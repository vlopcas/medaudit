import json
import tempfile
import unittest
from pathlib import Path

from medaudit.evaluation.decomposition_execution import evaluate, load_dataset


class DecompositionExecutionEvaluationTest(unittest.TestCase):
    def test_reports_case_step_and_temporal_accuracy(self) -> None:
        payload = {
            "schema_version": 1,
            "policy": "decomposition-execution-v1",
            "notice": (
                "Conteúdo integralmente sintético, sem reprodução de "
                "documentos reais."
            ),
            "comparison_chunks": [
                {"chunk_id": "a", "document_id": "doc-a", "text": "alfa"},
                {"chunk_id": "b", "document_id": "doc-b", "text": "beta"},
            ],
            "temporal_snapshots": [
                {
                    "reference_date": "2026-01-01",
                    "chunks": [
                        {
                            "chunk_id": "t1",
                            "document_id": "doc-t1",
                            "text": "gama",
                        }
                    ],
                },
                {
                    "reference_date": "2027-01-01",
                    "chunks": [
                        {
                            "chunk_id": "t2",
                            "document_id": "doc-t2",
                            "text": "gama",
                        }
                    ],
                },
            ],
            "cases": [
                {
                    "id": "comparison",
                    "query": "Compare alfa com beta.",
                    "status": "ready",
                    "document_ids": ["doc-a", "doc-b"],
                },
                {
                    "id": "temporal",
                    "query": "Compare gama em 2026-01-01 e 2027-01-01.",
                    "status": "ready",
                    "document_ids": ["doc-t1", "doc-t2"],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dataset.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = evaluate(load_dataset(path))

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["step_document_accuracy"], 1.0)
        self.assertEqual(
            report["metrics"]["temporal_step_document_accuracy"], 1.0
        )
