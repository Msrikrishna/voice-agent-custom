"""`place_order` — confirm and record the customer's order."""
from __future__ import annotations

import logging

from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def place_order(items: str) -> str:
    """Place the customer's confirmed order.

    Call this ONCE when the customer has stated what they want AND
    confirmed they are ready to order. Do NOT call this speculatively
    or to check availability — only after explicit confirmation.

    Args:
        items: Comma-separated list of items, sizes, and quantities the
            customer confirmed out loud.
            Example: "1 large pepperoni pizza, 1 medium margherita with extra cheese, 2 sodas".
    """
    logger.info("place_order: %r", items)
    print(f"[place_order] items={items!r}")
    return (
        f"Order placed: {items}. "
        "Tell the customer their order is confirmed and ask if there is anything else."
    )
