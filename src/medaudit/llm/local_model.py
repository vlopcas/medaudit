"""Download and verify the pinned GGUF without mounting private data."""

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.llm.local_http import MODEL_FILE, MODEL_ID, MODEL_REVISION, MODEL_SHA256

MODEL_URL = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{MODEL_FILE}"


def sha256_file(path: Path) -> str:
    """Hash a file incrementally."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def prepare_local_model(
    model_directory: Path, *, allow_download: bool
) -> dict[str, Any]:
    """Ensure the pinned model exists and matches its published digest."""
    model_directory.mkdir(parents=True, exist_ok=True)
    destination = model_directory / MODEL_FILE
    if not destination.is_file():
        if not allow_download:
            raise FileNotFoundError("pinned local model is not available")
        temporary = destination.with_suffix(f"{destination.suffix}.partial")
        try:
            with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
                with temporary.open("wb") as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
            temporary.replace(destination)
        except (OSError, urllib.error.URLError):
            temporary.unlink(missing_ok=True)
            raise
    digest = sha256_file(destination)
    if digest != MODEL_SHA256:
        raise ValueError("local model checksum mismatch")
    return {
        "schema_version": 1,
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "filename": MODEL_FILE,
        "sha256": digest,
        "size_bytes": destination.stat().st_size,
        "quantization": "Q4_K_M",
    }


def write_manifest(payload: dict[str, Any], path: Path) -> None:
    """Atomically write an ignored local model manifest."""
    if not path.name.endswith(".local.json"):
        raise ValueError("model manifest must end with .local.json")
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = prepare_local_model(args.models, allow_download=args.download)
        write_manifest(manifest, args.manifest)
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "model_id": manifest["model_id"],
                "revision": manifest["revision"],
                "size_bytes": manifest["size_bytes"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
