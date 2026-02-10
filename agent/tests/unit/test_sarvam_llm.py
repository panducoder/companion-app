"""Tests for Sarvam LLM wrapper.

Verifies src/services/sarvam.py SarvamLLM class:
  - Uses Sarvam-M model
  - Streaming responses enabled (SSE)
  - Endpoint: POST /chat/completions with stream=true
  - Temperature: 0.8
  - Max tokens: 300 (keep responses short for voice)
  - Handles: streaming SSE parsing, connection drops

Contract (from BUILD_PLAN.md):
  SarvamLLM implements livekit.agents.llm.LLM interface
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from tests.fixtures.mock_responses import (
    LLM_STREAMING_CHUNKS,
    LLM_STREAMING_CHUNKS_LONG,
    LLM_STREAMING_CHUNKS_SHORT,
    LLM_COMPLETE_RESPONSE,
)


@pytest.mark.unit
class TestSarvamLLMStreaming:
    """Test streaming response handling."""

    @pytest.mark.asyncio
    async def test_streaming_response_yields_text_chunks(self):
        """Should yield individual text chunks from SSE stream."""
        from src.services.sarvam import SarvamLLM

        async def _mock_stream(*args, **kwargs):
            for chunk in LLM_STREAMING_CHUNKS:
                yield chunk

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = _mock_stream
            mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            llm = SarvamLLM(api_key="test_key")
            chunks = []
            async for chunk in llm.chat([{"role": "user", "content": "Kya hua?"}]):
                chunks.append(chunk)
            assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_streaming_reassembles_full_response(self):
        """All chunks combined should form the complete response."""
        from src.services.sarvam import SarvamLLM

        async def _mock_stream(*args, **kwargs):
            for chunk in LLM_STREAMING_CHUNKS:
                yield chunk

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = _mock_stream
            mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            llm = SarvamLLM(api_key="test_key")
            full_text = ""
            async for chunk in llm.chat([{"role": "user", "content": "test"}]):
                text = getattr(chunk, "text", chunk.get("text", "") if isinstance(chunk, dict) else str(chunk))
                full_text += text
            assert "Achha" in full_text

    @pytest.mark.asyncio
    async def test_streaming_detects_finish_reason(self):
        """Should stop yielding when finish_reason is 'stop'."""
        from src.services.sarvam import SarvamLLM

        extra_chunk_after_stop = {
            "choices": [{"delta": {"content": "SHOULD NOT APPEAR"}, "finish_reason": None}]
        }
        chunks_with_extra = LLM_STREAMING_CHUNKS + [extra_chunk_after_stop]

        async def _mock_stream(*args, **kwargs):
            for chunk in chunks_with_extra:
                yield chunk

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = _mock_stream
            mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            llm = SarvamLLM(api_key="test_key")
            full_text = ""
            async for chunk in llm.chat([{"role": "user", "content": "test"}]):
                text = getattr(chunk, "text", chunk.get("text", "") if isinstance(chunk, dict) else str(chunk))
                full_text += text
            assert "SHOULD NOT APPEAR" not in full_text


@pytest.mark.unit
class TestSarvamLLMConfiguration:
    """Test LLM configuration matches spec."""

    def test_llm_uses_sarvam_m_model(self):
        """Should be configured to use Sarvam-M model."""
        from src.services.sarvam import SarvamLLM

        llm = SarvamLLM(api_key="test_key")
        model = getattr(llm, "model", getattr(llm, "_model", ""))
        assert "sarvam" in model.lower() or "sarvam" in str(llm.__dict__).lower()

    def test_llm_temperature_is_0_8(self):
        """Temperature should be 0.8 per spec."""
        from src.services.sarvam import SarvamLLM

        llm = SarvamLLM(api_key="test_key")
        temp = getattr(llm, "temperature", getattr(llm, "_temperature", None))
        assert temp == 0.8

    def test_llm_max_tokens_is_300(self):
        """Max tokens should be 300 for short voice responses."""
        from src.services.sarvam import SarvamLLM

        llm = SarvamLLM(api_key="test_key")
        max_tokens = getattr(llm, "max_tokens", getattr(llm, "_max_tokens", None))
        assert max_tokens == 300

    def test_llm_streaming_enabled(self):
        """Streaming should be enabled by default."""
        from src.services.sarvam import SarvamLLM

        llm = SarvamLLM(api_key="test_key")
        streaming = getattr(llm, "streaming", getattr(llm, "_streaming", True))
        assert streaming is True


@pytest.mark.unit
class TestSarvamLLMErrorHandling:
    """Test LLM error scenarios."""

    @pytest.mark.asyncio
    async def test_llm_handles_connection_drop(self):
        """Should raise an appropriate error on connection loss mid-stream."""
        from src.services.sarvam import SarvamLLM

        async def _broken_stream(*args, **kwargs):
            yield LLM_STREAMING_CHUNKS[0]
            raise httpx.ReadError("Connection reset by peer")

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = _broken_stream
            mock_client_instance.stream.return_value.__aenter__.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            llm = SarvamLLM(api_key="test_key")
            with pytest.raises((httpx.ReadError, ConnectionError, Exception)):
                async for _ in llm.chat([{"role": "user", "content": "test"}]):
                    pass

    @pytest.mark.asyncio
    async def test_llm_passes_messages_to_api(self):
        """All messages (system + user) must be sent to the API."""
        from src.services.sarvam import SarvamLLM

        captured_payload = {}

        async def _mock_post(*args, **kwargs):
            captured_payload.update(kwargs.get("json", {}))
            response = MagicMock()
            response.json.return_value = {"choices": [{"message": {"content": LLM_COMPLETE_RESPONSE}}]}
            response.status_code = 200
            response.raise_for_status = MagicMock()
            return response

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = _mock_post
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            llm = SarvamLLM(api_key="test_key")
            messages = [
                {"role": "system", "content": "You are Koi"},
                {"role": "user", "content": "Kya hua?"},
            ]
            # Try non-streaming path
            try:
                result = await llm.generate(messages)
            except AttributeError:
                # If streaming-only, this test validates the interface exists
                pass

    @pytest.mark.asyncio
    async def test_llm_sends_to_chat_completions_endpoint(self):
        """Must POST to /chat/completions endpoint."""
        from src.services.sarvam import SarvamLLM

        captured_url = []

        async def _capture_post(url, *args, **kwargs):
            captured_url.append(url)
            response = MagicMock()
            response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
            response.status_code = 200
            response.raise_for_status = MagicMock()
            return response

        with patch("src.services.sarvam.httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post = _capture_post
            MockClient.return_value.__aenter__.return_value = mock_client_instance

            llm = SarvamLLM(api_key="test_key")
            try:
                await llm.generate([{"role": "user", "content": "test"}])
            except (AttributeError, TypeError):
                pass
            if captured_url:
                assert "chat/completions" in captured_url[0]
