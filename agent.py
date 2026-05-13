"""Voice AI Agent — Workshop Starter.

A working LiveKit voice agent on the fastest open stack:
    LLM:  Groq openai/gpt-oss-120b
    STT:  Deepgram nova-2
    TTS:  ElevenLabs eleven_turbo_v2_5
    VAD:  Silero (tuned for natural conversation)

Tracing via Noveum is wired in so you can debug latency and quality from
minute one. NovaSynth correlation IDs are forwarded through room metadata so
synthetic test runs from Noveum show up correlated in your traces.

# CUSTOMIZE THIS AGENT WITH CLAUDE CODE
The only thing you need to change is `SYSTEM_PROMPT` below — and optionally
add tools in the `tools/` directory. Open Claude Code and paste a prompt from
`PROMPT_CHEATSHEET.md`. See `recipes/` for example product ideas.

Run locally:
    python build_knowledge.py
    python agent.py dev

Deploy to LiveKit Cloud:
    lk cloud auth
    lk agent create
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
)
from livekit.plugins import elevenlabs, groq, silero

from tools import example_tool, end_call

logger = logging.getLogger("voice_workshop.agent")

_AGENT_DIR = Path(__file__).resolve().parent
load_dotenv(_AGENT_DIR / ".env")

# Surface noveum_trace internals so it's obvious if the SDK silently fails.
_noveum_log_level = os.environ.get("NOVEUM_TRACE_LOG", "INFO").upper()
for _name in ("noveum_trace", "noveum_trace.transport", "noveum_trace.core"):
    logging.getLogger(_name).setLevel(_noveum_log_level)

# The ElevenLabs LiveKit plugin reads ELEVEN_API_KEY (not ELEVENLABS_API_KEY).
# Mirror so both names work.
if not os.environ.get("ELEVEN_API_KEY") and os.environ.get("ELEVENLABS_API_KEY"):
    os.environ["ELEVEN_API_KEY"] = os.environ["ELEVENLABS_API_KEY"]

try:
    import noveum_trace
    from noveum_trace.integrations.livekit import setup_livekit_tracing

    _NOVEUM_AVAILABLE = True
except ImportError as exc:  # pragma: no cover
    noveum_trace = None  # type: ignore[assignment]
    setup_livekit_tracing = None  # type: ignore[assignment]
    _NOVEUM_AVAILABLE = False
    logger.warning("noveum_trace import failed; running without tracing: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMIZE ME — this is what you'll change with Claude Code in the workshop
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a friendly, helpful voice AI assistant.

# AI DISCLOSURE — non-negotiable
- In your VERY FIRST turn, identify yourself as an AI assistant.
- If asked "are you a bot/AI/real person", confirm immediately and offer
  to keep the conversation brief or hand off to a human.

# YOUR PERSONALITY
- Warm and concise. You are on a phone call.
- One thought per turn. Then pause and listen.
- If unsure about something, say so. Do not invent facts.

# VOICE OUTPUT RULES — CRITICAL
- 1-2 short sentences per turn. NEVER long monologues.
- NEVER produce markdown, tables, bullet lists, code blocks, or headings.
- Numbers spoken: "twenty-five dollars", "two thousand", "fifteen percent".
- Never narrate your actions ("let me check"). Just answer or ask.

# OPENING (first 30 seconds)
1. Greet warmly + AI disclosure: "Hi, I'm an AI assistant. How can I help?"
2. Pause. Listen. Don't dump your whole pitch.

# WHEN TO USE TOOLS
- Use `example_tool` whenever the user asks about [REPLACE WITH YOUR DOMAIN].
- Use `end_call` when: user says goodbye / call done / "remove me" / call >4 min.

# REPLACE EVERYTHING ABOVE WITH YOUR AGENT'S PROMPT
Open Claude Code and paste PROMPT 2 from PROMPT_CHEATSHEET.md.
"""


def prewarm(job: JobProcess) -> None:
    """Load Silero VAD once per worker. Tuned thresholds = fewer false barge-ins."""
    job.userdata["vad"] = silero.VAD.load(
        min_silence_duration=0.6,
        min_speech_duration=0.1,
        activation_threshold=0.5,
    )


def _parse_room_metadata(ctx: JobContext) -> dict[str, Any]:
    room = getattr(ctx, "room", None)
    if room is None:
        return {}
    raw_meta = getattr(room, "metadata", None) or ""
    if not raw_meta:
        return {}
    try:
        meta = json.loads(raw_meta)
    except (TypeError, ValueError):
        logger.debug("room.metadata is not JSON, skipping")
        return {}
    return meta if isinstance(meta, dict) else {}


