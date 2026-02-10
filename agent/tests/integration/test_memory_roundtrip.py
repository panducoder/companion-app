"""
Real round-trip test: store a memory in Pinecone and retrieve it back.

This test hits the REAL Pinecone index ("koi-memories") to verify that
storage.py and retriever.py work end-to-end with consistent embeddings.

Usage:
    cd agent
    python -m tests.integration.test_memory_roundtrip

Requires PINECONE_API_KEY and PINECONE_INDEX to be set (loads from ../.env).
The Sarvam LLM call is bypassed -- we inject a known summary directly
so we can test the embed -> upsert -> query -> match pipeline in isolation.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Load environment from the project root .env
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

# Now safe to import project modules (they read env vars at import time)
from src.memory.retriever import _fallback_embed, _get_index_name, _get_pinecone, get_relevant


TEST_USER_ID = f"test_user_{uuid4().hex[:8]}"
TEST_SUMMARY = "User talked about learning to play guitar and feeling excited about it."
TEST_TOPIC = "hobbies"
TEST_TONE = "excited"


async def _store_test_memory() -> str:
    """Embed a known summary and upsert it directly to Pinecone. Returns the vector ID."""
    embedding = _fallback_embed(TEST_SUMMARY)
    assert len(embedding) == 1024, f"Expected 1024-dim vector, got {len(embedding)}"

    now = datetime.now(timezone.utc)
    vector_id = f"{TEST_USER_ID}_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    metadata = {
        "user_id": TEST_USER_ID,
        "summary": TEST_SUMMARY,
        "topic": TEST_TOPIC,
        "emotional_tone": TEST_TONE,
        "date": now.isoformat(),
        "message_count": 4,
    }

    pc = _get_pinecone()
    index = pc.Index(_get_index_name())

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata,
                }
            ]
        ),
    )
    print(f"[STORE] Upserted vector_id={vector_id} for user={TEST_USER_ID}")
    return vector_id


async def _retrieve_test_memory() -> list[dict]:
    """Query Pinecone via retriever.get_relevant with a related query."""
    # Use a query that overlaps semantically with the stored summary.
    # Since we use hash-based embedding, word overlap drives similarity.
    query = "guitar playing hobby excited"
    memories = await get_relevant(TEST_USER_ID, query, top_k=5)
    return memories


async def _cleanup(vector_id: str) -> None:
    """Delete the test vector so we don't pollute the index."""
    pc = _get_pinecone()
    index = pc.Index(_get_index_name())

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: index.delete(ids=[vector_id]))
    print(f"[CLEANUP] Deleted vector_id={vector_id}")


async def main() -> None:
    print("=" * 60)
    print("Memory round-trip test (real Pinecone)")
    print("=" * 60)

    # Verify env vars are present
    if not os.environ.get("PINECONE_API_KEY"):
        print("ERROR: PINECONE_API_KEY not set. Cannot run round-trip test.")
        sys.exit(1)

    # Step 1: Store
    print("\n--- Step 1: Storing test memory ---")
    vector_id = await _store_test_memory()

    # Give Pinecone a moment to index the vector (eventual consistency)
    print("Waiting for Pinecone indexing...")
    await asyncio.sleep(3)

    # Step 2: Retrieve
    print("\n--- Step 2: Retrieving test memory ---")
    memories = await _retrieve_test_memory()

    # Step 3: Verify
    print(f"\n--- Step 3: Verification ---")
    print(f"Retrieved {len(memories)} memories for user {TEST_USER_ID}")

    found = False
    for i, mem in enumerate(memories):
        print(f"  [{i}] score={mem.get('score', 0):.4f} topic={mem.get('topic')} tone={mem.get('emotional_tone')}")
        print(f"       summary: {mem.get('summary', '')[:80]}...")
        if TEST_SUMMARY[:40] in mem.get("summary", ""):
            found = True

    # Step 4: Cleanup
    print("\n--- Step 4: Cleanup ---")
    await _cleanup(vector_id)

    # Final verdict
    print("\n" + "=" * 60)
    if found:
        print("PASS: Round-trip successful. Stored memory was retrieved.")
    else:
        print("FAIL: Stored memory was NOT found in retrieval results.")
        print("  This may be due to Pinecone indexing delay. Try increasing the sleep.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
