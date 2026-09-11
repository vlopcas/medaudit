"""Download or verify the pinned local embedding model without corpus access."""

import argparse
import importlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

MODEL_ID = "intfloat/multilingual-e5-base"
MODEL_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"


def prepare_model(
    cache_directory: Path, *, allow_download: bool
) -> dict[str, Any]:
    """Load a pinned model and verify its embedding interface on synthetic text."""
    module = importlib.import_module("sentence_transformers")
    model_type: Any = module.SentenceTransformer
    model = model_type(
        MODEL_ID,
        revision=MODEL_REVISION,
        cache_folder=str(cache_directory),
        local_files_only=not allow_download,
        trust_remote_code=False,
    )
    embeddings = model.encode(
        ["query: synthetic verification", "passage: synthetic evidence"],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    if embeddings.ndim != 2 or embeddings.shape[0] != 2:
        raise ValueError("embedding model returned an unexpected shape")
    return {
        "schema_version": 1,
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "embedding_dimension": int(embeddings.shape[1]),
        "normalized": True,
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    return parser


def write_model_manifest(manifest: dict[str, Any], output: Path) -> None:
    if not output.name.endswith(".local.json"):
        raise ValueError("model manifest output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered + "\n", encoding="utf-8")
    temporary.replace(output)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = prepare_model(args.cache, allow_download=args.download)
        write_model_manifest(manifest, args.manifest)
    except (
        ImportError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        RuntimeError,
    ) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "embedding_dimension": manifest["embedding_dimension"],
                "model_id": manifest["model_id"],
                "revision": manifest["revision"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
