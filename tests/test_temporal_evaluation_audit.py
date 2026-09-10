import tempfile
import unittest
from datetime import date
from pathlib import Path

from medaudit.catalog import Catalog, CatalogEntry, ReviewStatus
from medaudit.evaluation.temporal_audit import (
    audit_temporal_references,
    write_private_audit,
)


class TemporalEvaluationAuditTest(unittest.TestCase):
    def test_detects_reference_outside_document_period(self) -> None:
        catalog = Catalog(1, (self.entry(),))
        golden_sets = [
            {
                "reference_date": "2026-02-01",
                "cases": [
                    {
                        "id": "case-1",
                        "relevant_document_ids": ["doc-1"],
                    }
                ],
            }
        ]

        report = audit_temporal_references(golden_sets, catalog)

        self.assertFalse(report["ready"])
        self.assertEqual(report["conflict_count"], 1)
        self.assertEqual(report["conflicts"][0]["reason"], "not_yet_effective")

    def test_accepts_reference_inside_document_period(self) -> None:
        catalog = Catalog(1, (self.entry(),))
        golden_sets = [
            {
                "reference_date": "2026-07-01",
                "cases": [
                    {"id": "case-1", "relevant_document_ids": ["doc-1"]},
                    {"id": "missing", "relevant_document_ids": []},
                ],
            }
        ]

        report = audit_temporal_references(golden_sets, catalog)

        self.assertTrue(report["ready"])
        self.assertEqual(report["case_count"], 2)

    def test_output_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_private_audit({}, Path(directory) / "audit.json")

    @staticmethod
    def entry() -> CatalogEntry:
        return CatalogEntry(
            document_id="doc-1",
            content_sha256="a" * 64,
            relative_paths=("synthetic.pdf",),
            media_type="application/pdf",
            size_bytes=10,
            review_status=ReviewStatus.REVIEWED,
            title="Synthetic",
            family="policy",
            organization="Synthetic Org",
            version="1",
            effective_from=date(2026, 6, 1),
            effective_until=date(2026, 12, 31),
        )
