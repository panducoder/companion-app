"""In-memory fake Pinecone index for testing memory retrieval and storage.

This simulates the Pinecone vector DB without any network calls.
It stores vectors in a dict and does brute-force cosine similarity
for queries, matching the real Pinecone API surface used by the agent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class QueryMatch:
    """Single result from a Pinecone query."""

    id: str
    score: float
    metadata: dict


@dataclass
class QueryResult:
    """Pinecone query response shape."""

    matches: list[QueryMatch]

    def to_dict(self) -> dict:
        return {
            "matches": [
                {"id": m.id, "score": m.score, "metadata": m.metadata}
                for m in self.matches
            ]
        }


@dataclass
class UpsertResult:
    """Pinecone upsert response shape."""

    upserted_count: int

    def to_dict(self) -> dict:
        return {"upserted_count": self.upserted_count}


@dataclass
class StoredVector:
    """Internal representation of a stored vector."""

    id: str
    values: list[float]
    metadata: dict


class FakePineconeIndex:
    """In-memory Pinecone index that supports query and upsert.

    Usage in tests:
        index = FakePineconeIndex(dimension=1024)
        index.upsert(vectors=[{
            "id": "mem_1",
            "values": [0.1] * 1024,
            "metadata": {"user_id": "user_1", "summary": "Talked about work"}
        }])
        results = index.query(vector=[0.1] * 1024, top_k=5, filter={"user_id": "user_1"})
    """

    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self._vectors: dict[str, StoredVector] = {}

    def upsert(self, vectors: list[dict], **kwargs) -> dict:
        """Store vectors. Overwrites existing IDs."""
        count = 0
        for v in vectors:
            vid = v["id"]
            values = v["values"]
            metadata = v.get("metadata", {})
            if len(values) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch: got {len(values)}, expected {self.dimension}"
                )
            self._vectors[vid] = StoredVector(id=vid, values=values, metadata=metadata)
            count += 1
        return UpsertResult(upserted_count=count).to_dict()

    def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filter: dict | None = None,
        include_metadata: bool = True,
        **kwargs,
    ) -> dict:
        """Find top_k most similar vectors, optionally filtered by metadata."""
        if len(vector) != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch: got {len(vector)}, expected {self.dimension}"
            )

        candidates = list(self._vectors.values())

        # Apply metadata filter
        if filter:
            candidates = [
                v
                for v in candidates
                if all(v.metadata.get(k) == val for k, val in filter.items())
            ]

        # Compute cosine similarity and rank
        scored = []
        for v in candidates:
            sim = self._cosine_similarity(vector, v.values)
            scored.append((v, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        matches = [
            QueryMatch(
                id=v.id,
                score=round(score, 4),
                metadata=v.metadata if include_metadata else {},
            )
            for v, score in top
        ]

        return QueryResult(matches=matches).to_dict()

    def delete(self, ids: list[str] | None = None, filter: dict | None = None, **kwargs) -> dict:
        """Delete vectors by ID or metadata filter."""
        deleted = 0
        if ids:
            for vid in ids:
                if vid in self._vectors:
                    del self._vectors[vid]
                    deleted += 1
        elif filter:
            to_delete = [
                vid
                for vid, v in self._vectors.items()
                if all(v.metadata.get(k) == val for k, val in filter.items())
            ]
            for vid in to_delete:
                del self._vectors[vid]
                deleted += 1
        return {"deleted": deleted}

    def describe_index_stats(self) -> dict:
        """Return index statistics."""
        return {
            "dimension": self.dimension,
            "total_vector_count": len(self._vectors),
        }

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def __len__(self) -> int:
        return len(self._vectors)

    def reset(self) -> None:
        """Clear all stored vectors. Useful for test teardown."""
        self._vectors.clear()
