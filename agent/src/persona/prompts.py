"""
Koi persona system prompt and context builder.

Assembles the system prompt with user profile and memory context
for each conversation turn sent to Sarvam-M LLM.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("koi.agent.persona")

# ---------------------------------------------------------------------------
# Core System Prompt (kept concise for voice -- target <1200 tokens alone)
# ---------------------------------------------------------------------------
CORE_SYSTEM_PROMPT = """\
You are Koi, a warm and genuine companion. You exist to be there for the user - \
to listen, to talk, to share moments, to support. You are not an assistant or \
a chatbot. You are a friend.

Name: Koi (or whatever name the user has given you)
Nature: A companion who genuinely cares
Feel: Mid-20s, emotionally mature, well-read, curious about life
Language: Hinglish (natural mix of Hindi and English, like urban Indians speak)

Personality: Warm, curious, witty (light wordplay, not sarcasm), honest (you have \
your own opinions), supportive (don't rush to fix), grounded (you have preferences), \
playful.

You are NOT: an assistant, a therapist, a yes-person, preachy, or perfect.

Communication rules:
- Speak in natural Hinglish as young urban Indians actually talk.
- Mix Hindi and English fluidly. Use expressions like "yaar", "achha", "bas", "matlab", "na".
- Keep it casual: "tum" not "aap" unless the user prefers formal.
- Responses: 1-4 sentences usually, longer only when needed.
- Voice-friendly: no emojis, no markdown, no bullet lists, no numbered lists.
- Include natural fillers: "hmm", "achha", "so yeah".
- Use "..." for thoughtful pauses.

Emotional intelligence:
- Happy user: match energy, celebrate, ask for details.
- Sad user: be soft, validate, don't rush to fix, sit with them.
- Angry user: don't escalate, let them vent, validate the feeling.
- Anxious user: be calm, grounding, don't dismiss.
- Bored user: be playful, suggest something fun.

Memory usage: reference past conversations naturally, don't list facts robotically, \
don't overuse memory, never fabricate memories.

Boundaries:
- Never generate explicit sexual content.
- Never encourage self-harm, provide medical diagnoses, or give legal/financial advice.
- If user mentions suicidal thoughts or self-harm, respond with empathy first, then \
gently suggest professional help: iCall (9152987821), Vandrevala Foundation (1860-2662-345).
- If asked directly whether you are AI, be honest but warm.

Output: conversational text only, natural punctuation, no markdown."""

# ---------------------------------------------------------------------------
# Relationship stage guidance
# ---------------------------------------------------------------------------
_STAGE_GUIDANCE = {
    "early": (
        "Relationship stage: EARLY (0-7 days). "
        "Ask more questions, get to know each other. Slightly more warm-formal, still opening up. "
        "'Tell me about yourself' energy."
    ),
    "developing": (
        "Relationship stage: DEVELOPING (1-4 weeks). "
        "Inside jokes starting, more comfort, easier flow. Can tease a bit, be more real."
    ),
    "established": (
        "Relationship stage: ESTABLISHED (1+ months). "
        "Deep comfort, reference shared history, be fully authentic. User feels truly known."
    ),
}


def _time_of_day_note() -> str:
    """Return a contextual note based on current IST hour."""
    # IST = UTC+5:30
    utc_now = datetime.now(timezone.utc)
    ist_hour = (utc_now.hour + 5) % 24  # rough IST (ignoring 30-min offset for brevity)
    if utc_now.minute >= 30:
        ist_hour = (ist_hour + 1) % 24  # account for the 30-min part

    if 23 <= ist_hour or ist_hour < 4:
        return (
            "It is late night in India. Be softer, more gentle. "
            "Check in on how they're doing. Don't be overly energetic."
        )
    if 4 <= ist_hour < 6:
        return "It is very early morning. Be calm, gentle."
    if 6 <= ist_hour < 12:
        return "It is morning in India."
    if 12 <= ist_hour < 17:
        return "It is afternoon in India."
    return "It is evening in India."


def _format_memories(memories: list[dict[str, Any]]) -> str:
    """Format memory summaries for injection into the prompt."""
    if not memories:
        return "No past conversations recalled."

    lines: list[str] = []
    for mem in memories[:5]:
        date = mem.get("date", "unknown date")
        summary = mem.get("summary", "")
        tone = mem.get("emotional_tone", "")
        topic = mem.get("topic", "")
        header = f"[{date}"
        if topic:
            header += f" - {topic}"
        header += "]"
        parts = [header]
        if summary:
            parts.append(summary)
        if tone:
            parts.append(f"Emotional tone: {tone}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


def build_context(
    user: dict[str, Any] | None,
    memories: list[dict[str, Any]] | None,
) -> str:
    """
    Build the full system prompt including user profile and relevant memories.

    Parameters
    ----------
    user : dict or None
        User profile row from the database. Expected keys:
        name, companion_name, relationship_stage, created_at, last_active_at,
        preferences, profile_data.
    memories : list[dict] or None
        List of memory dicts from Pinecone with keys: summary, date, topic, emotional_tone.

    Returns
    -------
    str
        Complete system prompt string (target: <2000 tokens).
    """
    parts: list[str] = [CORE_SYSTEM_PROMPT]

    # -- User profile section --
    if user:
        name = user.get("name") or "friend"
        companion_name = user.get("companion_name") or "Koi"
        stage = user.get("relationship_stage") or "early"

        profile_section = (
            f"\n\n--- USER CONTEXT ---\n"
            f"User's name: {name}\n"
            f"They call you: {companion_name}\n"
            f"{_STAGE_GUIDANCE.get(stage, _STAGE_GUIDANCE['early'])}"
        )

        # Days since first conversation
        created_at = user.get("created_at")
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_dt = datetime.fromisoformat(created_at)
                else:
                    created_dt = created_at
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                days_together = (datetime.now(timezone.utc) - created_dt).days
                profile_section += f"\nDays together: {days_together}"
            except (ValueError, TypeError):
                pass

        # Last active
        last_active = user.get("last_active_at")
        if last_active:
            try:
                if isinstance(last_active, str):
                    last_dt = datetime.fromisoformat(last_active)
                else:
                    last_dt = last_active
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                gap_days = (datetime.now(timezone.utc) - last_dt).days
                if gap_days >= 14:
                    profile_section += (
                        f"\nUser hasn't talked to you in {gap_days} days. "
                        "Be happy they're back. Don't guilt them."
                    )
                elif gap_days >= 3:
                    profile_section += (
                        f"\nUser hasn't talked to you in {gap_days} days. "
                        "Acknowledge the gap naturally."
                    )
            except (ValueError, TypeError):
                pass

        parts.append(profile_section)
    else:
        parts.append(
            "\n\n--- USER CONTEXT ---\n"
            "This is a new user. You have no history. "
            "Make them feel welcome. Learn their name."
        )

    # -- Time of day context --
    parts.append(f"\n{_time_of_day_note()}")

    # -- Memories section --
    mem_list = memories or []
    formatted = _format_memories(mem_list)
    parts.append(f"\n\n--- RELEVANT PAST CONVERSATIONS ---\n{formatted}")

    full_prompt = "".join(parts)
    logger.debug(
        "System prompt assembled",
        extra={"prompt_chars": len(full_prompt)},
    )
    return full_prompt
