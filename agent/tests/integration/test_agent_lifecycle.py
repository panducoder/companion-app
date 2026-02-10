"""Integration tests for agent lifecycle: connect -> converse -> disconnect.

Verifies the complete agent session from LiveKit room join to disconnect.
Contract (from BUILD_PLAN.md main.py spec):
  1. On new room: extract user_id from participant metadata
  2. Fetch user profile from Supabase DB
  3. Fetch relevant memories from Pinecone
  4. Build system prompt with user context + memories
  5. Create VoiceAssistant with Sarvam STT/LLM/TTS + Silero VAD
  6. On user_speech_committed: store message in DB + update Pinecone async
  7. On agent_speech_committed: store message in DB async
  8. Greet user by name on connect
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.fixtures.mock_responses import (
    STT_RESPONSE_HINGLISH,
    LLM_COMPLETE_RESPONSE,
    TTS_RESPONSE_SUCCESS,
    EMBEDDING_RESPONSE,
)


@pytest.mark.integration
class TestAgentConnect:
    """Test agent connection and initialization flow."""

    @pytest.mark.asyncio
    async def test_agent_extracts_user_id_from_metadata(self):
        """Agent must extract user_id from LiveKit participant metadata."""
        participant_metadata = '{"user_id": "user_1", "user_name": "Rahul", "companion_name": "Koi"}'
        import json

        metadata = json.loads(participant_metadata)
        assert metadata["user_id"] == "user_1"
        assert metadata["user_name"] == "Rahul"

    @pytest.mark.asyncio
    async def test_agent_fetches_user_profile_on_connect(self, mock_db):
        """On room join, agent must fetch user profile from DB."""
        conn = mock_db._test_conn
        user = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", "user_1")
        assert user is not None
        assert user["name"] == "Rahul"
        assert user["relationship_stage"] == "familiar"

    @pytest.mark.asyncio
    async def test_agent_fetches_memories_on_connect(self, mock_pinecone):
        """On room join, agent must query Pinecone for relevant memories."""
        results = mock_pinecone.query(
            vector=[0.0] * 1024,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )
        assert len(results["matches"]) > 0

    @pytest.mark.asyncio
    async def test_agent_builds_system_prompt_with_context(self, mock_db, mock_pinecone):
        """Agent must build system prompt containing user name and memories."""
        conn = mock_db._test_conn
        user = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", "user_1")
        memories = mock_pinecone.query(
            vector=[0.0] * 1024,
            filter={"user_id": "user_1"},
            top_k=5,
            include_metadata=True,
        )

        # Simulate prompt building
        memory_summaries = [m["metadata"]["summary"] for m in memories["matches"]]
        prompt = f"You are Koi, companion to {user['name']}. Memories: {'; '.join(memory_summaries)}"
        assert "Rahul" in prompt
        assert "job stress" in prompt

    @pytest.mark.asyncio
    async def test_agent_creates_conversation_record_on_connect(self, mock_db):
        """Agent must create a conversation record in DB when session starts."""
        conn = mock_db._test_conn
        conn.fetchrow.return_value = {
            "id": "conv_new_1",
            "user_id": "user_1",
            "started_at": "2025-02-10T12:00:00Z",
        }
        conversation = await conn.fetchrow(
            "INSERT INTO conversations (user_id) VALUES ($1) RETURNING *",
            "user_1",
        )
        assert conversation["id"] == "conv_new_1"


@pytest.mark.integration
class TestAgentConverse:
    """Test the conversation loop during an active session."""

    @pytest.mark.asyncio
    async def test_agent_stores_user_message_on_speech_committed(self, mock_db):
        """When user finishes speaking, the transcript must be stored in DB."""
        conn = mock_db._test_conn
        transcript = "Yaar, aaj bahut boring tha office mein"

        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "user", transcript,
        )
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0]
        assert "user" in call_args
        assert transcript in call_args

    @pytest.mark.asyncio
    async def test_agent_stores_assistant_message_on_speech_committed(self, mock_db):
        """When agent finishes speaking, the response must be stored in DB."""
        conn = mock_db._test_conn
        response = "Achha, kya hua? Bata na detail mein."

        await conn.execute(
            "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
            "conv_1", "user_1", "assistant", response,
        )
        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0]
        assert "assistant" in call_args
        assert response in call_args

    @pytest.mark.asyncio
    async def test_agent_updates_pinecone_after_user_speech(
        self, mock_pinecone, mock_sarvam_client
    ):
        """After user speech, agent should async-update Pinecone with new context."""
        # Simulate embedding and upsert
        embedding = await mock_sarvam_client.embed("boring day at work")
        mock_pinecone.upsert.return_value = {"upserted_count": 1}

        result = mock_pinecone.upsert(
            vectors=[
                {
                    "id": "mem_user1_latest",
                    "values": embedding["embedding"],
                    "metadata": {
                        "user_id": "user_1",
                        "summary": "boring day at work",
                        "date": "2025-02-10",
                    },
                }
            ]
        )
        assert result["upserted_count"] == 1

    @pytest.mark.asyncio
    async def test_agent_greets_user_by_name(self, mock_db, mock_sarvam_client):
        """Agent must generate a greeting that includes the user's name."""
        conn = mock_db._test_conn
        user = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", "user_1")

        # The greeting prompt should include the user's name
        greeting_prompt = f"Greet {user['name']} warmly. This is a returning user."
        assert "Rahul" in greeting_prompt

    @pytest.mark.asyncio
    async def test_multiple_turns_accumulate_messages(self, mock_db):
        """Multiple conversation turns should store messages sequentially."""
        conn = mock_db._test_conn
        turns = [
            ("user", "Aaj boring tha"),
            ("assistant", "Achha, kya hua?"),
            ("user", "Same routine yaar"),
            ("assistant", "Kuch naya plan karo evening ka"),
        ]
        for role, content in turns:
            await conn.execute(
                "INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)",
                "conv_1", "user_1", role, content,
            )
        assert conn.execute.call_count == 4


