"""Shared test fixtures for Koi voice agent tests.

These fixtures define the CONTRACT that the source code must satisfy.
They are independent of implementation details — written from the spec
in BUILD_PLAN.md and PROMPT_ENGINEERING.md.
"""

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.fixtures.mock_pinecone import FakePineconeIndex
from tests.fixtures.mock_responses import (
    EMBEDDING_RESPONSE,
    LLM_COMPLETE_RESPONSE,
    LLM_STREAMING_CHUNKS,
    STT_RESPONSE_HINGLISH,
    TTS_RESPONSE_AUDIO_B64,
    TTS_RESPONSE_SUCCESS,
)


# =============================================================================
# Sarvam API mocks
# =============================================================================


@pytest.fixture
def mock_sarvam_client():
    """Mock all Sarvam API calls with happy-path defaults.

    Attributes:
        transcribe: STT endpoint mock
        generate: LLM completion endpoint mock (non-streaming)
        generate_stream: LLM streaming endpoint mock
        synthesize: TTS endpoint mock
        embed: Embedding endpoint mock
    """
    client = AsyncMock()

    # STT - speech-to-text
    client.transcribe.return_value = STT_RESPONSE_HINGLISH

    # LLM - non-streaming
    client.generate.return_value = LLM_COMPLETE_RESPONSE

    # LLM - streaming: returns an async iterator of chunks
    async def _stream_chunks(*args, **kwargs):
        for chunk in LLM_STREAMING_CHUNKS:
            yield chunk

    client.generate_stream = MagicMock(return_value=_stream_chunks())

    # TTS - text-to-speech
    client.synthesize.return_value = TTS_RESPONSE_SUCCESS

    # Embedding
    client.embed.return_value = EMBEDDING_RESPONSE

    return client


@pytest.fixture
def mock_sarvam_stt():
    """Isolated mock for the SarvamSTT class.

    Conforms to the livekit.agents.stt.STT interface contract:
    - recognize(audio_buffer) -> STTEvent with text
    """
    stt = AsyncMock()
    stt.recognize.return_value = MagicMock(
        text="Yaar, aaj bahut boring tha office mein",
        language="hi-en",
    )
    return stt


@pytest.fixture
def mock_sarvam_llm():
    """Isolated mock for the SarvamLLM class.

    Conforms to the livekit.agents.llm.LLM interface contract:
    - chat(messages) -> LLMStream that yields text chunks
    """
    llm = AsyncMock()

    async def _chat_stream(*args, **kwargs):
        for chunk in LLM_STREAMING_CHUNKS:
            content = chunk["choices"][0]["delta"].get("content", "")
            if content:
                yield MagicMock(text=content)

    llm.chat = MagicMock(return_value=_chat_stream())
    return llm


@pytest.fixture
def mock_sarvam_tts():
    """Isolated mock for the SarvamTTS class.

    Conforms to the livekit.agents.tts.TTS interface contract:
    - synthesize(text) -> AudioFrame bytes
    """
    tts = AsyncMock()
    import base64

    audio_bytes = base64.b64decode(TTS_RESPONSE_AUDIO_B64)
    tts.synthesize.return_value = MagicMock(data=audio_bytes)
    return tts


# =============================================================================
# Pinecone mocks
# =============================================================================


@pytest.fixture
def mock_pinecone():
    """MagicMock Pinecone index with pre-loaded query results.

    Use this for unit tests that just need to verify call patterns.
    """
    index = MagicMock()
    index.query.return_value = {
        "matches": [
            {
                "id": "mem_1",
                "score": 0.92,
                "metadata": {
                    "user_id": "user_1",
                    "summary": "Talked about job stress and wanting to switch careers",
                    "date": "2025-02-01",
                    "topic": "work",
                    "emotional_tone": "anxious",
                },
            },
            {
                "id": "mem_2",
                "score": 0.85,
                "metadata": {
                    "user_id": "user_1",
                    "summary": "Sister's wedding plans, excited about venue selection",
                    "date": "2025-01-28",
                    "topic": "family",
                    "emotional_tone": "excited",
                },
            },
        ]
    }
    index.upsert.return_value = {"upserted_count": 1}
    index.delete.return_value = {}
    index.describe_index_stats.return_value = {
        "dimension": 1024,
        "total_vector_count": 42,
    }
    return index


@pytest.fixture
def fake_pinecone():
    """Fully functional in-memory Pinecone index.

    Use this for integration tests that need real query/upsert behavior.
    """
    index = FakePineconeIndex(dimension=1024)
    # Pre-seed with sample memories
    index.upsert(
        vectors=[
            {
                "id": "mem_user1_001",
                "values": [0.5, 0.3] + [0.01] * 1022,
                "metadata": {
                    "user_id": "user_1",
                    "summary": "Talked about job stress and wanting to switch careers",
                    "date": "2025-02-01",
                    "topic": "work",
                    "emotional_tone": "anxious",
                },
            },
            {
                "id": "mem_user1_002",
                "values": [0.1, 0.8] + [0.01] * 1022,
                "metadata": {
                    "user_id": "user_1",
                    "summary": "Sister's wedding plans, excited about venue selection",
                    "date": "2025-01-28",
                    "topic": "family",
                    "emotional_tone": "excited",
                },
            },
            {
                "id": "mem_user2_001",
                "values": [0.9, 0.1] + [0.01] * 1022,
                "metadata": {
                    "user_id": "user_2",
                    "summary": "Talked about exam preparation",
                    "date": "2025-02-05",
                    "topic": "education",
                    "emotional_tone": "stressed",
                },
            },
        ]
    )
    yield index
    index.reset()


