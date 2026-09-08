"""Build a private, content-agnostic inventory of local documents."""

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Sequence

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".xls", ".xlsx"})


@dataclass(frozen=True, slots=True)
class FileRecord:
    """Technical metadata for a local source file."""

    relative_path: str
    extension: str
    size_bytes: int
    modified_at: str
    sha256: str


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    """Hash a file incrementally without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def collect_inventory(root: Path) -> list[FileRecord]:
    """Collect metadata for supported documents below ``root``."""
    resolved_root = root.resolve()
    records: list[FileRecord] = []
    for path in sorted(resolved_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        stat = path.stat()
        records.append(
            FileRecord(
                relative_path=path.relative_to(resolved_root).as_posix(),
                extension=path.suffix.lower(),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                sha256=sha256_file(path),
            )
        )
    return records


def write_inventory(records: list[FileRecord], output: Path) -> None:
    """Write the local manifest as deterministic, readable JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "document_count": len(records),
        "documents": [asdict(record) for record in records],
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    args = build_parser().parse_args(argv)
    if not args.input.is_dir():
        raise SystemExit(f"input directory does not exist: {args.input}")
    records = collect_inventory(args.input)
    write_inventory(records, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

