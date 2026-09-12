"""Deterministic retrieval gate for evidence-first RAG."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.rag.models import (
    Evidence,
    EvidenceLocation,
    RetrievalDecision,
    RetrievalStatus,
)
from medaudit.retrieval import ConfidenceAnalyzer, Retriever


@dataclass(frozen=True, slots=True)
class FrozenTopScorePolicy:
    """Runtime representation of the calibrated, frozen abstention rule."""

    threshold: float

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("policy threshold cannot be negative")

    def accepts(self, top_score: float) -> bool:
        """Apply the inclusive threshold selected during calibration."""
        return top_score >= self.threshold

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "FrozenTopScorePolicy":
        """Validate and load the only policy shape supported at runtime."""
        if payload.get("schema_version") != 1:
            raise ValueError("unsupported confidence policy schema")
        if payload.get("status") != "frozen":
            raise ValueError("runtime confidence policy must be frozen")
        policy = payload.get("policy")
        if not isinstance(policy, dict):
            raise ValueError("confidence policy is missing")
        expected = ("top_score", "greater_than_or_equal")
        if (policy.get("signal"), policy.get("operator")) != expected:
            raise ValueError("unsupported runtime confidence policy")
        threshold = policy.get("threshold")
        if not isinstance(threshold, int | float) or isinstance(threshold, bool):
            raise ValueError("policy threshold must be numeric")
        return cls(threshold=float(threshold))

    @classmethod
    def from_file(cls, path: Path) -> "FrozenTopScorePolicy":
        """Load a private local policy artifact without logging its contents."""
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_payload(payload)


class EvidenceFirstPipeline:
    """Retrieve passages and enforce abstention before generation."""

    def __init__(
        self,
        *,
        chunks: list[Chunk],
        retriever: Retriever,
        policy: FrozenTopScorePolicy,
    ) -> None:
        if not chunks:
            raise ValueError("at least one chunk is required")
        if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
            raise ValueError("chunk ids must be unique")
        self._retriever = retriever
        self._policy = policy
        self._confidence = ConfidenceAnalyzer(chunks)
        self._chunks = {chunk.chunk_id: chunk for chunk in chunks}

    def retrieve(self, query: str, *, top_k: int = 5) -> RetrievalDecision:
        """Return traceable evidence or abstain without exposing passages."""
        if not query.strip():
            raise ValueError("query cannot be blank")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        results = self._retriever.search(query, top_k=top_k)
        if any(
            self._chunks.get(result.chunk.chunk_id) != result.chunk
            for result in results
        ):
            raise ValueError("retriever returned a chunk outside the configured corpus")
        signals = self._confidence.analyze(query, results)
        if not results or not self._policy.accepts(signals.top_score):
            return RetrievalDecision(
                query=query,
                status=RetrievalStatus.INSUFFICIENT_EVIDENCE,
                signals=signals,
            )
        evidence = tuple(
            Evidence(
                location=EvidenceLocation(
                    chunk_id=result.chunk.chunk_id,
                    document_id=result.chunk.document_id,
                    rank=rank,
                    score=result.score,
                    page=result.chunk.page,
                    section=result.chunk.section,
                ),
                text=result.chunk.text,
            )
            for rank, result in enumerate(results, start=1)
        )
        return RetrievalDecision(
            query=query,
            status=RetrievalStatus.READY,
            signals=signals,
            evidence=evidence,
        )
