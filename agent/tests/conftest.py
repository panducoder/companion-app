"""Shared test fixtures for Koi voice agent tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_sarvam_client():
    """Mock all Sarvam API calls."""
    client = AsyncMock()
    client.transcribe.return_value = {
        "transcript": "Yaar, aaj bahut boring tha",
        "language": "hi-en",
        "confidence": 0.95,
    }
    client.generate.return_value = "Achha, kya hua? Bata na"
    client.synthesize.return_value = b"fake_audio_pcm_bytes"
    return client


@pytest.fixture
def mock_pinecone():
    """Mock Pinecone vector DB."""
    index = MagicMock()
    index.query.return_value = {
        "matches": [
            {
                "id": "mem_1",
                "score": 0.92,
                "metadata": {
                    "summary": "Talked about job stress",
                    "date": "2025-02-01",
                    "topic": "work",
                    "emotional_tone": "anxious",
                },
            },
            {
                "id": "mem_2",
                "score": 0.85,
                "metadata": {
                    "summary": "Sister's wedding plans",
                    "date": "2025-01-28",
                    "topic": "family",
                    "emotional_tone": "excited",
                },
            },
        ]
    }
    index.upsert.return_value = {"upserted_count": 1}
    return index


@pytest.fixture
def mock_db():
    """Mock asyncpg database pool."""
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchrow.return_value = {
        "id": "user_1",
        "name": "Rahul",
        "companion_name": "Koi",
        "relationship_stage": "familiar",
        "phone": "+919876543210",
        "preferences": {},
    }
    conn.fetch.return_value = []
    conn.execute.return_value = "INSERT 0 1"
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    return pool


@pytest.fixture
def user_context():
    """Standard user context for tests."""
    return {
        "user_id": "user_1",
        "name": "Rahul",
        "companion_name": "Koi",
        "relationship_stage": "familiar",
        "memories": [
            "Discussed job interview last week",
            "Sister's wedding coming up in March",
        ],
    }


@pytest.fixture
def sample_conversation():
    """Sample conversation history for testing."""
    return [
        {"role": "user", "content": "Yaar aaj bahut boring tha office mein"},
        {"role": "assistant", "content": "Achha, kya hua? Kuch interesting nahi tha aaj?"},
        {"role": "user", "content": "Nahi yaar, same meetings same stuff"},
        {
            "role": "assistant",
            "content": "Haan, woh toh hota hai. Kuch aur plan hai evening ka?",
        },
    ]
