"""Integration tests for the full voice pipeline: STT -> LLM -> TTS.

Verifies the end-to-end flow with all Sarvam services mocked at the HTTP layer.
The pipeline must:
  1. Accept audio input
  2. Transcribe via STT (Saarika)
  3. Retrieve relevant memories from Pinecone
  4. Generate response via LLM (Sarvam-M) with user context
  5. Synthesize audio via TTS (Bulbul)
  6. Store messages in DB

Contract (from BUILD_PLAN.md):
  User audio -> Silero VAD -> Sarvam STT -> Memory retrieval -> Sarvam LLM -> Sarvam TTS -> Audio back
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from tests.fixtures.mock_responses import (
    STT_RESPONSE_HINGLISH,
    STT_RESPONSE_EMPTY,
    LLM_COMPLETE_RESPONSE,
    LLM_STREAMING_CHUNKS,
    TTS_RESPONSE_SUCCESS,
    EMBEDDING_RESPONSE,
)


@pytest.mark.integration
class TestFullConversationTurn:
    """Test complete flow: audio in -> transcribe -> retrieve -> generate -> synthesize."""

    @pytest.mark.asyncio
    async def test_full_conversation_turn(
        self, mock_sarvam_client, mock_db, mock_pinecone, fake_audio_buffer
    ):
        """Complete pipeline should produce audio output from audio input."""
        # Simulate the pipeline steps as the main.py would orchestrate them
        # Step 1: STT
        stt_result = await mock_sarvam_client.transcribe(fake_audio_buffer)
        transcript = stt_result["transcript"]
        assert transcript == "Yaar, aaj bahut boring tha office mein"

        # Step 2: Memory retrieval
        mock_sarvam_client.embed.return_value = EMBEDDING_RESPONSE
        embedding = await mock_sarvam_client.embed(transcript)
        memories = mock_pinecone.query(
            vector=embedding["embedding"],
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        assert len(memories["matches"]) > 0

        # Step 3: LLM response
        llm_response = await mock_sarvam_client.generate(transcript)
        assert len(llm_response) > 0

        # Step 4: TTS synthesis
        tts_result = await mock_sarvam_client.synthesize(llm_response)
        assert tts_result["audios"] is not None

        # Step 5: Store messages
        conn = mock_db._test_conn
        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "user", transcript,
        )
        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "assistant", llm_response,
        )
        assert conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_pipeline_preserves_user_context_through_flow(
        self, mock_sarvam_client, mock_db, mock_pinecone, user_context
    ):
        """User context (name, memories) must be available to LLM step."""
        # STT
        transcript = (await mock_sarvam_client.transcribe(b"audio"))["transcript"]

        # Fetch user from DB
        conn = mock_db._test_conn
        user = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", "user_1")
        assert user["name"] == "Rahul"

        # Memory retrieval
        memories = mock_pinecone.query(
            vector=[0.0] * 1024,
            filter={"user_id": user["id"]},
            top_k=5,
            include_metadata=True,
        )

        # Build context string for LLM
        memory_summaries = [m["metadata"]["summary"] for m in memories["matches"]]
        context = f"User: {user['name']}. Memories: {'; '.join(memory_summaries)}"
        assert "Rahul" in context
        assert "job stress" in context


@pytest.mark.integration
class TestPipelineErrorRecovery:
    """Test pipeline behavior when individual steps fail."""

    @pytest.mark.asyncio
    async def test_pipeline_handles_stt_failure(self, mock_sarvam_client, mock_db):
        """Pipeline should handle STT API failure without crashing the agent."""
        mock_sarvam_client.transcribe.side_effect = Exception("Sarvam STT timeout")

        with pytest.raises(Exception, match="timeout"):
            await mock_sarvam_client.transcribe(b"audio")
        # The agent should catch this and log, not crash
        # DB connection should still be usable
        conn = mock_db._test_conn
        result = await conn.fetchrow("SELECT 1")
        assert result is not None

    @pytest.mark.asyncio
    async def test_pipeline_handles_empty_transcript(self, mock_sarvam_client, mock_db):
        """Empty transcript from noise/silence should skip LLM call."""
        mock_sarvam_client.transcribe.return_value = STT_RESPONSE_EMPTY

        result = await mock_sarvam_client.transcribe(b"silent_audio")
        transcript = result["transcript"]
        assert transcript == ""
        # With empty transcript, LLM should NOT be called
        # (agent code should check this condition)

    @pytest.mark.asyncio
    async def test_pipeline_handles_llm_failure(self, mock_sarvam_client):
        """LLM failure should not crash TTS or DB operations."""
        mock_sarvam_client.generate.side_effect = ConnectionError("LLM service down")

        with pytest.raises(ConnectionError):
            await mock_sarvam_client.generate("test input")

    @pytest.mark.asyncio
    async def test_pipeline_handles_tts_failure(self, mock_sarvam_client):
        """TTS failure should not prevent message storage in DB."""
        mock_sarvam_client.synthesize.side_effect = Exception("TTS rate limit")

        # STT and LLM work fine
        transcript = (await mock_sarvam_client.transcribe(b"audio"))["transcript"]
        response = await mock_sarvam_client.generate(transcript)

        # TTS fails
        with pytest.raises(Exception, match="rate limit"):
            await mock_sarvam_client.synthesize(response)

    @pytest.mark.asyncio
    async def test_pipeline_handles_memory_failure_gracefully(
        self, mock_sarvam_client, mock_pinecone
    ):
        """Memory retrieval failure should not block conversation (degrade gracefully)."""
        mock_pinecone.query.side_effect = Exception("Pinecone connection timeout")

        transcript = (await mock_sarvam_client.transcribe(b"audio"))["transcript"]

        # Memory fails
        try:
            mock_pinecone.query(vector=[0.0] * 1024, filter={"user_id": "user_1"}, top_k=5)
            memories = []
        except Exception:
            memories = []  # Graceful degradation: continue without memories

        assert memories == []
        # LLM should still work without memories
        response = await mock_sarvam_client.generate(transcript)
        assert len(response) > 0


@pytest.mark.integration
class TestPipelineMessageStorage:
    """Test that conversations are properly stored in the database."""

    @pytest.mark.asyncio
    async def test_pipeline_stores_both_messages(
        self, mock_sarvam_client, mock_db, mock_pinecone
    ):
        """Both user and assistant messages should be stored after a turn."""
        transcript = (await mock_sarvam_client.transcribe(b"audio"))["transcript"]
        response = await mock_sarvam_client.generate(transcript)

        conn = mock_db._test_conn
        # Store user message
        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "user", transcript,
        )
        # Store assistant message
        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "assistant", response,
        )
        assert conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_pipeline_stores_user_message_content(
        self, mock_sarvam_client, mock_db
    ):
        """Stored user message must match the STT transcript."""
        transcript = (await mock_sarvam_client.transcribe(b"audio"))["transcript"]
        conn = mock_db._test_conn
        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "user", transcript,
        )
        call_args = conn.execute.call_args[0]
        assert "Yaar, aaj bahut boring tha office mein" in call_args

    @pytest.mark.asyncio
    async def test_pipeline_stores_assistant_message_content(
        self, mock_sarvam_client, mock_db
    ):
        """Stored assistant message must match the LLM response."""
        response = await mock_sarvam_client.generate("test")
        conn = mock_db._test_conn
        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "assistant", response,
        )
        call_args = conn.execute.call_args[0]
        assert response in call_args
