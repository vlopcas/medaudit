"""Benchmark deterministic decomposition execution on synthetic corpora."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.query_understanding import verify_input
from medaudit.query_understanding import DeterministicQueryPlanner
from medaudit.rag import (
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
)
from medaudit.retrieval import BM25Index


@dataclass(frozen=True, slots=True)
class ExecutionCase:
    """Golden outcome for one planned query."""

    case_id: str
    query: str
    expected_status: str
    expected_document_ids: tuple[str | None, ...]


@dataclass(frozen=True, slots=True)
class ExecutionDataset:
    """Synthetic corpora and cases required by the benchmark."""

    comparison_chunks: tuple[Chunk, ...]
    temporal_chunks: dict[date, tuple[Chunk, ...]]
    cases: tuple[ExecutionCase, ...]


def load_dataset(path: Path) -> ExecutionDataset:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "decomposition-execution-v1"
        or payload.get("notice")
        != "Conteúdo integralmente sintético, sem reprodução de documentos reais."
    ):
        raise ValueError("unsupported decomposition execution dataset schema")
    comparison_chunks = tuple(Chunk(**item) for item in payload["comparison_chunks"])
    temporal_chunks = {
        date.fromisoformat(snapshot["reference_date"]): tuple(
            Chunk(**item) for item in snapshot["chunks"]
        )
        for snapshot in payload["temporal_snapshots"]
    }
    cases = tuple(
        ExecutionCase(
            case_id=item["id"],
            query=item["query"],
            expected_status=item["status"],
            expected_document_ids=tuple(item["document_ids"]),
        )
        for item in payload["cases"]
    )
    _validate_dataset(comparison_chunks, temporal_chunks, cases)
    return ExecutionDataset(comparison_chunks, temporal_chunks, cases)


def _validate_dataset(
    comparison_chunks: tuple[Chunk, ...],
    temporal_chunks: dict[date, tuple[Chunk, ...]],
    cases: tuple[ExecutionCase, ...],
) -> None:
    if not comparison_chunks or not temporal_chunks or not cases:
        raise ValueError("corpora, temporal snapshots and cases are required")
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("execution case ids must be unique")
    all_chunks = comparison_chunks + tuple(
        chunk for chunks in temporal_chunks.values() for chunk in chunks
    )
    chunk_ids = [chunk.chunk_id for chunk in all_chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("execution chunk ids must be globally unique")
    document_ids = {chunk.document_id for chunk in all_chunks}
    expected_ids = {
        document_id
        for case in cases
        for document_id in case.expected_document_ids
        if document_id is not None
    }
    if unknown := expected_ids - document_ids:
        raise ValueError(f"cases reference unknown document ids: {sorted(unknown)}")


def evaluate(
    dataset: ExecutionDataset,
    *,
    top_k: int = 1,
    threshold: float = 0.1,
) -> dict[str, Any]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    comparison = _build_pipeline(dataset.comparison_chunks, threshold)
    temporal = {
        snapshot_date: _build_pipeline(chunks, threshold)
        for snapshot_date, chunks in dataset.temporal_chunks.items()
    }
    executor = DeterministicDecompositionExecutor(
        comparison_pipeline=comparison,
        temporal_pipeline_for=temporal.__getitem__,
    )
    planner = DeterministicQueryPlanner()
    outcomes: list[dict[str, Any]] = []
    step_correct = 0
    step_count = 0
    temporal_correct = 0
    temporal_count = 0
    for case in dataset.cases:
        execution = executor.execute(planner.plan(case.query), top_k=top_k)
        actual_ids = tuple(
            (
                item.retrieval.evidence[0].location.document_id
                if item.retrieval.evidence
                else None
            )
            for item in execution.steps
        )
        status_correct = execution.status.value == case.expected_status
        documents_correct = actual_ids == case.expected_document_ids
        matches = tuple(
            actual == expected
            for actual, expected in zip(
                actual_ids, case.expected_document_ids, strict=True
            )
        )
        step_correct += sum(matches)
        step_count += len(matches)
        if execution.plan.strategy is not None and execution.plan.strategy.value == (
            "temporal_snapshots"
        ):
            temporal_correct += sum(matches)
            temporal_count += len(matches)
        outcomes.append(
            {
                "case_id": case.case_id,
                "correct": status_correct and documents_correct,
                "status_correct": status_correct,
                "documents_correct": documents_correct,
                "expected_status": case.expected_status,
                "actual_status": execution.status.value,
                "expected_document_ids": list(case.expected_document_ids),
                "actual_document_ids": list(actual_ids),
            }
        )
    return {
        "schema_version": 1,
        "policy": "decomposition-execution-v1",
        "case_count": len(dataset.cases),
        "top_k": top_k,
        "threshold": threshold,
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes)
            / len(outcomes),
            "step_document_accuracy": step_correct / step_count,
            "temporal_step_document_accuracy": temporal_correct / temporal_count,
        },
        "cases": outcomes,
    }


def _build_pipeline(
    chunks: tuple[Chunk, ...], threshold: float
) -> EvidenceFirstPipeline:
    values = list(chunks)
    return EvidenceFirstPipeline(
        chunks=values,
        retriever=BM25Index(values),
        policy=FrozenTopScorePolicy(threshold),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--threshold", type=float, default=0.1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError("decomposition execution output already exists")
    report = evaluate(
        load_dataset(args.dataset),
        top_k=args.top_k,
        threshold=args.threshold,
    )
    report["input_sha256"] = verify_input(args.dataset, args.expected_sha256)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
