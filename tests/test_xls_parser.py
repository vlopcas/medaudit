import unittest
from datetime import date
from io import BytesIO

import xlwt  # type: ignore[import-untyped]

from medaudit.documents import Document, ElementKind
from medaudit.parsing import XLSParser


class XLSParserTest(unittest.TestCase):
    def test_extracts_rows_and_sheet_provenance(self) -> None:
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("Synthetic Rules")
        worksheet.write(0, 0, "Code")
        worksheet.write(0, 1, "Limit")
        worksheet.write(1, 0, "PX-101")
        worksheet.write(1, 1, 2)
        buffer = BytesIO()
        workbook.save(buffer)
        document = Document("xls-v1", "Synthetic XLS", "1", date(2026, 1, 1))

        parsed = XLSParser().parse(document, buffer.getvalue())

        self.assertEqual(len(parsed.elements), 2)
        self.assertEqual(parsed.elements[0].kind, ElementKind.TABLE)
        self.assertEqual(parsed.elements[1].text, "PX-101\t2")
        self.assertEqual(parsed.elements[1].section, "Synthetic Rules")
        self.assertEqual(parsed.elements[1].metadata["row"], "2")

    def test_rejects_invalid_xls(self) -> None:
        document = Document("xls-v1", "Synthetic", "1", date(2026, 1, 1))

        with self.assertRaisesRegex(ValueError, "invalid or unsupported XLS"):
            XLSParser().parse(document, b"not a workbook")
