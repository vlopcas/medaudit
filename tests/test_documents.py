import unittest
from datetime import date

from medaudit.documents import Document


class DocumentTest(unittest.TestCase):
    def test_effective_period_is_inclusive(self) -> None:
        document = Document(
            document_id="doc-v1",
            title="Documento sintético",
            version="1",
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 12, 31),
        )

        self.assertTrue(document.is_effective_on(date(2025, 1, 1)))
        self.assertTrue(document.is_effective_on(date(2025, 12, 31)))
        self.assertFalse(document.is_effective_on(date(2026, 1, 1)))
