import tempfile
import unittest
from pathlib import Path

from medaudit.catalog import Catalog, CatalogEntry, ReviewStatus
from medaudit.evaluation.review_queue import prepare_review_queue, write_review_queue


class ReviewQueueTest(unittest.TestCase):
    catalog = Catalog(
        1,
        (
            CatalogEntry(
                document_id="doc-1",
                content_sha256="a" * 64,
                relative_paths=("synthetic-policy.pdf",),
                media_type="application/pdf",
                size_bytes=10,
                review_status=ReviewStatus.REVIEWED,
                title="Synthetic Policy",
                family="policy",
                organization="Synthetic Org",
                version="1",
            ),
        ),
    )

    def test_maps_labels_but_keeps_case_pending(self) -> None:
        candidates = {
            "cases": [
                {
                    "candidate_id": "candidate-001",
                    "question": "Synthetic question?",
                    "answerability": "answerable",
                    "required_source_labels": ["Synthetic Policy"],
                }
            ]
        }

        queue = prepare_review_queue(candidates, self.catalog)

        case = queue["cases"][0]
        self.assertEqual(case["proposed_relevant_document_ids"], ["doc-1"])
        self.assertEqual(case["review_status"], "pending")

    def test_rejects_unknown_source_label_without_echoing_it(self) -> None:
        candidates = {
            "cases": [
                {
                    "candidate_id": "candidate-001",
                    "answerability": "answerable",
                    "required_source_labels": ["private unknown"],
                }
            ]
        }

        with self.assertRaisesRegex(ValueError, "missing or ambiguous") as caught:
            prepare_review_queue(candidates, self.catalog)

        self.assertNotIn("private unknown", str(caught.exception))

    def test_output_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_review_queue({}, Path(directory) / "review.json")
