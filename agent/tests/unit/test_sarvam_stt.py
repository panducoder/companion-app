"""Tests for Sarvam STT (Speech-to-Text) wrapper.

Verifies src/services/sarvam.py SarvamSTT class:
  - Uses Sarvam Saarika v2.5 model
  - Language: hi-IN (with Hinglish support)
  - Endpoint: POST /speech-to-text
  - Accepts audio buffer, returns transcript
  - Handles: timeouts (10s), retries (2x), empty audio

Contract (from BUILD_PLAN.md):
  SarvamSTT implements livekit.agents.stt.STT interface
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from tests.fixtures.mock_responses import (
    STT_RESPONSE_HINGLISH,
    STT_RESPONSE_EMPTY,
    STT_RESPONSE_LOW_CONFIDENCE,
    STT_RESPONSE_HINDI,
    STT_RESPONSE_ENGLISH,
)


@pytest.mark.unit
class TestSarvamSTTHappyPath:
    """Test successful transcription scenarios."""

    @pytest.mark.asyncio
    async def test_transcribe_hinglish_audio(self, fake_audio_buffer):
        """Should transcribe Hinglish audio and return transcript text."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.json.return_value = STT_RESPONSE_HINGLISH
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            stt = SarvamSTT(api_key="test_key")
            result = await stt.recognize(fake_audio_buffer)
            assert result.text == "Yaar, aaj bahut boring tha office mein"

    @pytest.mark.asyncio
    async def test_transcribe_returns_language_code(self, fake_audio_buffer):
        """Result should include the detected language code."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.json.return_value = STT_RESPONSE_HINGLISH
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            stt = SarvamSTT(api_key="test_key")
            result = await stt.recognize(fake_audio_buffer)
            assert hasattr(result, "language") or hasattr(result, "language_code")

    @pytest.mark.asyncio
    async def test_transcribe_sends_to_correct_endpoint(self, fake_audio_buffer):
        """Must POST to /speech-to-text endpoint."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = STT_RESPONSE_HINGLISH
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client_instance.post.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            stt = SarvamSTT(api_key="test_key")
            await stt.recognize(fake_audio_buffer)
            call_args = mock_client_instance.post.call_args
            url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
            assert "speech-to-text" in url

    @pytest.mark.asyncio
    async def test_transcribe_includes_api_key_header(self, fake_audio_buffer):
        """Request must include the Sarvam API key in headers."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = STT_RESPONSE_HINGLISH
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_client_instance.post.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            stt = SarvamSTT(api_key="test_key_123")
            await stt.recognize(fake_audio_buffer)
            # API key should be somewhere in the call (headers)
            call_kwargs = mock_client_instance.post.call_args
            headers = call_kwargs.kwargs.get("headers", {})
            assert any("test_key_123" in str(v) for v in headers.values()) or \
                   "test_key_123" in str(call_kwargs)


@pytest.mark.unit
class TestSarvamSTTErrorHandling:
    """Test STT error and edge case handling."""

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio_returns_empty(self, empty_audio_buffer):
        """Empty/silent audio should return empty transcript, not crash."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.json.return_value = STT_RESPONSE_EMPTY
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            stt = SarvamSTT(api_key="test_key")
            result = await stt.recognize(empty_audio_buffer)
            assert result.text == "" or result.text is None

    @pytest.mark.asyncio
    async def test_transcribe_timeout_raises(self, fake_audio_buffer):
        """Should raise or handle timeout after 10 seconds."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.side_effect = httpx.TimeoutException("Request timed out")
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            stt = SarvamSTT(api_key="test_key")
            with pytest.raises((httpx.TimeoutException, TimeoutError, Exception)):
                await stt.recognize(fake_audio_buffer)

    @pytest.mark.asyncio
    async def test_transcribe_retries_on_failure(self, fake_audio_buffer):
        """Should retry up to 2 times on transient failures."""
        from src.services.sarvam import SarvamSTT

        call_count = 0

        async def _flaky_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.HTTPStatusError(
                    "Server Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                )
            response = MagicMock()
            response.json.return_value = STT_RESPONSE_HINGLISH
            response.status_code = 200
            response.raise_for_status = MagicMock()
            return response

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = _flaky_post
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            stt = SarvamSTT(api_key="test_key")
            result = await stt.recognize(fake_audio_buffer)
            assert call_count >= 2  # At least retried once
            assert result.text == "Yaar, aaj bahut boring tha office mein"

    @pytest.mark.asyncio
    async def test_transcribe_low_confidence_still_returns(self, fake_audio_buffer):
        """Low confidence transcription should still return the text (let caller decide)."""
        from src.services.sarvam import SarvamSTT

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_response = MagicMock()
            mock_response.json.return_value = STT_RESPONSE_LOW_CONFIDENCE
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            stt = SarvamSTT(api_key="test_key")
            result = await stt.recognize(fake_audio_buffer)
            assert result.text is not None


@pytest.mark.unit
class TestSarvamSTTConfiguration:
    """Test that STT is configured per spec."""

    def test_stt_uses_saarika_model(self):
        """Should be configured to use Sarvam Saarika v2.5 model."""
        from src.services.sarvam import SarvamSTT

        stt = SarvamSTT(api_key="test_key")
        assert hasattr(stt, "model") or hasattr(stt, "_model")
        model = getattr(stt, "model", getattr(stt, "_model", ""))
        assert "saarika" in model.lower() or "saarika" in str(stt.__dict__).lower()

    def test_stt_default_language_is_hindi(self):
        """Default language should be hi-IN."""
        from src.services.sarvam import SarvamSTT

        stt = SarvamSTT(api_key="test_key")
        lang = getattr(stt, "language", getattr(stt, "_language", ""))
        assert "hi" in lang.lower()
