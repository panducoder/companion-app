"""
Memory storage: summarize conversations and upsert to Pinecone.

After a conversation ends, this module:
1. Summarizes the conversation via Sarvam LLM
2. Embeds the summary
3. Upserts the vector + metadata to Pinecone

Designed to run as a background task so it doesn't block the voice pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from pinecone import Pinecone
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.memory.retriever import _embed_text, _get_index_name, _get_pinecone

logger = logging.getLogger("koi.agent.memory.storage")

SARVAM_BASE_URL = "https://api.sarvam.ai"
_LLM_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

_SUMMARIZE_PROMPT = """\
Summarize the following conversation between a user and their AI companion Koi. \
Produce a concise 2-3 sentence summary covering: what was discussed, the user's \
emotional state, and any important facts mentioned. Also identify the primary topic \
and the user's emotional tone in one word each.

Respond in this exact JSON format:
{"summary": "...", "topic": "...", "emotional_tone": "..."}

Conversation:
"""


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, asyncio.TimeoutError)),
    reraise=True,
)
async def _summarize_conversation(messages: list[dict[str, str]]) -> dict[str, str]:
    """
    Use Sarvam-M to summarize a conversation into a short summary.

    Parameters
    ----------
    messages : list[dict]
        List of {"role": "user"|"assistant", "content": "..."} dicts.

    Returns
    -------
    dict with keys: summary, topic, emotional_tone
    """
    api_key = os.environ.get("SARVAM_API_KEY", "")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY not set")

    # Build a text transcript (without revealing raw content in logs)
    transcript_lines: list[str] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        transcript_lines.append(f"{role}: {content}")
    transcript = "\n".join(transcript_lines)

    payload = {
        "model": "sarvam-m",
        "messages": [
            {
                "role": "system",
                "content": _SUMMARIZE_PROMPT + transcript,
            }
        ],
        "temperature": 0.3,
        "max_tokens": 200,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=_LLM_TIMEOUT) as client:
        resp = await client.post(
            f"{SARVAM_BASE_URL}/chat/completions",
            json=payload,
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    # Parse JSON from the LLM response
    import json

    try:
        result = json.loads(raw_content)
        return {
            "summary": result.get("summary", raw_content[:300]),
            "topic": result.get("topic", "general"),
            "emotional_tone": result.get("emotional_tone", "neutral"),
        }
    except json.JSONDecodeError:
        # LLM didn't return valid JSON -- use the raw text as summary
        return {
            "summary": raw_content[:300],
            "topic": "general",
            "emotional_tone": "neutral",
        }


async def store_conversation(
    user_id: str,
    messages: list[dict[str, str]],
) -> None:
    """
    Summarize a conversation and store it in Pinecone.

    This should be called when a conversation ends. It runs the
    summarization LLM call, embeds the summary, and upserts to Pinecone.

    Parameters
    ----------
    user_id : str
        The user's UUID.
    messages : list[dict]
        The full list of conversation messages with role and content keys.
    """
    if not messages or len(messages) < 2:
        logger.info("Conversation too short to store", extra={"user_id": user_id})
        return

    try:
        summary_data = await _summarize_conversation(messages)
    except Exception:
        logger.exception(
            "Failed to summarize conversation",
            extra={"user_id": user_id},
        )
        return

    summary_text = summary_data["summary"]

    try:
        embedding = await _embed_text(summary_text)
    except Exception:
        logger.exception(
            "Failed to embed conversation summary",
            extra={"user_id": user_id},
        )
        return

    now = datetime.now(timezone.utc)
    vector_id = f"{user_id}_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    metadata = {
        "user_id": user_id,
        "summary": summary_text,
        "topic": summary_data["topic"],
        "emotional_tone": summary_data["emotional_tone"],
        "date": now.isoformat(),
        "message_count": len(messages),
    }

    try:
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
        logger.info(
            "Conversation memory stored",
            extra={"user_id": user_id, "vector_id": vector_id},
        )
    except Exception:
        logger.exception(
            "Failed to upsert to Pinecone",
            extra={"user_id": user_id},
        )
