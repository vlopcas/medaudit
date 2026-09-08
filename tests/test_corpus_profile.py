import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import pymupdf
import xlwt  # type: ignore[import-untyped]

from medaudit.ingestion.profile import profile_corpus, write_private_profile


class CorpusProfileTest(unittest.TestCase):
    def test_reports_aggregates_without_extracted_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf: Any = pymupdf.open()  # type: ignore[no-untyped-call]
            page = pdf.new_page()
            page.insert_text((72, 72), "Synthetic private-like text")
            (root / "sample.pdf").write_bytes(pdf.tobytes())
            pdf.close()
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet("Synthetic")
            worksheet.write(0, 0, "PX-101")
            workbook.save(str(root / "legacy.xls"))

            report = profile_corpus(root)

            self.assertEqual(report["summary"]["file_count"], 2)
            self.assertEqual(report["summary"]["status_counts"]["extracted"], 2)
            self.assertNotIn("Synthetic private-like text", json.dumps(report))

    def test_output_requires_local_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profile.json"

            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_private_profile({}, output)

    def test_empty_pdf_is_classified_for_ocr(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf: Any = pymupdf.open()  # type: ignore[no-untyped-call]
            pdf.new_page()
            (root / "scan-like.pdf").write_bytes(pdf.tobytes())
            pdf.close()

            report = profile_corpus(root)

            self.assertEqual(report["summary"]["status_counts"]["needs_ocr"], 1)