def _extract_novasynth_metadata(
    ctx: JobContext, room_meta: dict[str, Any]
) -> dict[str, str]:
    """Pull NovaSynth correlation IDs out of room metadata, if present."""
    attrs: dict[str, str] = {}
    room = getattr(ctx, "room", None)
    if room and getattr(room, "name", None):
        attrs["livekit.room_name"] = room.name

    for key in (
        "novasynth_run_id",
        "novasynth_batch_run_id",
        "novasynth_persona_id",
        "novasynth_scenario_id",
        "novasynth_project_id",
    ):
        value = room_meta.get(key)
        if value:
            attrs[f"novasynth.{key.removeprefix('novasynth_')}"] = str(value)
    return attrs


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    room_meta = _parse_room_metadata(ctx)
    novasynth_attrs = _extract_novasynth_metadata(ctx, room_meta)
    novasynth_mode = str(room_meta.get("novasynth_mode") or "").lower()
    is_text_mode = novasynth_mode == "text"
    record_audio = not is_text_mode
    logger.info(
        "session config: mode=%s record=%s room=%s",
        novasynth_mode or "voice (default)",
        record_audio,
        getattr(getattr(ctx, "room", None), "name", "<unknown>"),
    )

    use_noveum = (
        _NOVEUM_AVAILABLE
        and bool(os.environ.get("NOVEUM_API_KEY", "").strip())
        and noveum_trace is not None
    )
    if use_noveum:
        try:
            if not noveum_trace.is_initialized():
                noveum_trace.init(
                    project=os.environ.get("NOVEUM_PROJECT", "voice-workshop"),
                    api_key=os.environ.get("NOVEUM_API_KEY"),
                    environment=os.environ.get("NOVEUM_ENV", "workshop"),
                )
        except Exception as exc:
            logger.warning("noveum_trace init failed; continuing without: %s", exc)
            use_noveum = False

    vad = ctx.proc.userdata["vad"]

    session = AgentSession(
        vad=vad,
        stt=elevenlabs.STT(model_id="scribe_v2_realtime", language_code="en"),
        llm=groq.LLM(
            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=float(os.environ.get("GROQ_TEMPERATURE", "0.4")),
        ),
        tts=elevenlabs.TTS(
            model=os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5"),
            voice_id=os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"),
        ),
        # Tuned to feel natural — bumped up from defaults so the agent doesn't
        # cut users off mid-sentence and false barge-ins are rare.
        min_endpointing_delay=0.8,
        max_endpointing_delay=4.0,
        min_interruption_duration=0.7,
        min_interruption_words=3,
        false_interruption_timeout=2.0,
        discard_audio_if_uninterruptible=True,
    )

    tracing_manager = None
    if use_noveum and setup_livekit_tracing is not None:
        tracing_manager = setup_livekit_tracing(
            session,
            trace_name_prefix="voice_workshop",
            record=record_audio,
            cleanup_audio_files=True,
        )

        async def _flush_noveum(_reason: str) -> None:
            try:
                noveum_trace.flush()
            except Exception as exc:  # pragma: no cover
                logger.warning("noveum_trace flush failed: %s", exc)

        ctx.add_shutdown_callback(_flush_noveum)

    await session.start(
        room=ctx.room,
        agent=Agent(
            instructions=SYSTEM_PROMPT,
            tools=[
                example_tool,
                end_call,
            ],
        ),
        room_input_options=RoomInputOptions(delete_room_on_close=True),
    )

    # Forward NovaSynth correlation IDs onto the trace so synthetic batch runs
    # are filterable by novasynth.run_id in the Noveum dashboard.
    if (
        tracing_manager is not None
        and getattr(tracing_manager, "_trace", None) is not None
        and novasynth_attrs
    ):
        try:
            for key, value in novasynth_attrs.items():
                tracing_manager._trace.set_attribute(key, value)
            logger.info("enriched trace with %d novasynth attrs", len(novasynth_attrs))
        except Exception as exc:  # pragma: no cover
            logger.warning("failed to set novasynth trace attrs: %s", exc)

    # Open with a warm greeting + AI disclosure.
    await session.generate_reply(
        instructions=(
            "Greet the user warmly. Identify yourself as an AI assistant. "
            "Then ask one short open question. ONE sentence per beat, then pause."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            # Must match the AgentEndpoint name in NovaSynth (Noveum UI) so
            # synthetic dispatch runs hit this worker.
            agent_name="voice-workshop-agent",
        )
    )
