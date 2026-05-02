"""`end_call` — gracefully shut down the AgentSession.

Universal across every voice agent. Don't customize unless you really need to.
"""

from __future__ import annotations

import asyncio
import logging

from livekit.agents.llm import function_tool
from livekit.agents.voice.events import RunContext

logger = logging.getLogger(__name__)

_END_CALL_SHUTDOWN_DELAY = 1.5  # seconds — lets goodbye TTS finish

# Strong-ref set so background shutdown tasks aren't garbage-collected mid-flight.
_background_tasks: set[asyncio.Task[None]] = set()


@function_tool
async def end_call(run_ctx: RunContext, reason: str) -> str:
    """End the call. Use when ANY of these are true:
    - The user said goodbye, "we're done", "thanks bye", or similar.
    - The call's purpose is complete (booking made, question answered, etc.).
    - The user said "stop calling me" / "remove me".
    - Voicemail detected (your last 2 turns got no human response).
    - The call has run >4 minutes wall-clock.

    Provide a short warm goodbye in the SAME turn as this tool call.

    Args:
        reason: Brief reason. Required. Examples:
            "user said goodbye", "task complete", "voicemail detected",
            "DNC request", "natural completion".
    """
    safe_reason = (reason or "").strip() or "natural completion"
    logger.info("end_call invoked (reason=%s)", safe_reason[:80])

    async def _delayed_shutdown() -> None:
        await asyncio.sleep(_END_CALL_SHUTDOWN_DELAY)
        run_ctx.session.shutdown()

    task = asyncio.create_task(_delayed_shutdown())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return "Say a brief, warm goodbye now. The call will end in a moment."
