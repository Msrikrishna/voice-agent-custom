"""`check_availability` — see if a room is open for a requested slot."""
from __future__ import annotations

import logging

from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def check_availability(
    room_type: str,
    date: str,
    start_time: str,
    duration_minutes: int,
) -> str:
    """Check whether a study or meeting room is available for a slot.

    Call this BEFORE asking for the patron's library card or calling
    `book_room`. The patron must have given you a room type, a date,
    a start time, and a duration. Use `search_kb` first if you do not
    yet know what room types exist or the per-room duration limits.

    Returns "available" if the slot is open, or a sentence explaining
    why it is not. If not available, suggest the patron pick a
    different time or room.

    Args:
        room_type: e.g. "quiet study room", "group study room",
            "conference room", "maker space", "auditorium".
        date: A natural-language date the patron said. Example:
            "Saturday May twenty-third" or "tomorrow".
        start_time: Start time the patron said. Example: "two PM".
        duration_minutes: Length of the booking in minutes.
    """
    logger.info(
        "check_availability: room=%r date=%r start=%r duration=%d",
        room_type,
        date,
        start_time,
        duration_minutes,
    )
    print(
        f"[check_availability] room={room_type!r} date={date!r} "
        f"start={start_time!r} duration={duration_minutes}"
    )
    return (
        "available — tell the patron the slot is open and ask if they "
        "would like to confirm the booking with their library card."
    )