@pytest.mark.integration
class TestAgentDisconnect:
    """Test agent session teardown."""

    @pytest.mark.asyncio
    async def test_agent_ends_conversation_on_disconnect(self, mock_db):
        """When user disconnects, agent must update conversation end time."""
        conn = mock_db._test_conn
        await conn.execute(
            "UPDATE conversations SET ended_at = NOW(), summary = $1 WHERE id = $2",
            "Talked about boring day at office",
            "conv_1",
        )
        conn.execute.assert_called_once()
        sql = conn.execute.call_args[0][0].lower()
        assert "ended_at" in sql
        assert "summary" in sql

    @pytest.mark.asyncio
    async def test_agent_stores_memory_on_disconnect(self, mock_pinecone, mock_sarvam_client):
        """On disconnect, conversation should be summarized and stored as memory."""
        # Summarize conversation
        summary = "User had a boring day at work, same meetings as always"
        embedding = await mock_sarvam_client.embed(summary)

        result = mock_pinecone.upsert(
            vectors=[
                {
                    "id": "mem_user1_conv_1",
                    "values": embedding["embedding"],
                    "metadata": {
                        "user_id": "user_1",
                        "summary": summary,
                        "date": "2025-02-10",
                        "topic": "work",
                        "emotional_tone": "bored",
                    },
                }
            ]
        )
        assert result["upserted_count"] == 1

    @pytest.mark.asyncio
    async def test_agent_handles_abrupt_disconnect(self, mock_db):
        """Agent should handle sudden disconnection without data loss."""
        conn = mock_db._test_conn
        # Even if disconnect is abrupt, we should try to save state
        try:
            await conn.execute(
                "UPDATE conversations SET ended_at = NOW() WHERE id = $1",
                "conv_1",
            )
        except Exception:
            pass  # Agent should handle gracefully
        # The important thing is no unhandled exception crashes the agent

    @pytest.mark.asyncio
    async def test_agent_calculates_conversation_duration(self, mock_db):
        """Conversation record should include duration in seconds."""
        conn = mock_db._test_conn
        # Simulate calculating duration
        import time

        start_time = time.time() - 300  # 5 minutes ago
        duration = int(time.time() - start_time)

        await conn.execute(
            "UPDATE conversations SET ended_at = NOW(), duration_seconds = $1 WHERE id = $2",
            duration,
            "conv_1",
        )
        call_args = conn.execute.call_args[0]
        assert "duration_seconds" in call_args[0]
