"""Local legacy XLS row parser backed by xlrd."""

import hashlib
from datetime import datetime

import xlrd  # type: ignore[import-untyped]

from medaudit.documents import Document, DocumentElement, ElementKind
from medaudit.parsing.models import ParsedDocument


class XLSParser:
    """Represent each non-empty BIFF worksheet row as an atomic table element."""

    supported_media_types = frozenset({"application/vnd.ms-excel"})

    def parse(self, document: Document, content: bytes) -> ParsedDocument:
        try:
            workbook = xlrd.open_workbook(file_contents=content, on_demand=True)
        except Exception as error:
            raise ValueError("invalid or unsupported XLS content") from error

        elements: list[DocumentElement] = []
        try:
            ordinal = 0
            for worksheet in workbook.sheets():
                for row_index in range(worksheet.nrows):
                    values = [
                        _render_cell(
                            worksheet.cell(row_index, column_index),
                            workbook.datemode,
                        )
                        for column_index in range(worksheet.ncols)
                    ]
                    while values and not values[-1]:
                        values.pop()
                    if not any(values):
                        continue
                    text = "\t".join(values)
                    row_number = row_index + 1
                    elements.append(
                        DocumentElement(
                            element_id=_element_id(
                                document.document_id,
                                worksheet.name,
                                row_number,
                                text,
                            ),
                            document_id=document.document_id,
                            ordinal=ordinal,
                            kind=ElementKind.TABLE,
                            text=text,
                            section=worksheet.name,
                            metadata={
                                "sheet": worksheet.name,
                                "row": str(row_number),
                                "parser": "xlrd-rows-v1",
                            },
                        )
                    )
                    ordinal += 1
        finally:
            workbook.release_resources()
        return ParsedDocument(document=document, elements=tuple(elements))


def _render_cell(cell: object, datemode: int) -> str:
    cell_type = cell.ctype  # type: ignore[attr-defined]
    value = cell.value  # type: ignore[attr-defined]
    if cell_type in {xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK}:
        return ""
    if cell_type == xlrd.XL_CELL_DATE:
        parsed: datetime = xlrd.xldate_as_datetime(value, datemode)
        return parsed.isoformat()
    if cell_type == xlrd.XL_CELL_BOOLEAN:
        return "true" if value else "false"
    if cell_type == xlrd.XL_CELL_NUMBER and float(value).is_integer():
        return str(int(value))
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def _element_id(document_id: str, sheet: str, row: int, text: str) -> str:
    value = f"{document_id}\0{sheet}\0{row}\0{text}".encode()
    return f"el-{hashlib.sha256(value).hexdigest()[:16]}"
