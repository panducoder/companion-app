"""Tests for Koi persona prompt building."""

import pytest


class TestPromptBuilder:
    """Test system prompt construction."""

    def test_build_context_includes_user_name(self, user_context):
        """System prompt should include user's name."""
        # TODO: Implement when prompts.py is built
        # from src.persona.prompts import build_context
        # prompt = build_context(user_context, memories=[])
        # assert "Rahul" in prompt
        pass

    def test_build_context_includes_memories(self, user_context):
        """System prompt should include relevant memories."""
        # TODO: Implement when prompts.py is built
        pass

    def test_build_context_respects_token_limit(self, user_context):
        """System prompt should stay under 2000 tokens."""
        # TODO: Implement when prompts.py is built
        pass

    def test_build_context_includes_time_of_day(self, user_context):
        """System prompt should adjust for time of day (late night = softer tone)."""
        # TODO: Implement when prompts.py is built
        pass

    def test_build_context_without_memories(self, user_context):
        """System prompt should work for new users with no memories."""
        # TODO: Implement when prompts.py is built
        pass
