"""Compare lexical, dense and hybrid retrieval on calibration only."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.private_bm25 import (
    PrivateEvaluationCase,
    load_private_cases,
    load_private_chunks,
    write_private_report,
)
from medaudit.evaluation.split import validate_split
from medaudit.retrieval import (
    BM25Index,
    DenseIndex,
    E5Embedder,
    EmbeddingCache,
    ReciprocalRankFusion,
    Retriever,
    WeightedRetriever,
)
from medaudit.retrieval.local_model import MODEL_ID, MODEL_REVISION


def evaluate_rankings(
    cases: list[PrivateEvaluationCase], retriever: Retriever, *, top_k: int
) -> list[dict[str, Any]]:
    """Evaluate rankings without retaining query or chunk text."""
    outcomes: list[dict[str, Any]] = []
    for case in cases:
        results = retriever.search(case.question, top_k=top_k)
        relevant = case.relevant_chunk_ids or case.relevant_document_ids
        if not relevant:
            outcomes.append(
                {
                    "case_id": case.case_id,
                    "answerable": False,
                    "returned_result_count": len(results),
                }
            )
            continue
        retrieved = [
            result.chunk.chunk_id
            if case.relevant_chunk_ids
            else result.chunk.document_id
            for result in results
        ]
        ranks = [
            rank
            for rank, unit in enumerate(retrieved, start=1)
            if unit in relevant
        ]
        outcomes.append(
            {
                "case_id": case.case_id,
                "answerable": True,
                "hit": bool(ranks),
                "reciprocal_rank": 1 / min(ranks) if ranks else 0.0,
                "recall": len(set(retrieved).intersection(relevant)) / len(relevant),
            }
        )
    return outcomes


def summarize_outcomes(outcomes: list[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    answerable = [outcome for outcome in outcomes if outcome["answerable"]]
    unanswerable = [outcome for outcome in outcomes if not outcome["answerable"]]
    return {
        "case_count": len(outcomes),
        "answerable_case_count": len(answerable),
        "unanswerable_case_count": len(unanswerable),
        "metrics": {
            f"hit_rate@{top_k}": (
                sum(bool(outcome["hit"]) for outcome in answerable) / len(answerable)
                if answerable
                else 0.0
            ),
            f"recall@{top_k}": (
                sum(float(outcome["recall"]) for outcome in answerable)
                / len(answerable)
                if answerable
                else 0.0
            ),
            "mrr": (
                sum(float(outcome["reciprocal_rank"]) for outcome in answerable)
                / len(answerable)
                if answerable
                else 0.0
            ),
            "unanswerable_nonempty_rate": (
                sum(bool(outcome["returned_result_count"]) for outcome in unanswerable)
                / len(unanswerable)
                if unanswerable
                else None
            ),
        },
        "cases": outcomes,
    }


def benchmark_calibration(
    *,
    snapshots_directory: Path,
    golden_directory: Path,
    review: dict[str, Any],
    split: dict[str, Any],
    embedding_cache_path: Path,
    model_cache_directory: Path,
    top_k: int,
    candidate_depth: int,
    rank_constant: int,
    bm25_weight: float,
    dense_weight: float,
    batch_size: int,
    passage_strategy: str,
) -> dict[str, Any]:
    """Run all retrievers over exactly the calibration partition."""
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    validate_split(split, review)
    selected_ids = set(split["partitions"]["calibration"])
    if not selected_ids:
        raise ValueError("calibration partition is empty")

    embedder = E5Embedder(
        model_cache_directory, passage_strategy=passage_strategy
    )
    cache = EmbeddingCache(
        embedding_cache_path,
        model_id=MODEL_ID,
        model_revision=MODEL_REVISION,
        embedding_strategy=passage_strategy,
    )
    outcomes: dict[str, list[dict[str, Any]]] = {
        "bm25": [],
        "dense": [],
        "hybrid_rrf": [],
    }
    seen_ids: set[str] = set()
    snapshot_count = 0
    for cases_path in sorted(golden_directory.glob("retrieval-*.local.json")):
        cases, case_date = load_private_cases(cases_path)
        selected_cases = [case for case in cases if case.case_id in selected_ids]
        if not selected_cases:
            continue
        suffix = cases_path.name.removeprefix("retrieval-").removesuffix(
            ".local.json"
        )
        chunks_path = snapshots_directory / f"chunks-{suffix}.local.jsonl"
        chunks, chunk_date = load_private_chunks(chunks_path)
        if chunk_date != case_date:
            raise ValueError("snapshot and golden set dates do not match")
        snapshot_count += 1
        seen_ids.update(case.case_id for case in selected_cases)
        matrix = cache.materialize(chunks, embedder, batch_size=batch_size)
        bm25 = BM25Index(chunks)
        dense = DenseIndex(chunks, embedder, passage_embeddings=matrix)
        hybrid = ReciprocalRankFusion(
            [
                WeightedRetriever(bm25, bm25_weight),
                WeightedRetriever(dense, dense_weight),
            ],
            rank_constant=rank_constant,
            candidate_depth=candidate_depth,
        )
        for name, retriever in (
            ("bm25", bm25),
            ("dense", dense),
            ("hybrid_rrf", hybrid),
        ):
            outcomes[name].extend(
                evaluate_rankings(selected_cases, retriever, top_k=top_k)
            )
    if seen_ids != selected_ids:
        raise ValueError("benchmark cases do not match calibration partition")
    return {
        "schema_version": 1,
        "partition": "calibration",
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "configuration": {
            "top_k": top_k,
            "candidate_depth": candidate_depth,
            "rank_constant": rank_constant,
            "bm25_weight": bm25_weight,
            "dense_weight": dense_weight,
            "passage_strategy": passage_strategy,
        },
        "snapshot_count": snapshot_count,
        "retrievers": {
            name: summarize_outcomes(values, top_k=top_k)
            for name, values in outcomes.items()
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--golden-sets", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--embedding-cache", type=Path, required=True)
    parser.add_argument("--model-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-depth", type=int, default=20)
    parser.add_argument("--rank-constant", type=int, default=60)
    parser.add_argument("--bm25-weight", type=float, default=1.0)
    parser.add_argument("--dense-weight", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--passage-strategy",
        choices=("truncate-v1", "token-window-mean-v1"),
        default="truncate-v1",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        review: dict[str, Any] = json.loads(args.review.read_text(encoding="utf-8"))
        split: dict[str, Any] = json.loads(args.split.read_text(encoding="utf-8"))
        report = benchmark_calibration(
            snapshots_directory=args.snapshots,
            golden_directory=args.golden_sets,
            review=review,
            split=split,
            embedding_cache_path=args.embedding_cache,
            model_cache_directory=args.model_cache,
            top_k=args.top_k,
            candidate_depth=args.candidate_depth,
            rank_constant=args.rank_constant,
            bm25_weight=args.bm25_weight,
            dense_weight=args.dense_weight,
            batch_size=args.batch_size,
            passage_strategy=args.passage_strategy,
        )
        write_private_report(report, args.output)
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
                "partition": report["partition"],
                "snapshot_count": report["snapshot_count"],
                "retriever_count": len(report["retrievers"]),
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
