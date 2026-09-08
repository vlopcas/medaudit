"""Document parsing contracts and local implementations."""

from medaudit.parsing.models import ParsedDocument
from medaudit.parsing.ocr import OCRFallbackPDFParser, OCRProvider, TesseractOCRProvider
from medaudit.parsing.pdf import PDFParser
from medaudit.parsing.plain_text import PlainTextParser
from medaudit.parsing.protocol import DocumentParser
from medaudit.parsing.xls import XLSParser
from medaudit.parsing.xlsx import XLSXParser

__all__ = [
    "DocumentParser",
    "OCRFallbackPDFParser",
    "OCRProvider",
    "PDFParser",
    "ParsedDocument",
    "PlainTextParser",
    "TesseractOCRProvider",
    "XLSParser",
    "XLSXParser",
]