# =============================================================================
# Database mocks
# =============================================================================


@pytest.fixture
def mock_db():
    """Mock asyncpg database pool with realistic return values.

    Simulates the Supabase PostgreSQL connection used by db/client.py.
    The pool.acquire() context manager returns a connection mock.
    """
    pool = AsyncMock()
    conn = AsyncMock()

    # Default user profile
    conn.fetchrow.return_value = {
        "id": "user_1",
        "name": "Rahul",
        "companion_name": "Koi",
        "relationship_stage": "familiar",
        "phone": "+919876543210",
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "last_active_at": datetime(2025, 2, 10, tzinfo=timezone.utc),
        "preferences": {},
        "profile_data": {},
        "subscription_status": "free",
    }

    # Default empty list for fetch queries
    conn.fetch.return_value = []

    # Default insert result
    conn.execute.return_value = "INSERT 0 1"

    # Make pool.acquire() work as async context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    # Expose the connection for direct assertions
    pool._test_conn = conn

    return pool


@pytest.fixture
def mock_db_no_user():
    """Mock DB pool that returns None for user lookups (new/missing user)."""
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchrow.return_value = None
    conn.fetch.return_value = []
    conn.execute.return_value = "INSERT 0 1"
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    pool._test_conn = conn
    return pool


@pytest.fixture
def mock_db_connection_error():
    """Mock DB pool that raises on acquire (simulates connection failure)."""
    pool = AsyncMock()
    pool.acquire.side_effect = ConnectionError("Could not connect to database")
    return pool


# =============================================================================
# User context and conversation fixtures
# =============================================================================


@pytest.fixture
def user_context():
    """Standard user context matching the spec's build_context input shape."""
    return {
        "user_id": "user_1",
        "name": "Rahul",
        "companion_name": "Koi",
        "relationship_stage": "familiar",
        "memories": [
            "Discussed job interview last week — was nervous about it",
            "Sister's wedding coming up in March, excited about shopping",
        ],
    }


@pytest.fixture
def user_context_new():
    """New user with no memories and early relationship stage."""
    return {
        "user_id": "user_new",
        "name": "Priya",
        "companion_name": "Koi",
        "relationship_stage": "early",
        "memories": [],
    }


@pytest.fixture
def user_context_established():
    """Long-term user with many memories."""
    return {
        "user_id": "user_veteran",
        "name": "Amit",
        "companion_name": "Buddy",
        "relationship_stage": "established",
        "memories": [
            "Works at a startup, often stressed about deadlines",
            "Has a dog named Bruno",
            "Loves old Bollywood music, especially Kishore Kumar",
            "Recently broke up, still processing it",
            "Sister's name is Meera, they are close",
        ],
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation history for testing message flow."""
    return [
        {"role": "user", "content": "Yaar aaj bahut boring tha office mein"},
        {"role": "assistant", "content": "Achha, kya hua? Kuch interesting nahi tha aaj?"},
        {"role": "user", "content": "Nahi yaar, same meetings same stuff"},
        {
            "role": "assistant",
            "content": "Haan, woh toh hota hai. Kuch aur plan hai evening ka?",
        },
    ]


@pytest.fixture
def sample_conversation_long():
    """Longer conversation to test token limits and summarization."""
    msgs = []
    topics = [
        ("Aaj office mein bahut kaam tha", "Achha, hectic day? Kya karna pada?"),
        ("Boss ne last minute meeting rakh di", "Uff, wo toh annoying hai. Kya tha meeting mein?"),
        ("Naya project assign hua", "Nice! Kya project hai?"),
        ("Machine learning wala kuch hai", "Oh interesting! Tumhe ML achha lagta hai na?"),
        ("Haan but timeline tight hai", "Hmm, kitna time diya hai?"),
        ("Bas do hafte", "That's tight. But you've got this."),
        ("Dekho kya hota hai", "Haan, best try karo. I believe in you."),
        ("Thanks yaar", "Anytime. Aur kuch hua aaj?"),
    ]
    for user_msg, assistant_msg in topics:
        msgs.append({"role": "user", "content": user_msg})
        msgs.append({"role": "assistant", "content": assistant_msg})
    return msgs


@pytest.fixture
def fake_audio_buffer():
    """Fake audio buffer simulating raw PCM data from microphone."""
    return b"\x00\x01" * 16000  # ~1 second of 16kHz mono PCM


@pytest.fixture
def empty_audio_buffer():
    """Empty/silent audio buffer."""
    return b"\x00\x00" * 16000
