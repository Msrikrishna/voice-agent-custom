"""Tools your voice agent can call.

To add a new tool: drop a file here, decorate the function with
`@function_tool` (from `livekit.agents.llm`), then import it below and add
to the `tools=[]` list in `agent.py`.

Claude Code can do this for you — see PROMPT_CHEATSHEET.md prompt #3.
"""

from .end_call import end_call
from .example_tool import example_tool

__all__ = [
    "end_call",
    "example_tool",
]
