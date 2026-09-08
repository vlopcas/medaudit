"""Document parsing contracts and local implementations."""

from medaudit.parsing.models import ParsedDocument
from medaudit.parsing.plain_text import PlainTextParser
from medaudit.parsing.protocol import DocumentParser

__all__ = ["DocumentParser", "ParsedDocument", "PlainTextParser"]
