"""Tests for Supabase/PostgreSQL database client.

Verifies db/client.py functions:
  - get_user(pool, user_id) -> dict | None
  - store_message(pool, conversation_id, user_id, role, content) -> None
  - create_conversation(pool, user_id) -> conversation record
  - end_conversation(pool, conversation_id, summary) -> None

Contract (from BUILD_PLAN.md):
  - Uses asyncpg pool with acquire() context manager
  - get_user queries profiles table by UUID
  - store_message inserts into messages table
  - create_conversation inserts into conversations table
  - end_conversation updates end time and summary
"""

import pytest
from unittest.mock import AsyncMock, call


@pytest.mark.unit
class TestGetUser:
    """Test user profile retrieval from profiles table."""

    @pytest.mark.asyncio
    async def test_get_user_returns_profile(self, mock_db):
        """Should return user profile dict with expected fields."""
        from src.db.client import get_user

        user = await get_user(mock_db, "user_1")
        assert user is not None
        assert user["name"] == "Rahul"
        assert user["companion_name"] == "Koi"
        assert user["relationship_stage"] == "familiar"

    @pytest.mark.asyncio
    async def test_get_user_returns_none_for_missing(self, mock_db_no_user):
        """Should return None for non-existent user ID."""
        from src.db.client import get_user

        user = await get_user(mock_db_no_user, "nonexistent_user")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_queries_by_id(self, mock_db):
        """Should query the profiles table with the correct user_id parameter."""
        from src.db.client import get_user

        await get_user(mock_db, "user_1")
        conn = mock_db._test_conn
        conn.fetchrow.assert_called_once()
        # The SQL should reference the profiles table and use parameterized query
        call_args = conn.fetchrow.call_args
        sql = call_args[0][0]
        assert "profiles" in sql.lower() or "profile" in sql.lower()
        # user_id should be passed as parameter, not string-concatenated
        assert "user_1" in call_args[0] or "user_1" in call_args.kwargs.values()

    @pytest.mark.asyncio
    async def test_get_user_handles_connection_error(self, mock_db_connection_error):
        """Should raise or propagate ConnectionError when DB is unreachable."""
        from src.db.client import get_user

        with pytest.raises((ConnectionError, Exception)):
            await get_user(mock_db_connection_error, "user_1")

    @pytest.mark.asyncio
    async def test_get_user_includes_subscription_status(self, mock_db):
        """Returned profile must include subscription_status field."""
        from src.db.client import get_user

        user = await get_user(mock_db, "user_1")
        assert "subscription_status" in user


@pytest.mark.unit
class TestStoreMessage:
    """Test message storage in messages table."""

    @pytest.mark.asyncio
    async def test_store_message_inserts_row(self, mock_db):
        """Should execute an INSERT into the messages table."""
        from src.db.client import store_message

        await store_message(
            mock_db,
            conversation_id="conv_1",
            user_id="user_1",
            role="user",
            content="Yaar aaj boring tha",
        )
        conn = mock_db._test_conn
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_message_passes_role(self, mock_db):
        """The role parameter ('user' or 'assistant') must be passed to the INSERT."""
        from src.db.client import store_message

        await store_message(
            mock_db,
            conversation_id="conv_1",
            user_id="user_1",
            role="assistant",
            content="Achha, kya hua?",
        )
        conn = mock_db._test_conn
        call_args = conn.execute.call_args[0]
        # Role should be in the parameters
        assert "assistant" in call_args

    @pytest.mark.asyncio
    async def test_store_message_passes_content(self, mock_db):
        """The message content must be stored in the database."""
        from src.db.client import store_message

        content = "Yaar aaj boring tha office mein"
        await store_message(
            mock_db,
            conversation_id="conv_1",
            user_id="user_1",
            role="user",
            content=content,
        )
        conn = mock_db._test_conn
        call_args = conn.execute.call_args[0]
        assert content in call_args

    @pytest.mark.asyncio
    async def test_store_message_uses_parameterized_query(self, mock_db):
        """SQL must use parameterized inputs, never string concatenation."""
        from src.db.client import store_message

        await store_message(
            mock_db,
            conversation_id="conv_1",
            user_id="user_1",
            role="user",
            content="test message",
        )
        conn = mock_db._test_conn
        sql = conn.execute.call_args[0][0]
        # Should use $1, $2, etc. placeholders (asyncpg style)
        assert "$" in sql


@pytest.mark.unit
class TestCreateConversation:
    """Test conversation creation."""

    @pytest.mark.asyncio
    async def test_create_conversation_returns_record(self, mock_db):
        """Should return the newly created conversation record."""
        from src.db.client import create_conversation

        # Set up fetchrow to return a new conversation
        mock_db._test_conn.fetchrow.return_value = {
            "id": "conv_new_1",
            "user_id": "user_1",
            "started_at": "2025-02-10T12:00:00Z",
        }
        result = await create_conversation(mock_db, "user_1")
        assert result is not None
        assert "id" in result

    @pytest.mark.asyncio
    async def test_create_conversation_sets_user_id(self, mock_db):
        """The user_id must be associated with the new conversation."""
        from src.db.client import create_conversation

        mock_db._test_conn.fetchrow.return_value = {
            "id": "conv_new_1",
            "user_id": "user_1",
            "started_at": "2025-02-10T12:00:00Z",
        }
        await create_conversation(mock_db, "user_1")
        conn = mock_db._test_conn
        # Verify the SQL references conversations table
        call_args = conn.fetchrow.call_args[0]
        sql = call_args[0].lower()
        assert "conversations" in sql or "conversation" in sql


@pytest.mark.unit
class TestEndConversation:
    """Test conversation finalization."""

    @pytest.mark.asyncio
    async def test_end_conversation_with_summary(self, mock_db):
        """Should update conversation record with end time and summary."""
        from src.db.client import end_conversation

        await end_conversation(mock_db, "conv_1", summary="Talked about work stress")
        conn = mock_db._test_conn
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_conversation_passes_summary(self, mock_db):
        """The summary text must be stored in the update."""
        from src.db.client import end_conversation

        summary = "Talked about work stress and evening plans"
        await end_conversation(mock_db, "conv_1", summary=summary)
        conn = mock_db._test_conn
        call_args = conn.execute.call_args[0]
        assert summary in call_args

    @pytest.mark.asyncio
    async def test_end_conversation_sets_ended_at(self, mock_db):
        """SQL must update the ended_at column."""
        from src.db.client import end_conversation

        await end_conversation(mock_db, "conv_1", summary="test")
        conn = mock_db._test_conn
        sql = conn.execute.call_args[0][0].lower()
        assert "ended_at" in sql or "end" in sql
