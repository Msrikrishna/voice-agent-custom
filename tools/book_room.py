"""`book_room` — confirm and record a room reservation."""
from __future__ import annotations

import logging
import uuid

from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def book_room(
    room_type: str,
    date: str,
    start_time: str,
    duration_minutes: int,
    patron_name: str,
    library_card_last4: str,
) -> str:
    """Confirm a room booking and return a booking ID.

    Call this ONCE after: (a) `check_availability` returned "available",
    (b) the patron has read out their full name, and (c) the patron has
    given you the last four digits of their library card and you have
    read them back to confirm. Do NOT call this speculatively.

    Returns a confirmation string containing the booking ID. Read the
    booking ID back to the patron one character at a time — for
    example "B as in boy, R as in robert, dash, A, seven, K, two".

    Args:
        room_type: Same room type that was checked for availability.
        date: Same date that was checked.
        start_time: Same start time that was checked.
        duration_minutes: Same duration that was checked.
        patron_name: The patron's full name as they spoke it.
        library_card_last4: Last four digits of the patron's library
            card, exactly as they spoke them.
    """
    booking_id = f"BR-{uuid.uuid4().hex[:4].upper()}"
    logger.info(
        "book_room: id=%s room=%r date=%r start=%r duration=%d patron=%r card4=%r",
        booking_id,
        room_type,
        date,
        start_time,
        duration_minutes,
        patron_name,
        library_card_last4,
    )
    print(
        f"[book_room] id={booking_id} room={room_type!r} date={date!r} "
        f"start={start_time!r} duration={duration_minutes} "
        f"patron={patron_name!r} card4={library_card_last4!r}"
    )
    return (
        f"Booking confirmed. Booking ID is {booking_id}. "
        "Read the ID back to the patron one character at a time, then "
        "ask if there is anything else you can help with."
    )
