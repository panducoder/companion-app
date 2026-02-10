"""Tests for Supabase/PostgreSQL database client."""

import pytest


class TestDatabaseClient:
    """Test database operations."""

    @pytest.mark.asyncio
    async def test_get_user_returns_profile(self, mock_db):
        """Should return user profile by ID."""
        # TODO: Implement when db/client.py is built
        # from src.db.client import get_user
        # user = await get_user(mock_db, "user_1")
        # assert user["name"] == "Rahul"
        pass

    @pytest.mark.asyncio
    async def test_get_user_returns_none_for_missing(self, mock_db):
        """Should return None for non-existent user."""
        # TODO: Implement when db/client.py is built
        pass

    @pytest.mark.asyncio
    async def test_store_message(self, mock_db):
        """Should store a message in the messages table."""
        # TODO: Implement when db/client.py is built
        pass

    @pytest.mark.asyncio
    async def test_create_conversation(self, mock_db):
        """Should create a new conversation record."""
        # TODO: Implement when db/client.py is built
        pass

    @pytest.mark.asyncio
    async def test_end_conversation_with_summary(self, mock_db):
        """Should update conversation with end time and summary."""
        # TODO: Implement when db/client.py is built
        pass
