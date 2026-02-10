"""
Memory retrieval from Pinecone vector database.

Fetches relevant past conversation memories for a given user,
embedding the query text via the Sarvam embedding endpoint
and querying Pinecone with a user_id metadata filter.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx
from pinecone import Pinecone
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("koi.agent.memory")

_pinecone_client: Pinecone | None = None
_EMBED_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
SARVAM_BASE_URL = "https://api.sarvam.ai"


def _get_pinecone() -> Pinecone:
    """Return the shared Pinecone client singleton."""
    global _pinecone_client
    if _pinecone_client is None:
        api_key = os.environ.get("PINECONE_API_KEY", "")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY environment variable is not set")
        _pinecone_client = Pinecone(api_key=api_key)
    return _pinecone_client


def _get_index_name() -> str:
    return os.environ.get("PINECONE_INDEX", "koi-memories")


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, asyncio.TimeoutError)),
    reraise=True,
)
async def _embed_text(text: str) -> list[float]:
    """
    Embed text using Sarvam's embedding endpoint.

    Returns a 1024-dimensional float vector.
    Falls back to a simple hash-based vector if the API fails.
    """
    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key:
        logger.warning("SARVAM_API_KEY not set, using fallback embedding")
        return _fallback_embed(text)

    async with httpx.AsyncClient(timeout=_EMBED_TIMEOUT) as client:
        resp = await client.post(
            f"{SARVAM_BASE_URL}/embed",
            json={"model": "sarvam-embed", "input": [text]},
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        embeddings = data.get("data", [])
        if embeddings and "embedding" in embeddings[0]:
            return embeddings[0]["embedding"]

        logger.warning("Unexpected embedding response shape, using fallback")
        return _fallback_embed(text)


def _fallback_embed(text: str) -> list[float]:
    """
    Simple deterministic embedding for MVP fallback.

    Produces a 1024-dim vector by hashing character n-grams.
    Not production quality -- exists so the system works without
    the embedding API.
    """
    import hashlib

    vec = [0.0] * 1024
    words = text.lower().split()
    for i, word in enumerate(words):
        h = hashlib.md5(word.encode()).hexdigest()  # noqa: S324
        idx = int(h[:4], 16) % 1024
        vec[idx] += 1.0 / (1 + i * 0.1)

    # Normalize
    magnitude = sum(v * v for v in vec) ** 0.5
    if magnitude > 0:
        vec = [v / magnitude for v in vec]
    return vec


async def get_relevant(
    user_id: str,
    query_text: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Retrieve relevant memories for a user.

    Parameters
    ----------
    user_id : str
        The user's UUID.
    query_text : str
        Text to use for semantic search (usually last user utterance).
    top_k : int
        Maximum number of memories to return.

    Returns
    -------
    list[dict]
        Each dict has keys: summary, date, topic, emotional_tone, score.
    """
    try:
        query_vector = await _embed_text(query_text)
    except Exception:
        logger.exception("Failed to embed query text, returning empty memories")
        return []

    try:
        pc = _get_pinecone()
        index = pc.Index(_get_index_name())

        # Pinecone query is synchronous -- run in executor to avoid blocking
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: index.query(
                vector=query_vector,
                filter={"user_id": {"$eq": user_id}},
                top_k=top_k,
                include_metadata=True,
            ),
        )
    except Exception:
        logger.exception("Pinecone query failed", extra={"user_id": user_id})
        return []

    memories: list[dict[str, Any]] = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        memories.append(
            {
                "summary": meta.get("summary", ""),
                "date": meta.get("date", ""),
                "topic": meta.get("topic", ""),
                "emotional_tone": meta.get("emotional_tone", ""),
                "score": match.get("score", 0.0),
            }
        )

    logger.info(
        "Memories retrieved",
        extra={"user_id": user_id, "count": len(memories)},
    )
    return memories
