"""Serialize local ingestion results into a versioned JSON representation."""

import json
from dataclasses import asdict

from medaudit.ingestion.pipeline import IngestionResult


def serialize_result(result: IngestionResult) -> str:
    """Return deterministic JSON suitable for an ignored processed artifact."""
    payload = asdict(result)
    document = payload["parsed_document"]["document"]
    document["effective_from"] = document["effective_from"].isoformat()
    if document["effective_until"] is not None:
        document["effective_until"] = document["effective_until"].isoformat()
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
