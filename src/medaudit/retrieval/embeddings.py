"""Local E5 embedding adapter with explicit query and passage roles."""

import importlib
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from medaudit.retrieval.local_model import MODEL_ID, MODEL_REVISION

FloatMatrix = NDArray[np.float32]
TRUNCATE_STRATEGY = "truncate-v1"
WINDOW_MEAN_STRATEGY = "token-window-mean-v1"
PASSAGE_STRATEGIES = (TRUNCATE_STRATEGY, WINDOW_MEAN_STRATEGY)


class E5Embedder:
    """Load the pinned E5 model from a local cache and create normalized vectors."""

    def __init__(
        self,
        cache_directory: Path,
        *,
        device: str = "cuda",
        passage_strategy: str = TRUNCATE_STRATEGY,
        window_overlap: int = 64,
    ) -> None:
        if passage_strategy not in PASSAGE_STRATEGIES:
            raise ValueError("unsupported passage embedding strategy")
        if window_overlap < 0:
            raise ValueError("window overlap cannot be negative")
        self._cache_directory = cache_directory
        self._device = device
        self.passage_strategy = passage_strategy
        self._window_overlap = window_overlap
        self._model: Any | None = None
        self._query_cache: dict[str, FloatMatrix] = {}

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        module = importlib.import_module("sentence_transformers")
        model_type: Any = module.SentenceTransformer
        self._model = model_type(
            MODEL_ID,
            revision=MODEL_REVISION,
            cache_folder=str(self._cache_directory),
            local_files_only=True,
            trust_remote_code=False,
            device=self._device,
        )
        return self._model

    def encode_passages(self, texts: list[str], *, batch_size: int) -> FloatMatrix:
        """Encode private chunks locally using the E5 passage prefix."""
        if batch_size <= 0:
            raise ValueError("embedding batch size must be positive")
        if self.passage_strategy == WINDOW_MEAN_STRATEGY:
            return self._encode_windowed_passages(texts, batch_size=batch_size)
        return self._encode([f"passage: {text}" for text in texts], batch_size)

    def encode_query(self, text: str) -> FloatMatrix:
        """Encode one query locally using the E5 query prefix."""
        cached = self._query_cache.get(text)
        if cached is None:
            cached = self._encode([f"query: {text}"], 1)
            self._query_cache[text] = cached
        return cached

    def passage_token_lengths(
        self, texts: list[str], *, batch_size: int = 256
    ) -> tuple[list[int], int]:
        """Count untruncated passage tokens using the model's own tokenizer."""
        if batch_size <= 0:
            raise ValueError("tokenizer batch size must be positive")
        model = self._load_model()
        maximum = int(model.max_seq_length)
        lengths: list[int] = []
        for start in range(0, len(texts), batch_size):
            batch = [f"passage: {text}" for text in texts[start : start + batch_size]]
            encoded: Any = model.tokenizer(
                batch,
                add_special_tokens=True,
                truncation=False,
                return_length=True,
                verbose=False,
            )
            lengths.extend(int(length) for length in encoded["length"])
        if len(lengths) != len(texts):
            raise ValueError("tokenizer returned an unexpected number of lengths")
        return lengths, maximum

    def _encode_windowed_passages(
        self, texts: list[str], *, batch_size: int
    ) -> FloatMatrix:
        model = self._load_model()
        tokenizer: Any = model.tokenizer
        special_tokens = int(tokenizer.num_special_tokens_to_add(pair=False))
        prefix_tokens = len(
            tokenizer.encode("passage: ", add_special_tokens=False, verbose=False)
        )
        capacity = int(model.max_seq_length) - special_tokens - prefix_tokens
        if capacity <= self._window_overlap:
            raise ValueError("embedding window overlap leaves no usable capacity")

        encoded: Any = tokenizer(
            texts, add_special_tokens=False, truncation=False, verbose=False
        )
        window_texts: list[str] = []
        owners: list[int] = []
        for owner, (text, token_ids) in enumerate(
            zip(texts, encoded["input_ids"], strict=True)
        ):
            windows = token_windows(
                [int(token_id) for token_id in token_ids],
                capacity=capacity,
                overlap=self._window_overlap,
            )
            if len(windows) == 1:
                window_texts.append(text)
                owners.append(owner)
                continue
            window_texts.extend(
                tokenizer.decode(window, skip_special_tokens=True) for window in windows
            )
            owners.extend([owner] * len(windows))
        vectors = self._encode(
            [f"passage: {text}" for text in window_texts], batch_size
        )
        return mean_window_embeddings(vectors, owners=owners, passage_count=len(texts))

    def _encode(self, texts: list[str], batch_size: int) -> FloatMatrix:
        vectors: Any = self._load_model().encode(
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


def token_windows(
    token_ids: list[int], *, capacity: int, overlap: int
) -> list[list[int]]:
    """Split token IDs into deterministic overlapping windows."""
    if capacity <= 0 or overlap < 0 or overlap >= capacity:
        raise ValueError("invalid token window configuration")
    if not token_ids:
        return [[]]
    step = capacity - overlap
    windows: list[list[int]] = []
    for start in range(0, len(token_ids), step):
        windows.append(token_ids[start : start + capacity])
        if start + capacity >= len(token_ids):
            break
    return windows


def mean_window_embeddings(
    vectors: FloatMatrix, *, owners: list[int], passage_count: int
) -> FloatMatrix:
    """Mean window vectors per passage and restore unit normalization."""
    if vectors.ndim != 2 or vectors.shape[0] != len(owners):
        raise ValueError("window vectors and owners do not match")
    if passage_count <= 0 or set(owners) - set(range(passage_count)):
        raise ValueError("window owner is outside passage range")
    sums = np.zeros((passage_count, vectors.shape[1]), dtype=np.float32)
    counts = np.zeros(passage_count, dtype=np.int32)
    for owner, vector in zip(owners, vectors, strict=True):
        sums[owner] += vector
        counts[owner] += 1
    if np.any(counts == 0):
        raise ValueError("every passage must own at least one window")
    means = sums / counts[:, np.newaxis]
    norms = np.linalg.norm(means, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("window mean produced a zero vector")
    return np.asarray(means / norms, dtype=np.float32)
