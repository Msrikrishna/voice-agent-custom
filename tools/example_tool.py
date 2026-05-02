"""An example tool. Replace or duplicate this for your own agent's tools.

The docstring is visible to the LLM — write it as if it's instructions to
a junior engineer who only ever reads the docstring.
"""

from __future__ import annotations

import logging

from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def example_tool(query: str) -> str:
    """Look up information about a topic.

    Call this whenever the user asks a question that requires looking
    something up. Returns a short factual answer.

    Args:
        query: A short phrase describing what to look up.
            Examples: "store hours", "menu", "appointment availability".
    """
    # TODO: replace this stub with real logic. For the workshop, just
    # log the query and return a placeholder string. Claude Code can
    # rewrite the body to hit your real backend / database / API.
    logger.info("example_tool called with query=%r", query)
    return f"(stub) You asked about: {query}. Replace this with real logic."
