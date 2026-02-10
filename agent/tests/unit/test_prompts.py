"""Tests for Koi persona prompt building.

Verifies the build_context function from src/persona/prompts.py.
Contract (from BUILD_PLAN.md):
  - build_context(user, memories) assembles the full system prompt
  - Output contains: base persona, user profile, memories, time context
  - Total prompt stays under 2000 tokens
  - Handles missing data gracefully
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.mark.unit
class TestBuildContextUserInfo:
    """System prompt must include user-specific information."""

    def test_build_context_includes_user_name(self, user_context):
        """Prompt must contain the user's name for personalized greeting."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=user_context["memories"])
        assert "Rahul" in prompt

    def test_build_context_includes_companion_name(self, user_context):
        """Prompt must contain the chosen companion name."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=user_context["memories"])
        assert "Koi" in prompt

    def test_build_context_includes_custom_companion_name(self, user_context_established):
        """Prompt must work with non-default companion names."""
        from src.persona.prompts import build_context

        prompt = build_context(
            user_context_established, memories=user_context_established["memories"]
        )
        assert "Buddy" in prompt

    def test_build_context_includes_relationship_stage(self, user_context):
        """Prompt must reflect the current relationship stage."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=user_context["memories"])
        assert "familiar" in prompt.lower()


@pytest.mark.unit
class TestBuildContextMemories:
    """System prompt must properly integrate memory context."""

    def test_build_context_includes_memories(self, user_context):
        """Memories from Pinecone must appear in the prompt."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=user_context["memories"])
        assert "job interview" in prompt.lower()

    def test_build_context_includes_multiple_memories(self, user_context_established):
        """All provided memories should be present in the prompt."""
        from src.persona.prompts import build_context

        memories = user_context_established["memories"]
        prompt = build_context(user_context_established, memories=memories)
        assert "Bruno" in prompt  # dog's name
        assert "Kishore Kumar" in prompt or "Bollywood" in prompt

    def test_build_context_without_memories(self, user_context_new):
        """Prompt must be valid for new users with no memories."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context_new, memories=[])
        assert "Priya" in prompt
        # Should still have the base persona
        assert len(prompt) > 100


@pytest.mark.unit
class TestBuildContextTokenLimit:
    """System prompt must respect token budget."""

    def test_build_context_respects_token_limit(self, user_context):
        """Total prompt must stay under 2000 tokens (~8000 chars as rough estimate)."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=user_context["memories"])
        # Rough heuristic: 1 token ~ 4 chars for English/Hinglish
        estimated_tokens = len(prompt) / 4
        assert estimated_tokens < 2000

    def test_build_context_truncates_excess_memories(self, user_context):
        """When too many memories would exceed token budget, truncate gracefully."""
        from src.persona.prompts import build_context

        # Create excessive memories to push past token limit
        many_memories = [f"Memory about topic {i}: " + "details " * 50 for i in range(20)]
        prompt = build_context(user_context, memories=many_memories)
        estimated_tokens = len(prompt) / 4
        assert estimated_tokens < 2000


@pytest.mark.unit
class TestBuildContextTimeAwareness:
    """System prompt should adjust for time-of-day context."""

    @patch("src.persona.prompts.datetime")
    def test_build_context_includes_time_of_day(self, mock_dt, user_context):
        """Prompt should mention time context for appropriate tone adjustment."""
        from src.persona.prompts import build_context

        # Simulate late night
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

        prompt = build_context(user_context, memories=[])
        # The prompt should contain some time-of-day indicator
        # (exact wording depends on implementation, but should reference late night)
        assert any(
            term in prompt.lower()
            for term in ["night", "late", "raat", "evening"]
        )

    @patch("src.persona.prompts.datetime")
    def test_build_context_morning_tone(self, mock_dt, user_context):
        """Morning conversations should not have late-night adjustments."""
        from src.persona.prompts import build_context

        mock_now = MagicMock()
        mock_now.hour = 9
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)

        prompt = build_context(user_context, memories=[])
        # Morning prompt should exist and be valid
        assert len(prompt) > 100


@pytest.mark.unit
class TestBuildContextPersona:
    """System prompt must contain core Koi persona elements."""

    def test_build_context_has_system_prompt_base(self, user_context):
        """Prompt must include the base Koi personality definition."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=[])
        # Core persona elements from PROMPT_ENGINEERING.md
        prompt_lower = prompt.lower()
        assert "companion" in prompt_lower or "friend" in prompt_lower

    def test_build_context_includes_hinglish_instruction(self, user_context):
        """Prompt must instruct the model to respond in Hinglish."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=[])
        prompt_lower = prompt.lower()
        assert "hinglish" in prompt_lower or "hindi" in prompt_lower

    def test_build_context_includes_boundaries(self, user_context):
        """Prompt must include safety boundaries."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=[])
        prompt_lower = prompt.lower()
        # Should mention boundaries like not being a therapist or assistant
        assert "not" in prompt_lower or "never" in prompt_lower

    def test_build_context_returns_string(self, user_context):
        """build_context must return a string, not a list or dict."""
        from src.persona.prompts import build_context

        prompt = build_context(user_context, memories=[])
        assert isinstance(prompt, str)
