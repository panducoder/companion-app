"""
Langfuse observability for the Koi voice agent.

Provides a singleton Langfuse client and helpers for creating
session-level traces with child spans for STT, LLM, and TTS calls.

All tracing is opt-in via LANGFUSE_ENABLED=true.
Conversation content is redacted by default; set TRACE_CONTENT=true to include it.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("koi.agent.observability")

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_langfuse_client: Any = None  # Langfuse | None
_enabled: bool = False
_trace_content: bool = False


def _is_truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("true", "1", "yes")


def init_langfuse() -> None:
    """Initialize the Langfuse client from environment variables.

    Required env vars (when enabled):
      LANGFUSE_ENABLED   - "true" to activate tracing
      LANGFUSE_PUBLIC_KEY
      LANGFUSE_SECRET_KEY
      LANGFUSE_HOST      - e.g. "https://cloud.langfuse.com"

    Optional:
      TRACE_CONTENT      - "true" to include conversation text in traces (default: false)
    """
    global _langfuse_client, _enabled, _trace_content

    _enabled = _is_truthy(os.environ.get("LANGFUSE_ENABLED"))
    _trace_content = _is_truthy(os.environ.get("TRACE_CONTENT"))

    if not _enabled:
        logger.info("Langfuse tracing is disabled (LANGFUSE_ENABLED != true)")
        return

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            enabled=True,
        )
        logger.info(
            "Langfuse tracing initialized",
            extra={"host": os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")},
        )
    except Exception:
        logger.exception("Failed to initialize Langfuse -- tracing disabled")
        _enabled = False
        _langfuse_client = None


def shutdown_langfuse() -> None:
    """Flush pending events and shut down the Langfuse client."""
    global _langfuse_client, _enabled
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
            _langfuse_client.shutdown()
            logger.info("Langfuse client shut down")
        except Exception:
            logger.exception("Error shutting down Langfuse")
        finally:
            _langfuse_client = None
            _enabled = False


def is_enabled() -> bool:
    return _enabled


def trace_content_enabled() -> bool:
    return _trace_content


# ---------------------------------------------------------------------------
# Trace & span helpers
# ---------------------------------------------------------------------------

def create_session_trace(
    *,
    session_id: str,
    user_id: str,
    metadata: dict[str, Any] | None = None,
) -> Any:
    """Create a top-level trace for a voice session. Returns the trace object or None."""
    if not _enabled or _langfuse_client is None:
        return None
    try:
        trace = _langfuse_client.trace(
            name="voice-session",
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )
        return trace
    except Exception:
        logger.exception("Failed to create Langfuse session trace")
        return None


def create_stt_span(
    trace: Any,
    *,
    audio_size_bytes: int,
    language: str,
    model: str,
) -> Any:
    """Create a child span on the trace for an STT call. Returns the span or None."""
    if trace is None:
        return None
    try:
        span = trace.span(
            name="stt",
            input={"audio_size_bytes": audio_size_bytes, "language": language},
            metadata={"model": model},
            start_time=datetime.now(timezone.utc),
        )
        return span
    except Exception:
        logger.exception("Failed to create STT span")
        return None


def end_stt_span(
    span: Any,
    *,
    transcript: str,
    language: str,
) -> None:
    """End an STT span with the result."""
    if span is None:
        return
    try:
        output: dict[str, Any] = {"language": language, "transcript_chars": len(transcript)}
        if _trace_content:
            output["transcript"] = transcript
        span.end(
            output=output,
            end_time=datetime.now(timezone.utc),
        )
    except Exception:
        logger.exception("Failed to end STT span")


def create_llm_generation(
    trace: Any,
    *,
    messages: list[dict[str, str]],
    model: str,
    model_parameters: dict[str, Any],
) -> Any:
    """Create a generation span for an LLM chat completion. Returns the generation or None."""
    if trace is None:
        return None
    try:
        input_data: Any
        if _trace_content:
            input_data = messages
        else:
            input_data = {
                "message_count": len(messages),
                "roles": [m.get("role", "unknown") for m in messages],
            }
        generation = trace.generation(
            name="llm-chat",
            model=model,
            model_parameters=model_parameters,
            input=input_data,
            start_time=datetime.now(timezone.utc),
        )
        return generation
    except Exception:
        logger.exception("Failed to create LLM generation")
        return None


def end_llm_generation(
    generation: Any,
    *,
    output_text: str,
    usage: dict[str, int] | None = None,
) -> None:
    """End an LLM generation with the output."""
    if generation is None:
        return
    try:
        output_data: Any
        if _trace_content:
            output_data = output_text
        else:
            output_data = {"output_chars": len(output_text)}
        generation.end(
            output=output_data,
            usage=usage,
            end_time=datetime.now(timezone.utc),
        )
    except Exception:
        logger.exception("Failed to end LLM generation")


def create_tts_span(
    trace: Any,
    *,
    text: str,
    model: str,
    voice: str,
    language: str,
) -> Any:
    """Create a child span for a TTS call. Returns the span or None."""
    if trace is None:
        return None
    try:
        input_data: dict[str, Any] = {"text_chars": len(text), "voice": voice, "language": language}
        if _trace_content:
            input_data["text"] = text
        span = trace.span(
            name="tts",
            input=input_data,
            metadata={"model": model},
            start_time=datetime.now(timezone.utc),
        )
        return span
    except Exception:
        logger.exception("Failed to create TTS span")
        return None


def end_tts_span(
    span: Any,
    *,
    audio_size_bytes: int,
) -> None:
    """End a TTS span with the result."""
    if span is None:
        return
    try:
        span.end(
            output={"audio_size_bytes": audio_size_bytes},
            end_time=datetime.now(timezone.utc),
        )
    except Exception:
        logger.exception("Failed to end TTS span")


def flush() -> None:
    """Flush pending Langfuse events (call at end of session)."""
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
        except Exception:
            logger.exception("Failed to flush Langfuse events")
