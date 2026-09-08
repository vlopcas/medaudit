"""Evaluate BM25 on private JSONL chunks without printing private details."""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.retrieval import BM25Index


@dataclass(frozen=True, slots=True)
class PrivateEvaluationCase:
    case_id: str
    question: str
    category: str
    relevant_chunk_ids: frozenset[str] = frozenset()
    relevant_document_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if self.relevant_chunk_ids and self.relevant_document_ids:
            raise ValueError("a case must use chunk or document relevance, not both")


def load_private_chunks(path: Path) -> tuple[list[Chunk], str]:
    chunks: list[Chunk] = []
    reference_dates: set[str] = set()
    with path.open(encoding="utf-8") as source:
        for line in source:
            payload = json.loads(line)
            if payload.get("schema_version") != 1:
                raise ValueError("unsupported private chunk schema")
            chunks.append(Chunk(**payload["chunk"]))
            reference_dates.add(payload["reference_date"])
    if not chunks:
        raise ValueError("at least one private chunk is required")
    if len(reference_dates) != 1:
        raise ValueError("chunks must share one reference date")
    if len({chunk.chunk_id for chunk in chunks}) != len(chunks):
        raise ValueError("duplicate chunk ids")
    return chunks, reference_dates.pop()


def load_private_cases(path: Path) -> tuple[list[PrivateEvaluationCase], str]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported private evaluation schema")
    cases = [
        PrivateEvaluationCase(
            case_id=item["id"],
            question=item["question"],
            category=item["category"],
            relevant_chunk_ids=frozenset(item.get("relevant_chunk_ids", ())),
            relevant_document_ids=frozenset(item.get("relevant_document_ids", ())),
        )
        for item in payload["cases"]
    ]
    if not cases:
        raise ValueError("at least one private evaluation case is required")
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("duplicate private evaluation case ids")
    return cases, payload["reference_date"]


def validate_private_references(
    chunks: list[Chunk], cases: list[PrivateEvaluationCase]
) -> None:
    known_chunks = {chunk.chunk_id for chunk in chunks}
    known_documents = {chunk.document_id for chunk in chunks}
    for case in cases:
        if case.relevant_chunk_ids - known_chunks:
            raise ValueError("evaluation case references unknown chunks")
        if case.relevant_document_ids - known_documents:
            raise ValueError("evaluation case references unknown documents")


def evaluate_private(
    chunks: list[Chunk],
    cases: list[PrivateEvaluationCase],
    *,
    top_k: int,
    min_score: float,
) -> dict[str, Any]:
    index = BM25Index(chunks)
    hit_count = 0
    reciprocal_rank_sum = 0.0
    recall_sum = 0.0
    answerable = 0
    unanswerable = 0
    correct_abstentions = 0
    categories: defaultdict[str, list[float]] = defaultdict(list)
    details: list[dict[str, Any]] = []
    for case in cases:
        results = index.search(case.question, top_k=top_k, min_score=min_score)
        if not case.relevant_chunk_ids and not case.relevant_document_ids:
            unanswerable += 1
            correct = not results
            correct_abstentions += correct
            details.append({"case_id": case.case_id, "correct_abstention": correct})
            continue
        answerable += 1
        retrieved_units = [
            result.chunk.chunk_id
            if case.relevant_chunk_ids
            else result.chunk.document_id
            for result in results
        ]
        relevant = case.relevant_chunk_ids or case.relevant_document_ids
        unique_retrieved = set(retrieved_units)
        ranks = [
            rank
            for rank, unit in enumerate(retrieved_units, start=1)
            if unit in relevant
        ]
        reciprocal_rank = 1 / min(ranks) if ranks else 0.0
        recall = len(unique_retrieved.intersection(relevant)) / len(relevant)
        hit_count += bool(ranks)
        reciprocal_rank_sum += reciprocal_rank
        recall_sum += recall
        categories[case.category].append(reciprocal_rank)
        details.append(
            {
                "case_id": case.case_id,
                "reciprocal_rank": reciprocal_rank,
                "recall": recall,
            }
        )
    return {
        "schema_version": 1,
        "retriever": "bm25",
        "top_k": top_k,
        "min_score": min_score,
        "case_count": len(cases),
        "answerable_case_count": answerable,
        "unanswerable_case_count": unanswerable,
        "metrics": {
            f"hit_rate@{top_k}": hit_count / answerable if answerable else 0.0,
            f"recall@{top_k}": recall_sum / answerable if answerable else 0.0,
            "mrr": reciprocal_rank_sum / answerable if answerable else 0.0,
            "abstention_accuracy": (
                correct_abstentions / unanswerable if unanswerable else None
            ),
        },
        "mrr_by_category": {
            category: sum(values) / len(values)
            for category, values in sorted(categories.items())
        },
        "cases": details,
    }


def write_private_report(report: dict[str, Any], output: Path) -> None:
    if not output.name.endswith(".local.json"):
        raise ValueError("evaluation output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        chunks, chunk_date = load_private_chunks(args.chunks)
        cases, case_date = load_private_cases(args.cases)
        if chunk_date != case_date:
            raise ValueError("evaluation and chunks use different reference dates")
        validate_private_references(chunks, cases)
        report = evaluate_private(
            chunks, cases, top_k=args.top_k, min_score=args.min_score
        )
        write_private_report(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    summary = {
        "retriever": report["retriever"],
        "top_k": report["top_k"],
        "min_score": report["min_score"],
        "case_count": report["case_count"],
        "answerable_case_count": report["answerable_case_count"],
        "unanswerable_case_count": report["unanswerable_case_count"],
        "metrics": report["metrics"],
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
