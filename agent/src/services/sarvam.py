"""
Sarvam AI API wrappers for LiveKit Agents framework.

Implements three classes that conform to the LiveKit agent plugin interfaces:
  - SarvamSTT  (speech-to-text using Saarika v2.5)
  - SarvamLLM  (chat completions using Sarvam-M, streaming)
  - SarvamTTS  (text-to-speech using Bulbul v3)

All classes use httpx for async HTTP, tenacity for retries,
and structured logging (never logging conversation content).
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
from typing import Any

import httpx
from livekit.agents import llm as agents_llm
from livekit.agents import stt as agents_stt
from livekit.agents import tts as agents_tts
from livekit.agents import utils as agents_utils
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("koi.agent.sarvam")

SARVAM_BASE_URL = "https://api.sarvam.ai"
_HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)
_STT_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)


def _get_api_key() -> str:
    key = os.environ.get("SARVAM_API_KEY", "")
    if not key:
        raise RuntimeError("SARVAM_API_KEY environment variable is not set")
    return key


def _auth_headers() -> dict[str, str]:
    return {
        "api-subscription-key": _get_api_key(),
        "Content-Type": "application/json",
    }


# ============================================================================
# SarvamSTT -- Speech-to-Text (Saarika v2.5)
# ============================================================================


class SarvamSTT(agents_stt.STT):
    """
    Sarvam Saarika v2.5 speech-to-text.

    Accepts raw audio frames, sends to POST /speech-to-text,
    returns a SpeechEvent with the transcript.
    """

    def __init__(
        self,
        *,
        language: str = "hi-IN",
        model: str = "saarika:v2.5",
    ) -> None:
        super().__init__(
            capabilities=agents_stt.STTCapabilities(streaming=False, interim_results=False),
        )
        self._language = language
        self._model = model
        self._client = httpx.AsyncClient(timeout=_STT_TIMEOUT)

    async def _recognize_impl(
        self,
        buffer: agents_utils.AudioBuffer,
        *,
        language: str | None = None,
    ) -> agents_stt.SpeechEvent:
        """Transcribe an audio buffer via Sarvam STT API."""
        lang = language or self._language

        # Convert AudioBuffer to WAV bytes
        wav_bytes = _audio_buffer_to_wav(buffer)

        if len(wav_bytes) < 100:
            logger.warning("Audio buffer too small, returning empty transcript")
            return agents_stt.SpeechEvent(
                type=agents_stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[agents_stt.SpeechData(text="", language=lang)],
            )

        transcript = await self._call_stt_api(wav_bytes, lang)

        return agents_stt.SpeechEvent(
            type=agents_stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[agents_stt.SpeechData(text=transcript, language=lang)],
        )

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def _call_stt_api(self, wav_bytes: bytes, language: str) -> str:
        """POST audio to Sarvam /speech-to-text with retry."""
        audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
        payload = {
            "model": self._model,
            "language_code": language,
            "audio": audio_b64,
            "with_timestamps": False,
        }
        resp = await self._client.post(
            f"{SARVAM_BASE_URL}/speech-to-text",
            json=payload,
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        transcript = data.get("transcript", "")
        logger.info(
            "STT transcription complete",
            extra={"language": language, "response_chars": len(transcript)},
        )
        return transcript

    async def aclose(self) -> None:
        await self._client.aclose()


# ============================================================================
# SarvamLLM -- Chat Completions (Sarvam-M, streaming)
# ============================================================================


class SarvamLLM(agents_llm.LLM):
    """
    Sarvam-M chat completions with streaming SSE.

    Implements the LiveKit agents LLM interface so VoiceAssistant
    can stream responses token-by-token for low-latency TTS.
    """

    def __init__(
        self,
        *,
        model: str = "sarvam-m",
        temperature: float = 0.8,
        max_tokens: int = 300,
    ) -> None:
        super().__init__()
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = httpx.AsyncClient(timeout=_HTTP_TIMEOUT)

    def chat(
        self,
        *,
        chat_ctx: agents_llm.ChatContext,
        fnc_ctx: agents_llm.FunctionContext | None = None,
        temperature: float | None = None,
        n: int | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> _SarvamLLMStream:
        """Start a streaming chat completion request."""
        messages = _chat_context_to_messages(chat_ctx)
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._temperature,
            "max_tokens": self._max_tokens,
            "stream": True,
        }

        # We need to start the HTTP request inside the stream's _run,
        # but LiveKit expects us to return the stream synchronously.
        # So we create the stream and let _run do the actual HTTP call.
        stream = _SarvamLLMStreamLazy(
            client=self._client,
            payload=payload,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx or agents_llm.FunctionContext(),
        )
        return stream

    async def aclose(self) -> None:
        await self._client.aclose()


class _SarvamLLMStreamLazy(agents_llm.LLMStream):
    """
    LLM stream that lazily opens the HTTP connection when _run is called.

    This is needed because LiveKit's interface requires chat() to return
    the stream object synchronously, but the HTTP request is async.
    """

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
        chat_ctx: agents_llm.ChatContext,
        fnc_ctx: agents_llm.FunctionContext,
    ) -> None:
        super().__init__(chat_ctx=chat_ctx, fnc_ctx=fnc_ctx)
        self._client = client
        self._payload = payload
        self._collected_text = ""
        self._request_id = ""

    async def _run(self) -> None:
        """Open the SSE stream and parse chunks."""
        request_url = f"{SARVAM_BASE_URL}/chat/completions"
        response: httpx.Response | None = None
        try:
            response = await self._client.send(
                self._client.build_request(
                    "POST",
                    request_url,
                    json=self._payload,
                    headers=_auth_headers(),
                ),
                stream=True,
            )
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                self._request_id = chunk.get("id", self._request_id)

                choices = chunk.get("choices", [])
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    self._collected_text += content
                    self._event_ch.send_nowait(
                        agents_llm.ChatChunk(
                            request_id=self._request_id,
                            choices=[
                                agents_llm.Choice(
                                    delta=agents_llm.ChoiceDelta(
                                        role="assistant",
                                        content=content,
                                    ),
                                    index=0,
                                )
                            ],
                        )
                    )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Sarvam LLM API error",
                extra={"status": exc.response.status_code},
            )
            raise
        except httpx.ConnectError:
            logger.error("Sarvam LLM connection failed")
            raise
        finally:
            if response is not None:
                await response.aclose()
            logger.info(
                "LLM stream finished",
                extra={
                    "request_id": self._request_id,
                    "output_chars": len(self._collected_text),
                },
            )


# ============================================================================
# SarvamTTS -- Text-to-Speech (Bulbul v3)
# ============================================================================


class SarvamTTS(agents_tts.TTS):
    """
    Sarvam Bulbul v3 text-to-speech.

    Sends text to POST /text-to-speech, receives base64 audio,
    decodes to raw PCM and yields as AudioFrame(s).
    """

    def __init__(
        self,
        *,
        voice: str = "meera",
        language: str = "hi-IN",
        model: str = "bulbul:v3",
        pace: float = 1.1,
        sample_rate: int = 22050,
    ) -> None:
        super().__init__(
            capabilities=agents_tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )
        self._voice = voice
        self._language = language
        self._model = model
        self._pace = pace
        self._sample_rate = sample_rate
        self._client = httpx.AsyncClient(timeout=_HTTP_TIMEOUT)

    def synthesize(self, text: str) -> "SarvamTTSStream":
        """Return a ChunkedStream that synthesizes the given text."""
        return SarvamTTSStream(
            tts=self,
            text=text,
            client=self._client,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class SarvamTTSStream(agents_tts.ChunkedStream):
    """Chunked stream for Sarvam TTS synthesis."""

    def __init__(
        self,
        *,
        tts: SarvamTTS,
        text: str,
        client: httpx.AsyncClient,
    ) -> None:
        super().__init__(tts=tts, input_text=text)
        self._tts_ref = tts
        self._text = text
        self._client = client

    async def _run(self) -> None:
        """Synthesize text and emit audio frames."""
        if not self._text or not self._text.strip():
            logger.warning("Empty text passed to TTS, skipping synthesis")
            return

        # Chunk long text into sentences for better audio quality
        chunks = _split_into_sentences(self._text)

        for chunk_text in chunks:
            if not chunk_text.strip():
                continue

            try:
                audio_bytes = await self._call_tts_api(chunk_text)
                if audio_bytes:
                    frame = agents_tts.SynthesizedAudio(
                        request_id="",
                        frame=agents_utils.AudioFrame(
                            data=audio_bytes,
                            sample_rate=self._tts_ref._sample_rate,
                            num_channels=1,
                            samples_per_channel=len(audio_bytes) // 2,  # 16-bit PCM
                        ),
                    )
                    self._event_ch.send_nowait(frame)
            except (httpx.HTTPStatusError, httpx.ConnectError, asyncio.TimeoutError):
                logger.exception("TTS synthesis failed for a text chunk")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def _call_tts_api(self, text: str) -> bytes:
        """POST text to Sarvam /text-to-speech with retry."""
        payload = {
            "model": self._tts_ref._model,
            "target_language_code": self._tts_ref._language,
            "speaker": self._tts_ref._voice,
            "pitch": 0,
            "pace": self._tts_ref._pace,
            "loudness": 1.0,
            "speech_sample_rate": self._tts_ref._sample_rate,
            "enable_preprocessing": True,
            "inputs": [text],
        }
        resp = await self._client.post(
            f"{SARVAM_BASE_URL}/text-to-speech",
            json=payload,
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

        audios = data.get("audios")
        if not audios or not audios[0]:
            logger.warning("TTS returned empty audio")
            return b""

        audio_b64 = audios[0]
        raw_bytes = base64.b64decode(audio_b64)

        logger.info(
            "TTS synthesis complete",
            extra={"text_chars": len(text), "audio_bytes": len(raw_bytes)},
        )
        return raw_bytes


# ============================================================================
# Helper functions
# ============================================================================


def _audio_buffer_to_wav(buffer: agents_utils.AudioBuffer) -> bytes:
    """
    Convert a LiveKit AudioBuffer to WAV bytes suitable for the Sarvam API.

    AudioBuffer exposes raw PCM frames. We wrap them in a minimal WAV header.
    """
    import wave

    # Collect all frames into a single PCM byte stream
    pcm_data = bytearray()
    sample_rate = 16000  # LiveKit default
    num_channels = 1
    sample_width = 2  # 16-bit

    for frame in buffer:
        pcm_data.extend(frame.data)
        sample_rate = frame.sample_rate
        num_channels = frame.num_channels

    # Write WAV to in-memory buffer
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(pcm_data))

    return wav_buffer.getvalue()


def _chat_context_to_messages(ctx: agents_llm.ChatContext) -> list[dict[str, str]]:
    """Convert LiveKit ChatContext to a list of message dicts for the API."""
    messages: list[dict[str, str]] = []
    for msg in ctx.messages:
        role = msg.role
        # LiveKit uses ChatRole enum
        if hasattr(role, "value"):
            role = role.value
        content = ""
        if isinstance(msg.content, str):
            content = msg.content
        elif isinstance(msg.content, list):
            # Multi-part content -- concatenate text parts
            parts = []
            for part in msg.content:
                if isinstance(part, str):
                    parts.append(part)
                elif hasattr(part, "text"):
                    parts.append(part.text)
            content = " ".join(parts)
        messages.append({"role": str(role), "content": content})
    return messages


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentence-level chunks for TTS.

    Sarvam TTS handles shorter chunks better, and this enables
    streaming the first sentence while later ones are synthesized.
    """
    import re

    # Split on sentence-ending punctuation followed by whitespace
    raw_parts = re.split(r"(?<=[.!?।])\s+", text.strip())
    # Merge very short fragments with the previous chunk
    chunks: list[str] = []
    for part in raw_parts:
        if chunks and len(chunks[-1]) < 20:
            chunks[-1] = chunks[-1] + " " + part
        else:
            chunks.append(part)
    return chunks
