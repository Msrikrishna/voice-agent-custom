"""`end_call` — gracefully shut down the AgentSession.

The tool guards itself: if the LLM fires it without a real goodbye in the
user's most recent turn, we refuse and return a message that nudges the
model back into the conversation. This catches hallucinated "voicemail
detected" / "task complete" triggers we kept seeing in practice.
"""

from __future__ import annotations

import asyncio
import logging
import re

from livekit.agents.llm import function_tool
from livekit.agents.voice.events import RunContext

logger = logging.getLogger(__name__)

_END_CALL_SHUTDOWN_DELAY = 1.5  # seconds — lets goodbye TTS finish

# Strong-ref set so background shutdown tasks aren't garbage-collected mid-flight.
_background_tasks: set[asyncio.Task[None]] = set()

# Phrases that mean the user is closing the call. Matched case-insensitively
# against the user's most recent message.
_GOODBYE_PATTERNS = (
    r"\bbye\b",
    r"\bgoodbye\b",
    r"\bbye[- ]?bye\b",
    r"\bsee you\b",
    r"\bsee ya\b",
    r"\btalk (to you )?(later|soon)\b",
    r"\btake care\b",
    r"\bgotta go\b",
    r"\bhave to go\b",
    r"\bthat'?s all\b",
    r"\bthat'?s it\b",
    r"\bi'?m good\b",
    r"\b(i am|i'?m) done\b",
    r"\b(we are|we'?re) done\b",
    r"\b(are |we'?re )?all done\b",
    r"\bno thanks\b",
    r"\bnot interested\b",
    r"\bstop calling\b",
    r"\bdon'?t call\b",
    r"\bremove me\b",
    r"\bdo not call\b",
    r"\bend (the )?call\b",
    r"\bhang up\b",
)
_GOODBYE_RE = re.compile("|".join(_GOODBYE_PATTERNS), re.IGNORECASE)


def _last_user_text(run_ctx: RunContext) -> str | None:
    """Return the text of the user's most recent message, or None."""
    try:
        chat_ctx = run_ctx.session.current_agent.chat_ctx
    except Exception:
        return None
    for item in reversed(list(chat_ctx.items)):
        if getattr(item, "role", None) != "user":
            continue
        text = getattr(item, "text_content", None)
        if callable(text):
            try:
                text = text()
            except Exception:
                text = None
        if text:
            return str(text).strip()
    return None


@function_tool
async def end_call(run_ctx: RunContext, reason: str) -> str:
    """End the call. ONE TRIGGER ONLY:
    - The user's MOST RECENT turn contained a clear goodbye / DNC phrase.
      Examples: "bye", "thanks bye", "we're done", "I'm good", "that's
      all", "talk later", "stop calling me", "remove me", "don't call".

    There is no other trigger. The tool programmatically inspects the
    user's last message; if it does not contain a goodbye phrase, the
    tool REFUSES and returns an error string telling you to keep
    talking. You cannot bypass this by writing "voicemail detected" or
    "call exceeded four minutes" in `reason` — the validator ignores
    `reason` entirely. Do not try.

    NEVER call this tool:
    - In the same turn as another tool (e.g. place_order). Confirm that
      tool's result, wait for the user's reply, then later — only if
      they say goodbye — call this.
    - Right after the user gave you information or confirmed something.
      They are still engaged. Continue the conversation.
    - Because "the task feels complete". The user must close the call.

    This tool starts a one-and-a-half second shutdown timer. Any user
    speech in that window is silently dropped. Only fire when the user
    has just said goodbye in their most recent turn.

    Provide a short warm goodbye in the SAME turn as this tool call.

    Args:
        reason: One short phrase logged for analytics. The validator
            does NOT use it. Example: "user said bye".
    """
    safe_reason = (reason or "").strip() or "natural completion"
    last_user = _last_user_text(run_ctx)

    # GROUND TRUTH ONLY. We do NOT trust the LLM's `reason` string —
    # past runs showed the model fabricating "voicemail detected" and
    # "call exceeded four minutes" to bypass softer checks. The only
    # signal we accept is the user's own most recent message containing
    # a goodbye / DNC phrase. (The goodbye regex covers "remove me",
    # "stop calling", "don't call", etc., so DNC is handled here too.)
    user_said_goodbye = bool(last_user and _GOODBYE_RE.search(last_user))

    if not user_said_goodbye:
        logger.warning(
            "end_call REFUSED (reason=%r last_user=%r)",
            safe_reason[:80],
            (last_user or "<no user message>")[:120],
        )
        return (
            "REFUSED: do not end the call. The user has not said goodbye in "
            "their most recent turn. Ignore your previous plan to end the "
            "call — continue the conversation. Answer their question, ask "
            "the next field you need, or wait for them to speak."
        )

    logger.info("end_call invoked (reason=%s)", safe_reason[:80])

    async def _delayed_shutdown() -> None:
        await asyncio.sleep(_END_CALL_SHUTDOWN_DELAY)
        run_ctx.session.shutdown()

    task = asyncio.create_task(_delayed_shutdown())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return "Say a brief, warm goodbye now. The call will end in a moment."
