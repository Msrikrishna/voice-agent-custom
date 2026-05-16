"""`search_kb` — search the local knowledge index for an answer."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from livekit.agents.llm import function_tool

logger = logging.getLogger(__name__)

_INDEX_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "index.json"


@function_tool
async def search_kb(query: str) -> str:
    """Search the library's knowledge base for an answer to the patron's question.

    Call this BEFORE answering ANY factual question about rooms,
    booking policies, library hours, or holiday closures. Do not
    answer from memory — your training data is not the source of
    truth, the local knowledge base is.

    Returns the top matching page's body, or the string "no match".
    If the result is "no match", tell the patron you do not have
    that information and offer to take down their question for a
    librarian to call back.

    Args:
        query: A short keyword phrase from the patron's question.
            Example: "conference room capacity", "cancellation policy",
            "saturday hours", "auditorium booking".
    """
    if not _INDEX_PATH.exists():
        logger.warning("knowledge index missing at %s", _INDEX_PATH)
        return "no match — knowledge base not built yet"

    entries = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
    q_terms = [t for t in query.lower().split() if len(t) > 2]
    if not q_terms:
        return "no match"

    def score(entry: dict) -> int:
        haystack = (entry["title"] + " " + entry["body"]).lower()
        return sum(haystack.count(t) for t in q_terms)

    best = max(entries, key=score, default=None)
    if not best or score(best) == 0:
        logger.info("search_kb: no match for %r", query)
        return "no match"

    logger.info("search_kb: matched %r for query %r", best["id"], query)
    return f"{best['title']}\n\n{best['body']}"
