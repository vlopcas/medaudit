"""Process reviewed private documents into local provenance-rich chunks."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.catalog import CatalogAccessError, ReviewStatus
from medaudit.catalog.models import CatalogEntry
from medaudit.catalog.serialization import load_catalog
from medaudit.chunking import FormatAwareChunker
from medaudit.ingestion.inventory import collect_inventory
from medaudit.ingestion.pipeline import IngestionPipeline, ParserRegistry
from medaudit.parsing import (
    OCRFallbackPDFParser,
    PDFParser,
    TesseractOCRProvider,
    XLSParser,
    XLSXParser,
)


@dataclass(frozen=True, slots=True)
class ProcessingSummary:
    """Content-free aggregate result safe to print to the terminal."""

    catalog_document_count: int
    selected_document_count: int
    processed_document_count: int
    chunk_count: int
    status_counts: dict[str, int]
    ocr_enabled: bool

    @property
    def succeeded(self) -> bool:
        return self.status_counts.get("error", 0) == 0


def build_pipeline(*, enable_ocr: bool) -> IngestionPipeline:
    """Build the local parser and chunking composition root."""
    pdf_parser = (
        OCRFallbackPDFParser(TesseractOCRProvider()) if enable_ocr else PDFParser()
    )
    return IngestionPipeline(
        ParserRegistry([pdf_parser, XLSParser(), XLSXParser()]),
        FormatAwareChunker(),
    )


def process_catalog(
    catalog_path: Path,
    input_root: Path,
    output: Path,
    reference_date: date,
    *,
    enable_ocr: bool = False,
    pipeline: IngestionPipeline | None = None,
) -> ProcessingSummary:
    """Write chunks for reviewed entries effective on the reference date."""
    if not output.name.endswith(".local.jsonl"):
        raise ValueError("processed output must end with .local.jsonl")
    catalog = load_catalog(catalog_path)
    active_pipeline = pipeline or build_pipeline(enable_ocr=enable_ocr)
    resolved_root = input_root.resolve()
    inventory = collect_inventory(resolved_root)
    inventory_paths = {
        record.sha256: record.relative_path for record in inventory
    }
    statuses: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    selected = 0
    processed = 0

    for entry in catalog.entries:
        selection = _selection_status(entry, reference_date)
        if selection is not None:
            statuses[selection] += 1
            continue
        selected += 1
        try:
            source = _resolve_source(entry, resolved_root, inventory_paths)
            content = source.read_bytes()
            result = active_pipeline.ingest_catalog_entry(
                entry, content, reference_date
            )
        except (CatalogAccessError, OSError, ValueError, RuntimeError):
            statuses["error"] += 1
            continue
        if not result.chunks:
            statuses["empty"] += 1
            continue
        processed += 1
        statuses["processed"] += 1
        for chunk in result.chunks:
            records.append(
                {
                    "schema_version": 1,
                    "reference_date": reference_date.isoformat(),
                    "document": {
                        "document_id": result.parsed_document.document.document_id,
                        "version": result.parsed_document.document.version,
                        "effective_from": (
                            result.parsed_document.document.effective_from.isoformat()
                        ),
                        "effective_until": (
                            result.parsed_document.document.effective_until.isoformat()
                            if result.parsed_document.document.effective_until
                            else None
                        ),
                        "media_type": entry.media_type,
                        "metadata": result.parsed_document.document.metadata,
                    },
                    "chunk": asdict(chunk),
                }
            )

    rendered = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)
    return ProcessingSummary(
        catalog_document_count=len(catalog.entries),
        selected_document_count=selected,
        processed_document_count=processed,
        chunk_count=len(records),
        status_counts=dict(sorted(statuses.items())),
        ocr_enabled=enable_ocr,
    )


def _selection_status(entry: CatalogEntry, reference_date: date) -> str | None:
    if entry.review_status is not ReviewStatus.REVIEWED:
        return "not_reviewed"
    if entry.effective_from is None or reference_date < entry.effective_from:
        return "not_yet_effective"
    if entry.effective_until is not None and reference_date > entry.effective_until:
        return "expired"
    return None


def _resolve_source(
    entry: CatalogEntry, root: Path, inventory_paths: dict[str, str]
) -> Path:
    candidates = (*entry.relative_paths, inventory_paths.get(entry.content_sha256, ""))
    for relative_path in candidates:
        if not relative_path:
            continue
        candidate = (root / relative_path).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
            return candidate
    raise FileNotFoundError("catalog source is unavailable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-date", type=date.fromisoformat, required=True)
    parser.add_argument("--enable-ocr", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Process a corpus and print no private content or identifiers."""
    args = build_parser().parse_args(argv)
    try:
        summary = process_catalog(
            args.catalog,
            args.input,
            args.output,
            args.reference_date,
            enable_ocr=args.enable_ocr,
        )
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    payload = asdict(summary)
    payload["succeeded"] = summary.succeeded
    print(json.dumps(payload, sort_keys=True))
    return 0 if summary.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
