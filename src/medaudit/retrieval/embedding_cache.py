"""Persistent private cache for reproducible passage embeddings."""

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from medaudit.documents import Chunk
from medaudit.retrieval.dense import Embedder
from medaudit.retrieval.embeddings import FloatMatrix
from medaudit.retrieval.local_model import MODEL_ID, MODEL_REVISION


class EmbeddingCache:
    """Reuse embeddings by chunk identity while detecting stale content."""

    def __init__(self, path: Path, *, model_id: str, model_revision: str) -> None:
        if not path.name.endswith(".local.npz"):
            raise ValueError("embedding cache output must end with .local.npz")
        self._path = path
        self._model_id = model_id
        self._model_revision = model_revision

    def materialize(
        self,
        chunks: list[Chunk],
        embedder: Embedder,
        *,
        batch_size: int = 32,
    ) -> FloatMatrix:
        """Return vectors in input order, encoding only previously unseen chunks."""
        if not chunks:
            raise ValueError("at least one chunk is required")
        if batch_size <= 0:
            raise ValueError("embedding batch size must be positive")
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("duplicate chunk ids")

        cached = self._load()
        missing: list[Chunk] = []
        for chunk in chunks:
            digest = _text_hash(chunk.text)
            stored = cached.get(chunk.chunk_id)
            if stored is None:
                missing.append(chunk)
            elif stored[0] != digest:
                raise ValueError("cached chunk id refers to different content")

        if missing:
            vectors = embedder.encode_passages(
                [chunk.text for chunk in missing], batch_size=batch_size
            )
            _validate_matrix(vectors, len(missing))
            dimensions = {vector.shape[0] for _, vector in cached.values()}
            if dimensions and dimensions != {vectors.shape[1]}:
                raise ValueError("cached and generated embedding dimensions differ")
            for chunk, vector in zip(missing, vectors, strict=True):
                cached[chunk.chunk_id] = (_text_hash(chunk.text), vector)
            self._write(cached)

        matrix = np.stack([cached[chunk_id][1] for chunk_id in chunk_ids]).astype(
            np.float32, copy=False
        )
        _validate_matrix(matrix, len(chunks))
        return matrix

    def _load(self) -> dict[str, tuple[str, FloatMatrix]]:
        if not self._path.exists():
            return {}
        with np.load(self._path, allow_pickle=False) as archive:
            metadata = json.loads(str(archive["metadata"].item()))
            if metadata.get("schema_version") != 1:
                raise ValueError("unsupported embedding cache schema")
            if (
                metadata.get("model_id") != self._model_id
                or metadata.get("model_revision") != self._model_revision
            ):
                raise ValueError("embedding cache belongs to a different model")
            chunk_ids = archive["chunk_ids"]
            text_hashes = archive["text_sha256"]
            embeddings = archive["embeddings"]
        _validate_matrix(embeddings, len(chunk_ids))
        if len(chunk_ids) != len(text_hashes) or len(set(chunk_ids.tolist())) != len(
            chunk_ids
        ):
            raise ValueError("embedding cache index is inconsistent")
        return {
            str(chunk_id): (str(text_hash), vector)
            for chunk_id, text_hash, vector in zip(
                chunk_ids, text_hashes, embeddings, strict=True
            )
        }

    def _write(self, cached: dict[str, tuple[str, FloatMatrix]]) -> None:
        ordered = sorted(cached.items())
        embeddings = np.stack([entry[1][1] for entry in ordered]).astype(
            np.float32, copy=False
        )
        metadata: dict[str, Any] = {
            "schema_version": 1,
            "model_id": self._model_id,
            "model_revision": self._model_revision,
            "embedding_dimension": int(embeddings.shape[1]),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_name(f".{self._path.name}.tmp")
        with temporary.open("wb") as destination:
            np.savez(
                destination,
                metadata=np.asarray(json.dumps(metadata, sort_keys=True)),
                chunk_ids=np.asarray([entry[0] for entry in ordered]),
                text_sha256=np.asarray([entry[1][0] for entry in ordered]),
                embeddings=embeddings,
            )
        temporary.replace(self._path)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _validate_matrix(matrix: FloatMatrix, expected_rows: int) -> None:
    if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not matrix.shape[1]:
        raise ValueError("embedding matrix has an unexpected shape")
    if matrix.dtype != np.float32:
        raise ValueError("embedding matrix must use float32")
    if not np.isfinite(matrix).all():
        raise ValueError("embedding matrix contains non-finite values")


def load_unique_snapshot_chunks(directory: Path) -> tuple[list[Chunk], int]:
    """Load temporal snapshots and deduplicate identical chunk IDs safely."""
    from medaudit.evaluation.private_bm25 import load_private_chunks

    unique: dict[str, Chunk] = {}
    snapshot_count = 0
    for path in sorted(directory.glob("chunks-*.local.jsonl")):
        snapshot_count += 1
        if path.stat().st_size == 0:
            continue
        chunks, _ = load_private_chunks(path)
        for chunk in chunks:
            existing = unique.get(chunk.chunk_id)
            if existing is not None and existing.text != chunk.text:
                raise ValueError("snapshot chunk id refers to different content")
            unique[chunk.chunk_id] = chunk
    if not snapshot_count:
        raise ValueError("no temporal snapshots found")
    if not unique:
        raise ValueError("temporal snapshots contain no chunks")
    return [unique[chunk_id] for chunk_id in sorted(unique)], snapshot_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--model-cache", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        from medaudit.retrieval.embeddings import E5Embedder

        chunks, snapshot_count = load_unique_snapshot_chunks(args.snapshots)
        embedder = E5Embedder(args.model_cache)
        matrix = EmbeddingCache(
            args.cache, model_id=MODEL_ID, model_revision=MODEL_REVISION
        ).materialize(chunks, embedder, batch_size=args.batch_size)
    except (
        ImportError,
        KeyError,
        TypeError,
        ValueError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "embedding_dimension": int(matrix.shape[1]),
                "snapshot_count": snapshot_count,
                "succeeded": True,
                "unique_chunk_count": len(chunks),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
