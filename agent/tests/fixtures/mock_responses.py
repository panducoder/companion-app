"""Canned API responses for Sarvam AI services.

These represent the contract between our agent and Sarvam's APIs.
Tests use these to verify our code correctly parses and handles
each response shape, including error cases.
"""

# =============================================================================
# STT (Saarika v2.5) - POST /speech-to-text
# =============================================================================

STT_RESPONSE_HINGLISH = {
    "transcript": "Yaar, aaj bahut boring tha office mein",
    "language_code": "hi-en",
    "confidence": 0.95,
}

STT_RESPONSE_HINDI = {
    "transcript": "aaj bahut thakan ho gayi",
    "language_code": "hi-IN",
    "confidence": 0.92,
}

STT_RESPONSE_ENGLISH = {
    "transcript": "I had a really long day at work",
    "language_code": "en-IN",
    "confidence": 0.97,
}

STT_RESPONSE_EMPTY = {
    "transcript": "",
    "language_code": "hi-IN",
    "confidence": 0.1,
}

STT_RESPONSE_LOW_CONFIDENCE = {
    "transcript": "kuch",
    "language_code": "hi-IN",
    "confidence": 0.3,
}

STT_ERROR_TIMEOUT = {
    "error": "Request timeout",
    "status_code": 504,
}

STT_ERROR_INVALID_AUDIO = {
    "error": "Invalid audio format",
    "status_code": 400,
}


# =============================================================================
# LLM (Sarvam-M) - POST /chat/completions (stream=true)
# =============================================================================

LLM_STREAMING_CHUNKS = [
    {"choices": [{"delta": {"content": "Achha, "}, "finish_reason": None}]},
    {"choices": [{"delta": {"content": "kya hua? "}, "finish_reason": None}]},
    {"choices": [{"delta": {"content": "Bata na "}, "finish_reason": None}]},
    {"choices": [{"delta": {"content": "detail mein."}, "finish_reason": "stop"}]},
]

LLM_COMPLETE_RESPONSE = "Achha, kya hua? Bata na detail mein."

LLM_STREAMING_CHUNKS_LONG = [
    {"choices": [{"delta": {"content": chunk}, "finish_reason": None}]}
    for chunk in [
        "Hmm, ",
        "main samajh ",
        "sakta hoon. ",
        "Office mein ",
        "same routine ",
        "hota hai toh ",
        "boring lagta hai. ",
        "Kya kuch alag ",
        "karne ka mann hai ",
        "aaj evening ko?",
    ]
] + [{"choices": [{"delta": {"content": ""}, "finish_reason": "stop"}]}]

LLM_STREAMING_CHUNKS_SHORT = [
    {"choices": [{"delta": {"content": "Hmm, achha."}, "finish_reason": "stop"}]},
]

LLM_ERROR_RATE_LIMIT = {
    "error": {"message": "Rate limit exceeded", "type": "rate_limit_error"},
    "status_code": 429,
}

LLM_ERROR_CONTEXT_LENGTH = {
    "error": {"message": "Context length exceeded", "type": "invalid_request_error"},
    "status_code": 400,
}


# =============================================================================
# TTS (Bulbul v3) - POST /text-to-speech
# =============================================================================

# Simulated base64-encoded audio (small PCM frames for testing)
import base64

_fake_pcm_bytes = b"\x00\x01" * 8000  # ~0.5s of fake 16kHz mono PCM
TTS_RESPONSE_AUDIO_B64 = base64.b64encode(_fake_pcm_bytes).decode("utf-8")

TTS_RESPONSE_SUCCESS = {
    "audios": [TTS_RESPONSE_AUDIO_B64],
    "request_id": "tts-req-001",
}

TTS_RESPONSE_MULTI_CHUNK = {
    "audios": [
        base64.b64encode(b"\x00\x01" * 4000).decode("utf-8"),
        base64.b64encode(b"\x00\x01" * 4000).decode("utf-8"),
    ],
    "request_id": "tts-req-002",
}

TTS_RESPONSE_EMPTY = {
    "audios": [],
    "request_id": "tts-req-003",
}

TTS_ERROR_INVALID_TEXT = {
    "error": "Text input is empty or invalid",
    "status_code": 400,
}


# =============================================================================
# Embedding responses (for memory system)
# =============================================================================

EMBEDDING_RESPONSE = {
    "embedding": [0.01] * 1024,  # 1024-dim vector matching Pinecone index
    "model": "sarvam-embed-v1",
}

EMBEDDING_RESPONSE_ZERO = {
    "embedding": [0.0] * 1024,
    "model": "sarvam-embed-v1",
}
