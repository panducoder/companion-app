"""
Supabase PostgreSQL database client using asyncpg.

Handles user profile retrieval, conversation lifecycle,
and message storage. All operations use parameterized queries.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import asyncpg

logger = logging.getLogger("koi.agent.db")

_pool: asyncpg.Pool | None = None

_CONNECT_TIMEOUT_S = 10
_QUERY_TIMEOUT_S = 5


async def get_pool() -> asyncpg.Pool:
    """Return the shared connection pool, creating it on first call."""
    global _pool
    if _pool is None or _pool._closed:  # noqa: SLF001
        dsn = os.environ["SUPABASE_DB_URL"]
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=5,
            timeout=_CONNECT_TIMEOUT_S,
            command_timeout=_QUERY_TIMEOUT_S,
        )
        logger.info("Database connection pool created")
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool is not None and not _pool._closed:  # noqa: SLF001
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


async def get_user(user_id: str) -> dict[str, Any] | None:
    """
    Fetch a user profile by ID.

    Returns None if the user does not exist.
    """
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, name, companion_name, phone, relationship_stage,
               created_at, last_active_at, subscription_status,
               preferences, profile_data
        FROM public.profiles
        WHERE id = $1
        """,
        UUID(user_id),
    )
    if row is None:
        logger.warning("User not found", extra={"user_id": user_id})
        return None

    result = dict(row)
    # Update last_active_at on every fetch (fire-and-forget is fine here)
    try:
        await pool.execute(
            "UPDATE public.profiles SET last_active_at = $1 WHERE id = $2",
            datetime.now(timezone.utc),
            UUID(user_id),
        )
    except asyncpg.PostgresError:
        logger.exception("Failed to update last_active_at", extra={"user_id": user_id})

    logger.info("User fetched", extra={"user_id": user_id})
    return result


async def create_conversation(user_id: str) -> str:
    """
    Create a new conversation record.

    Returns the conversation UUID as a string.
    """
    pool = await get_pool()
    conversation_id = uuid4()
    await pool.execute(
        """
        INSERT INTO public.conversations (id, user_id, started_at)
        VALUES ($1, $2, $3)
        """,
        conversation_id,
        UUID(user_id),
        datetime.now(timezone.utc),
    )
    cid = str(conversation_id)
    logger.info("Conversation created", extra={"user_id": user_id, "conversation_id": cid})
    return cid


async def end_conversation(conversation_id: str, summary: str | None = None) -> None:
    """
    Mark a conversation as ended with optional summary.
    Calculates duration from started_at to now.
    """
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    await pool.execute(
        """
        UPDATE public.conversations
        SET ended_at = $1,
            duration_seconds = EXTRACT(EPOCH FROM ($1 - started_at))::INTEGER,
            summary = $2
        WHERE id = $3
        """,
        now,
        summary,
        UUID(conversation_id),
    )
    logger.info("Conversation ended", extra={"conversation_id": conversation_id})


async def store_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
) -> str:
    """
    Store a single message in the messages table.

    Parameters
    ----------
    conversation_id : str
        UUID of the conversation.
    user_id : str
        UUID of the user.
    role : str
        Either 'user' or 'assistant'.
    content : str
        The message text.

    Returns
    -------
    str
        The UUID of the inserted message.
    """
    pool = await get_pool()
    message_id = uuid4()
    await pool.execute(
        """
        INSERT INTO public.messages (id, conversation_id, user_id, role, content, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        message_id,
        UUID(conversation_id),
        UUID(user_id),
        role,
        content,
        datetime.now(timezone.utc),
    )
    # Do NOT log content -- privacy requirement
    logger.info(
        "Message stored",
        extra={
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
        },
    )
    return str(message_id)
