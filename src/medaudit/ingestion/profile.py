"""Profile a private local corpus without persisting extracted content."""

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.documents import Document
from medaudit.parsing import PDFParser, XLSXParser
from medaudit.parsing.protocol import DocumentParser

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
KNOWN_UNSUPPORTED = frozenset({".xls"})


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    """Private diagnostics for one file; never includes extracted text."""

    relative_path: str
    extension: str
    status: str
    size_bytes: int
    element_count: int | None = None
    page_count: int | None = None
    error_type: str | None = None


def profile_corpus(root: Path) -> dict[str, Any]:
    """Parse recognized local files and return content-free diagnostics."""
    resolved_root = root.resolve()
    parsers: dict[str, DocumentParser] = {
        "application/pdf": PDFParser(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (
            XLSXParser()
        ),
    }
    records: list[ProfileRecord] = []
    supported_suffixes = MEDIA_TYPES.keys() | KNOWN_UNSUPPORTED
    for path in sorted(resolved_root.rglob("*")):
        suffix = path.suffix.casefold()
        if not path.is_file() or suffix not in supported_suffixes:
            continue
        relative_path = path.relative_to(resolved_root).as_posix()
        size_bytes = path.stat().st_size
        if suffix in KNOWN_UNSUPPORTED:
            records.append(
                ProfileRecord(relative_path, suffix, "unsupported", size_bytes)
            )
            continue

        content = path.read_bytes()
        document_id = f"local-{hashlib.sha256(content).hexdigest()[:16]}"
        document = Document(
            document_id=document_id,
            title="private-local-document",
            version="unclassified",
            effective_from=date.min,
        )
        try:
            parsed = parsers[MEDIA_TYPES[suffix]].parse(document, content)
        except Exception as error:
            records.append(
                ProfileRecord(
                    relative_path,
                    suffix,
                    "error",
                    size_bytes,
                    error_type=_root_error_type(error),
                )
            )
            continue
        pages = [element.page for element in parsed.elements if element.page]
        records.append(
            ProfileRecord(
                relative_path,
                suffix,
                "extracted" if parsed.elements else "empty",
                size_bytes,
                element_count=len(parsed.elements),
                page_count=max(pages, default=None),
            )
        )

    status_counts = Counter(record.status for record in records)
    return {
        "schema_version": 1,
        "privacy": "local-only; contains filenames but no extracted content",
        "summary": {
            "file_count": len(records),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "files": [asdict(record) for record in records],
    }


def _root_error_type(error: Exception) -> str:
    root: BaseException = error
    while root.__cause__ is not None:
        root = root.__cause__
    return type(root).__name__


def write_private_profile(report: dict[str, Any], output: Path) -> None:
    """Persist diagnostics only to a conventionally ignored local filename."""
    if not output.name.endswith(".local.json"):
        raise ValueError("profile output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Write private details and print only aggregate counts."""
    args = build_parser().parse_args(argv)
    if not args.input.is_dir():
        raise SystemExit("input directory does not exist")
    report = profile_corpus(args.input)
    write_private_profile(report, args.output)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
