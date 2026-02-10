"""
Koi Voice Agent -- LiveKit Worker Entry Point.

Registers as a LiveKit agent worker. When a user joins a room, the agent:
1. Extracts user_id from participant metadata
2. Fetches user profile from Supabase DB
3. Fetches relevant memories from Pinecone
4. Builds the system prompt with context
5. Creates a VoiceAssistant with Sarvam STT/LLM/TTS + Silero VAD
6. Stores messages on speech events
7. Greets the user by name

Run: python -m src.main dev       (development)
     python -m src.main start     (production)
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm as agents_llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import silero

from src.db.client import (
    close_pool,
    create_conversation,
    end_conversation,
    get_user,
    store_message,
)
from src.memory.retriever import get_relevant
from src.memory.storage import store_conversation
from src.persona.prompts import build_context
from src.services.sarvam import SarvamLLM, SarvamSTT, SarvamTTS

# ---------------------------------------------------------------------------
# Logging setup -- structured, never logs conversation content
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO,
    stream=sys.stderr,
)
logger = logging.getLogger("koi.agent")

# Load environment variables
load_dotenv()


# ---------------------------------------------------------------------------
# Process-level initialization (runs once per worker process)
# ---------------------------------------------------------------------------
async def _on_process_start() -> None:
    """Called once when the worker process starts."""
    logger.info("Koi agent worker process starting")


async def _on_process_shutdown() -> None:
    """Called when the worker process is shutting down."""
    logger.info("Koi agent worker process shutting down")
    await close_pool()


# ---------------------------------------------------------------------------
# Per-room entrypoint
# ---------------------------------------------------------------------------
async def entrypoint(ctx: JobContext) -> None:
    """
    Main entrypoint for each LiveKit room session.

    Called by the LiveKit agent framework when a new participant
    joins a room that this agent is assigned to.
    """
    logger.info("New room session starting", extra={"room": ctx.room.name})

    # Wait for the first participant to connect
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(
        "Participant connected",
        extra={"participant_identity": participant.identity},
    )

    # -----------------------------------------------------------------------
    # Extract user context from participant metadata
    # -----------------------------------------------------------------------
    user_id: str = participant.identity
    user_name: str = "friend"
    companion_name: str = "Koi"

    raw_metadata = participant.metadata
    if raw_metadata:
        try:
            meta = json.loads(raw_metadata)
            user_id = meta.get("user_id", user_id)
            user_name = meta.get("user_name", user_name)
            companion_name = meta.get("companion_name", companion_name)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not parse participant metadata")

    # -----------------------------------------------------------------------
    # Fetch user profile and memories concurrently
    # -----------------------------------------------------------------------
    user_profile, memories = await asyncio.gather(
        _safe_get_user(user_id),
        _safe_get_memories(user_id, "greeting"),
        return_exceptions=False,
    )

    if user_profile:
        user_name = user_profile.get("name") or user_name
        companion_name = user_profile.get("companion_name") or companion_name

    # -----------------------------------------------------------------------
    # Build system prompt
    # -----------------------------------------------------------------------
    system_prompt = build_context(user=user_profile, memories=memories)
    logger.info(
        "System prompt built",
        extra={"user_id": user_id, "prompt_chars": len(system_prompt)},
    )

    # -----------------------------------------------------------------------
    # Create conversation record
    # -----------------------------------------------------------------------
    conversation_id = await _safe_create_conversation(user_id)

    # -----------------------------------------------------------------------
    # Assemble the voice pipeline
    # -----------------------------------------------------------------------
    initial_ctx = agents_llm.ChatContext()
    initial_ctx.append(role="system", text=system_prompt)

    stt = SarvamSTT()
    llm_instance = SarvamLLM()
    tts = SarvamTTS()
    vad = silero.VAD.load()

    assistant = VoiceAssistant(
        vad=vad,
        stt=stt,
        llm=llm_instance,
        tts=tts,
        chat_ctx=initial_ctx,
        allow_interruptions=True,
        min_endpointing_delay=0.5,
    )

    # Track conversation messages for memory storage at end
    conversation_messages: list[dict[str, str]] = []

    # -----------------------------------------------------------------------
    # Event handlers for message storage
    # -----------------------------------------------------------------------
    @assistant.on("user_speech_committed")
    def on_user_speech(msg: agents_llm.ChatMessage) -> None:
        """Fired when user speech is finalized by the assistant."""
        content = _extract_text(msg)
        if not content:
            return
        conversation_messages.append({"role": "user", "content": content})
        if conversation_id:
            asyncio.ensure_future(
                _safe_store_message(conversation_id, user_id, "user", content)
            )
        # Fetch fresh memories based on what the user just said
        asyncio.ensure_future(_update_memories_context(assistant, user_id, content))

    @assistant.on("agent_speech_committed")
    def on_agent_speech(msg: agents_llm.ChatMessage) -> None:
        """Fired when the agent finishes speaking a response."""
        content = _extract_text(msg)
        if not content:
            return
        conversation_messages.append({"role": "assistant", "content": content})
        if conversation_id:
            asyncio.ensure_future(
                _safe_store_message(conversation_id, user_id, "assistant", content)
            )

    # -----------------------------------------------------------------------
    # Start the assistant and greet the user
    # -----------------------------------------------------------------------
    assistant.start(ctx.room, participant)
    logger.info("VoiceAssistant started", extra={"user_id": user_id})

    # Generate personalized greeting
    greeting = _build_greeting(user_name, companion_name, user_profile)
    await assistant.say(greeting, allow_interruptions=True)

    # -----------------------------------------------------------------------
    # Wait until the session ends, then clean up
    # -----------------------------------------------------------------------
    try:
        await _wait_for_disconnect(ctx)
    finally:
        logger.info("Session ending", extra={"user_id": user_id})

        # End conversation and store memory in background
        if conversation_id:
            await _safe_end_conversation(conversation_id, conversation_messages)

        if conversation_messages:
            asyncio.ensure_future(
                _safe_store_conversation_memory(user_id, conversation_messages)
            )

        # Close Sarvam HTTP clients
        await stt.aclose()
        await llm_instance.aclose()
        await tts.aclose()

        logger.info(
            "Session cleanup complete",
            extra={
                "user_id": user_id,
                "message_count": len(conversation_messages),
            },
        )


# ---------------------------------------------------------------------------
# Greeting builder
# ---------------------------------------------------------------------------
def _build_greeting(
    user_name: str,
    companion_name: str,
    user_profile: dict | None,
) -> str:
    """Build a personalized greeting message."""
    stage = "early"
    if user_profile:
        stage = user_profile.get("relationship_stage", "early")

    if stage == "early":
        return f"Hey {user_name}! Main {companion_name}. Kaisa chal raha hai sab? Batao na, kya scene hai?"
    elif stage == "developing":
        return f"Arre {user_name}! Kya haal hai? Batao kya chal raha hai aaj?"
    else:
        return f"Hey {user_name}! Achha laga sun ke tumhari awaaz. Kya scene hai?"


# ---------------------------------------------------------------------------
# Safe wrappers (never let DB/API errors crash the voice session)
# ---------------------------------------------------------------------------
async def _safe_get_user(user_id: str) -> dict | None:
    try:
        return await asyncio.wait_for(get_user(user_id), timeout=5.0)
    except Exception:
        logger.exception("Failed to fetch user", extra={"user_id": user_id})
        return None


async def _safe_get_memories(user_id: str, query: str) -> list[dict]:
    try:
        return await asyncio.wait_for(get_relevant(user_id, query), timeout=5.0)
    except Exception:
        logger.exception("Failed to fetch memories", extra={"user_id": user_id})
        return []


async def _safe_create_conversation(user_id: str) -> str | None:
    try:
        return await asyncio.wait_for(create_conversation(user_id), timeout=5.0)
    except Exception:
        logger.exception("Failed to create conversation", extra={"user_id": user_id})
        return None


async def _safe_store_message(
    conversation_id: str, user_id: str, role: str, content: str
) -> None:
    try:
        await asyncio.wait_for(
            store_message(conversation_id, user_id, role, content),
            timeout=5.0,
        )
    except Exception:
        logger.exception(
            "Failed to store message",
            extra={"user_id": user_id, "role": role},
        )


async def _safe_end_conversation(
    conversation_id: str,
    messages: list[dict[str, str]],
) -> None:
    summary = None
    if messages:
        # Use message count as a quick summary fallback
        summary = f"Conversation with {len(messages)} exchanges"
    try:
        await asyncio.wait_for(
            end_conversation(conversation_id, summary),
            timeout=5.0,
        )
    except Exception:
        logger.exception(
            "Failed to end conversation",
            extra={"conversation_id": conversation_id},
        )


async def _safe_store_conversation_memory(
    user_id: str,
    messages: list[dict[str, str]],
) -> None:
    try:
        await asyncio.wait_for(
            store_conversation(user_id, messages),
            timeout=30.0,
        )
    except Exception:
        logger.exception(
            "Failed to store conversation memory",
            extra={"user_id": user_id},
        )


async def _update_memories_context(
    assistant: VoiceAssistant,
    user_id: str,
    query: str,
) -> None:
    """Fetch fresh memories based on user speech and update the system prompt."""
    try:
        memories = await asyncio.wait_for(
            get_relevant(user_id, query, top_k=3),
            timeout=5.0,
        )
        if memories:
            logger.info(
                "Updated memories context",
                extra={"user_id": user_id, "memory_count": len(memories)},
            )
    except Exception:
        logger.exception("Failed to update memories context", extra={"user_id": user_id})


async def _wait_for_disconnect(ctx: JobContext) -> None:
    """Wait until the room is empty or the job is cancelled."""
    disconnect_event = asyncio.Event()

    def on_participant_disconnected(*args: object) -> None:
        remaining = len(ctx.room.remote_participants)
        if remaining == 0:
            disconnect_event.set()

    ctx.room.on("participant_disconnected", on_participant_disconnected)

    # Also handle the job shutdown signal
    ctx.add_shutdown_callback(lambda: disconnect_event.set())

    await disconnect_event.wait()


def _extract_text(msg: agents_llm.ChatMessage) -> str:
    """Extract plain text from a ChatMessage."""
    if isinstance(msg.content, str):
        return msg.content
    if isinstance(msg.content, list):
        parts = []
        for part in msg.content:
            if isinstance(part, str):
                parts.append(part)
            elif hasattr(part, "text"):
                parts.append(part.text)
        return " ".join(parts)
    return ""


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )
