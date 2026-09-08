"""Evaluate the BM25 baseline against a synthetic golden dataset."""

import argparse
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.retrieval import BM25Index


@dataclass(frozen=True, slots=True)
class EvaluationCase:
    case_id: str
    question: str
    relevant_chunk_ids: frozenset[str]
    category: str


def load_chunks(path: Path) -> list[Chunk]:
    payload = _load_json(path)
    chunks = [Chunk(**item) for item in payload["chunks"]]
    _ensure_unique((chunk.chunk_id for chunk in chunks), "chunk_id")
    return chunks


def load_cases(path: Path) -> list[EvaluationCase]:
    payload = _load_json(path)
    cases = [
        EvaluationCase(
            case_id=item["id"],
            question=item["question"],
            relevant_chunk_ids=frozenset(item["relevant_chunk_ids"]),
            category=item["category"],
        )
        for item in payload["cases"]
    ]
    _ensure_unique((case.case_id for case in cases), "case id")
    return cases


def _ensure_unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {label}: {value}")
        seen.add(value)


def validate_references(chunks: list[Chunk], cases: list[EvaluationCase]) -> None:
    """Reject golden cases that reference chunks absent from the corpus."""
    known_chunk_ids = {chunk.chunk_id for chunk in chunks}
    for case in cases:
        unknown = case.relevant_chunk_ids - known_chunk_ids
        if unknown:
            values = ", ".join(sorted(unknown))
            raise ValueError(f"case {case.case_id} references unknown chunks: {values}")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        payload: dict[str, Any] = json.load(source)
    return payload


def evaluate(
    index: BM25Index,
    cases: list[EvaluationCase],
    top_k: int,
    min_score: float = 0.0,
) -> dict[str, Any]:
    reciprocal_rank_sum = 0.0
    hit_count = 0
    recall_sum = 0.0
    answerable_count = 0
    abstention_correct = 0
    unanswerable_count = 0
    case_results: list[dict[str, Any]] = []
    category_values: dict[str, list[float]] = defaultdict(list)

    if not cases:
        raise ValueError("at least one evaluation case is required")

    for case in cases:
        retrieved = index.search(case.question, top_k=top_k, min_score=min_score)
        retrieved_ids = [result.chunk.chunk_id for result in retrieved]
        if not case.relevant_chunk_ids:
            unanswerable_count += 1
            correct_abstention = not retrieved_ids
            abstention_correct += correct_abstention
            case_results.append(
                {
                    "case_id": case.case_id,
                    "category": case.category,
                    "answerable": False,
                    "retrieved_chunk_ids": retrieved_ids,
                    "correct_abstention": correct_abstention,
                }
            )
            continue

        answerable_count += 1
        relevant_retrieved = case.relevant_chunk_ids.intersection(retrieved_ids)
        ranks = [
            rank
            for rank, chunk_id in enumerate(retrieved_ids, start=1)
            if chunk_id in case.relevant_chunk_ids
        ]
        reciprocal_rank = 1 / min(ranks) if ranks else 0.0
        recall = len(relevant_retrieved) / len(case.relevant_chunk_ids)
        reciprocal_rank_sum += reciprocal_rank
        recall_sum += recall
        hit_count += bool(relevant_retrieved)
        category_values[case.category].append(reciprocal_rank)
        case_results.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "answerable": True,
                "retrieved_chunk_ids": retrieved_ids,
                "reciprocal_rank": reciprocal_rank,
                "recall": recall,
            }
        )

    retrieval_metrics = {
        f"hit_rate@{top_k}": hit_count / answerable_count if answerable_count else 0.0,
        f"recall@{top_k}": recall_sum / answerable_count if answerable_count else 0.0,
        "mrr": reciprocal_rank_sum / answerable_count if answerable_count else 0.0,
    }
    return {
        "retriever": "bm25",
        "top_k": top_k,
        "min_score": min_score,
        "case_count": len(cases),
        "answerable_case_count": answerable_count,
        "unanswerable_case_count": unanswerable_count,
        "metrics": {
            **retrieval_metrics,
            "abstention_accuracy": (
                abstention_correct / unanswerable_count if unanswerable_count else None
            ),
        },
        "mrr_by_category": {
            category: sum(values) / len(values)
            for category, values in sorted(category_values.items())
        },
        "cases": case_results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    chunks = load_chunks(args.corpus)
    cases = load_cases(args.cases)
    validate_references(chunks, cases)
    report = evaluate(BM25Index(chunks), cases, args.top_k, args.min_score)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
