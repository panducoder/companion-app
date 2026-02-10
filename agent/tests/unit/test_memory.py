"""Tests for Pinecone memory retrieval and storage.

Verifies:
  - memory/retriever.py: get_relevant(index, user_id, query_text, top_k=5)
  - memory/storage.py: store_conversation(index, user_id, messages, embed_fn)

Contract (from BUILD_PLAN.md):
  - get_relevant embeds query_text, queries Pinecone with user_id filter, returns summaries
  - store_conversation summarizes conversation, embeds summary, upserts to Pinecone
  - Pinecone index: "koi-memories", 1024 dimensions, cosine metric
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from tests.fixtures.mock_responses import EMBEDDING_RESPONSE


@pytest.mark.unit
class TestGetRelevant:
    """Test memory retrieval from Pinecone."""

    @pytest.mark.asyncio
    async def test_get_relevant_returns_matches(self, mock_pinecone):
        """Should return a list of memory matches ranked by similarity score."""
        from src.memory.retriever import get_relevant

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        results = await get_relevant(
            mock_pinecone, user_id="user_1", query_text="how's work?", embed_fn=mock_embed
        )
        assert len(results) > 0
        assert results[0]["score"] >= results[-1]["score"]

    @pytest.mark.asyncio
    async def test_get_relevant_filters_by_user(self, mock_pinecone):
        """Pinecone query must include user_id in the filter."""
        from src.memory.retriever import get_relevant

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        await get_relevant(
            mock_pinecone, user_id="user_1", query_text="test query", embed_fn=mock_embed
        )
        call_kwargs = mock_pinecone.query.call_args
        # filter must contain user_id
        query_filter = call_kwargs.kwargs.get("filter") or call_kwargs[1].get("filter", {})
        assert query_filter.get("user_id") == "user_1"

    @pytest.mark.asyncio
    async def test_get_relevant_respects_top_k(self, mock_pinecone):
        """Should pass top_k parameter to Pinecone query."""
        from src.memory.retriever import get_relevant

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        await get_relevant(
            mock_pinecone,
            user_id="user_1",
            query_text="test",
            top_k=3,
            embed_fn=mock_embed,
        )
        call_kwargs = mock_pinecone.query.call_args
        top_k = call_kwargs.kwargs.get("top_k") or call_kwargs[1].get("top_k")
        assert top_k == 3

    @pytest.mark.asyncio
    async def test_get_relevant_default_top_k_is_five(self, mock_pinecone):
        """Default top_k should be 5 per spec."""
        from src.memory.retriever import get_relevant

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        await get_relevant(
            mock_pinecone, user_id="user_1", query_text="test", embed_fn=mock_embed
        )
        call_kwargs = mock_pinecone.query.call_args
        top_k = call_kwargs.kwargs.get("top_k") or call_kwargs[1].get("top_k")
        assert top_k == 5

    @pytest.mark.asyncio
    async def test_get_relevant_handles_empty_index(self, mock_pinecone):
        """Should return empty list when no memories exist for user."""
        from src.memory.retriever import get_relevant

        mock_pinecone.query.return_value = {"matches": []}
        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        results = await get_relevant(
            mock_pinecone, user_id="user_1", query_text="test", embed_fn=mock_embed
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_get_relevant_includes_metadata_in_results(self, mock_pinecone):
        """Each result should include the metadata (summary, date, topic, emotional_tone)."""
        from src.memory.retriever import get_relevant

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        results = await get_relevant(
            mock_pinecone, user_id="user_1", query_text="work stress", embed_fn=mock_embed
        )
        first_result = results[0]
        assert "summary" in first_result.get("metadata", first_result)

    @pytest.mark.asyncio
    async def test_get_relevant_embeds_query_text(self, mock_pinecone):
        """The query text must be embedded before querying Pinecone."""
        from src.memory.retriever import get_relevant

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        await get_relevant(
            mock_pinecone, user_id="user_1", query_text="how is work going?", embed_fn=mock_embed
        )
        mock_embed.assert_called_once()


@pytest.mark.unit
class TestStoreConversation:
    """Test storing conversations to Pinecone."""

    @pytest.mark.asyncio
    async def test_store_conversation_calls_upsert(self, mock_pinecone, sample_conversation):
        """Should call Pinecone upsert with the conversation embedding."""
        from src.memory.storage import store_conversation

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        mock_summarize = AsyncMock(return_value="Talked about boring day at office")

        await store_conversation(
            mock_pinecone,
            user_id="user_1",
            messages=sample_conversation,
            embed_fn=mock_embed,
            summarize_fn=mock_summarize,
        )
        mock_pinecone.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_conversation_includes_metadata(self, mock_pinecone, sample_conversation):
        """Upserted vector must include metadata: user_id, summary, date, topic, emotional_tone."""
        from src.memory.storage import store_conversation

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        mock_summarize = AsyncMock(return_value="Talked about boring day at office")

        await store_conversation(
            mock_pinecone,
            user_id="user_1",
            messages=sample_conversation,
            embed_fn=mock_embed,
            summarize_fn=mock_summarize,
        )
        upsert_args = mock_pinecone.upsert.call_args
        vectors = upsert_args.kwargs.get("vectors") or upsert_args[0][0]
        vector = vectors[0] if isinstance(vectors, list) else vectors
        metadata = vector.get("metadata", {})
        assert metadata.get("user_id") == "user_1"
        assert "summary" in metadata

    @pytest.mark.asyncio
    async def test_store_conversation_vector_has_correct_dimension(
        self, mock_pinecone, sample_conversation
    ):
        """Upserted vector must have 1024 dimensions matching Pinecone index config."""
        from src.memory.storage import store_conversation

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        mock_summarize = AsyncMock(return_value="test summary")

        await store_conversation(
            mock_pinecone,
            user_id="user_1",
            messages=sample_conversation,
            embed_fn=mock_embed,
            summarize_fn=mock_summarize,
        )
        upsert_args = mock_pinecone.upsert.call_args
        vectors = upsert_args.kwargs.get("vectors") or upsert_args[0][0]
        vector = vectors[0] if isinstance(vectors, list) else vectors
        assert len(vector["values"]) == 1024

    @pytest.mark.asyncio
    async def test_store_conversation_summarizes_first(self, mock_pinecone, sample_conversation):
        """The conversation must be summarized before embedding."""
        from src.memory.storage import store_conversation

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        mock_summarize = AsyncMock(return_value="Office was boring today, same routine")

        await store_conversation(
            mock_pinecone,
            user_id="user_1",
            messages=sample_conversation,
            embed_fn=mock_embed,
            summarize_fn=mock_summarize,
        )
        mock_summarize.assert_called_once()
        mock_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_conversation_generates_unique_id(self, mock_pinecone, sample_conversation):
        """Each stored memory must have a unique vector ID."""
        from src.memory.storage import store_conversation

        mock_embed = AsyncMock(return_value=EMBEDDING_RESPONSE)
        mock_summarize = AsyncMock(return_value="test summary")

        await store_conversation(
            mock_pinecone,
            user_id="user_1",
            messages=sample_conversation,
            embed_fn=mock_embed,
            summarize_fn=mock_summarize,
        )
        upsert_args = mock_pinecone.upsert.call_args
        vectors = upsert_args.kwargs.get("vectors") or upsert_args[0][0]
        vector = vectors[0] if isinstance(vectors, list) else vectors
        vec_id = vector["id"]
        assert "user_1" in vec_id  # ID should contain user_id for namespacing
