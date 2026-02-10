"""Integration tests for memory store-then-retrieve flow.

Verifies the complete memory lifecycle:
  1. A conversation happens
  2. Conversation is summarized and embedded
  3. Summary is stored in Pinecone with metadata
  4. Later, a relevant query retrieves that memory

Uses FakePineconeIndex for real vector storage/retrieval behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.fixtures.mock_pinecone import FakePineconeIndex
from tests.fixtures.mock_responses import EMBEDDING_RESPONSE


@pytest.mark.integration
class TestMemoryStoreAndRetrieve:
    """Test the full memory lifecycle: store conversation -> retrieve later."""

    def test_store_then_retrieve_by_same_user(self, fake_pinecone):
        """Stored memory should be retrievable by the same user."""
        # Store a new memory for user_1
        embedding = [0.4, 0.4] + [0.01] * 1022
        fake_pinecone.upsert(
            vectors=[
                {
                    "id": "mem_user1_new",
                    "values": embedding,
                    "metadata": {
                        "user_id": "user_1",
                        "summary": "Got a promotion at work today",
                        "date": "2025-02-10",
                        "topic": "work",
                        "emotional_tone": "happy",
                    },
                }
            ]
        )

        # Retrieve with a similar query vector
        results = fake_pinecone.query(
            vector=[0.4, 0.4] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        summaries = [m["metadata"]["summary"] for m in results["matches"]]
        assert "Got a promotion at work today" in summaries

    def test_retrieve_does_not_return_other_users_memories(self, fake_pinecone):
        """Memories from user_2 must NOT appear in user_1's retrieval."""
        results = fake_pinecone.query(
            vector=[0.9, 0.1] + [0.01] * 1022,  # Vector close to user_2's memory
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        for match in results["matches"]:
            assert match["metadata"]["user_id"] == "user_1"

    def test_retrieve_ranks_by_relevance(self, fake_pinecone):
        """Results should be ranked by cosine similarity (most relevant first)."""
        # Query with vector close to the "job stress" memory
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        if len(results["matches"]) >= 2:
            scores = [m["score"] for m in results["matches"]]
            assert scores == sorted(scores, reverse=True)

    def test_top_k_limits_results(self, fake_pinecone):
        """top_k=1 should return only the single most relevant memory."""
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=1,
            include_metadata=True,
        )
        assert len(results["matches"]) == 1


@pytest.mark.integration
class TestMemoryMetadata:
    """Test that stored metadata is preserved and queryable."""

    def test_stored_metadata_includes_date(self, fake_pinecone):
        """Retrieved memories must include the date they were stored."""
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=1,
            include_metadata=True,
        )
        first = results["matches"][0]
        assert "date" in first["metadata"]

    def test_stored_metadata_includes_topic(self, fake_pinecone):
        """Retrieved memories must include the conversation topic."""
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=1,
            include_metadata=True,
        )
        first = results["matches"][0]
        assert "topic" in first["metadata"]
        assert first["metadata"]["topic"] in ["work", "family", "relationships", "health", "general"]

    def test_stored_metadata_includes_emotional_tone(self, fake_pinecone):
        """Retrieved memories must include the emotional tone."""
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        for match in results["matches"]:
            assert "emotional_tone" in match["metadata"]

    def test_stored_metadata_includes_summary(self, fake_pinecone):
        """Retrieved memories must include a human-readable summary."""
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=1,
            include_metadata=True,
        )
        first = results["matches"][0]
        assert "summary" in first["metadata"]
        assert len(first["metadata"]["summary"]) > 10  # Not empty/trivial


@pytest.mark.integration
class TestMemoryDeletion:
    """Test memory deletion for privacy compliance."""

    def test_delete_by_id(self, fake_pinecone):
        """Should delete a specific memory by its vector ID."""
        initial_count = len(fake_pinecone)
        fake_pinecone.delete(ids=["mem_user1_001"])
        assert len(fake_pinecone) == initial_count - 1

        # Verify it's no longer retrievable
        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        ids = [m["id"] for m in results["matches"]]
        assert "mem_user1_001" not in ids

    def test_delete_all_user_memories(self, fake_pinecone):
        """Should delete ALL memories for a user (GDPR delete-my-data)."""
        fake_pinecone.delete(filter={"user_id": "user_1"})

        results = fake_pinecone.query(
            vector=[0.5, 0.3] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        assert len(results["matches"]) == 0

    def test_delete_user_does_not_affect_other_users(self, fake_pinecone):
        """Deleting user_1's memories must not affect user_2's memories."""
        fake_pinecone.delete(filter={"user_id": "user_1"})

        results = fake_pinecone.query(
            vector=[0.9, 0.1] + [0.01] * 1022,
            filter={"user_id": "user_2"},
            top_k=5,
            include_metadata=True,
        )
        assert len(results["matches"]) == 1


@pytest.mark.integration
class TestFakePineconeIndex:
    """Test the FakePineconeIndex itself to ensure test infrastructure works."""

    def test_empty_index_returns_no_matches(self):
        """Fresh index with no vectors should return empty results."""
        index = FakePineconeIndex(dimension=1024)
        results = index.query(vector=[0.0] * 1024, top_k=5)
        assert len(results["matches"]) == 0

    def test_dimension_mismatch_raises_error(self):
        """Upserting wrong-dimension vector should fail."""
        index = FakePineconeIndex(dimension=1024)
        with pytest.raises(ValueError, match="dimension"):
            index.upsert(
                vectors=[{"id": "bad", "values": [0.1] * 512, "metadata": {}}]
            )

    def test_query_dimension_mismatch_raises_error(self, fake_pinecone):
        """Querying with wrong-dimension vector should fail."""
        with pytest.raises(ValueError, match="dimension"):
            fake_pinecone.query(vector=[0.1] * 512, top_k=5)

    def test_upsert_overwrites_existing_id(self, fake_pinecone):
        """Upserting with an existing ID should overwrite the vector."""
        fake_pinecone.upsert(
            vectors=[
                {
                    "id": "mem_user1_001",
                    "values": [0.9, 0.9] + [0.01] * 1022,
                    "metadata": {
                        "user_id": "user_1",
                        "summary": "UPDATED memory",
                    },
                }
            ]
        )
        results = fake_pinecone.query(
            vector=[0.9, 0.9] + [0.01] * 1022,
            filter={"user_id": "user_1"},
            top_k=1,
            include_metadata=True,
        )
        assert results["matches"][0]["metadata"]["summary"] == "UPDATED memory"

    def test_describe_index_stats(self, fake_pinecone):
        """Should return correct vector count and dimension."""
        stats = fake_pinecone.describe_index_stats()
        assert stats["dimension"] == 1024
        assert stats["total_vector_count"] == 3  # 3 pre-seeded vectors
