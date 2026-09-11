"""Local E5 embedding adapter with explicit query and passage roles."""

import importlib
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from medaudit.retrieval.local_model import MODEL_ID, MODEL_REVISION

FloatMatrix = NDArray[np.float32]


class E5Embedder:
    """Load the pinned E5 model from a local cache and create normalized vectors."""

    def __init__(self, cache_directory: Path, *, device: str = "cuda") -> None:
        module = importlib.import_module("sentence_transformers")
        model_type: Any = module.SentenceTransformer
        self._model: Any = model_type(
            MODEL_ID,
            revision=MODEL_REVISION,
            cache_folder=str(cache_directory),
            local_files_only=True,
            trust_remote_code=False,
            device=device,
        )

    def encode_passages(self, texts: list[str], *, batch_size: int) -> FloatMatrix:
        """Encode private chunks locally using the E5 passage prefix."""
        if batch_size <= 0:
            raise ValueError("embedding batch size must be positive")
        return self._encode([f"passage: {text}" for text in texts], batch_size)

    def encode_query(self, text: str) -> FloatMatrix:
        """Encode one query locally using the E5 query prefix."""
        return self._encode([f"query: {text}"], 1)

    def _encode(self, texts: list[str], batch_size: int) -> FloatMatrix:
        vectors: Any = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        matrix = np.asarray(vectors, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] != len(texts):
            raise ValueError("embedding model returned an unexpected shape")
        return matrix
