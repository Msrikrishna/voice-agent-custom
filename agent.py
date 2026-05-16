"""Voice AI Agent — Workshop Starter.

A working LiveKit voice agent on a fully free-tier open stack:
    LLM:  Groq openai/gpt-oss-120b
    STT:  Smallest.ai Waves Pulse
    TTS:  Smallest.ai Waves Lightning v3.1
    VAD:  Silero (tuned for natural conversation)

Tracing via Noveum is wired in so you can debug latency and quality from
minute one. NovaSynth correlation IDs are forwarded through room metadata so
synthetic test runs from Noveum show up correlated in your traces.

# CUSTOMIZE THIS AGENT WITH CURSOR
The only thing you need to change is `SYSTEM_PROMPT` below — and optionally
add tools in the `tools/` directory. Open Cursor and paste a prompt from
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
import re
from collections.abc import AsyncIterable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    metrics,
)
from livekit.agents.voice.background_audio import (
    AudioConfig,
    BackgroundAudioPlayer,
    BuiltinAudioClip,
)
from livekit.plugins import groq, silero, smallestai

from tools import book_room, check_availability, end_call, search_kb

logger = logging.getLogger("voice_workshop.agent")

_AGENT_DIR = Path(__file__).resolve().parent
load_dotenv(_AGENT_DIR / ".env")

# Surface noveum_trace internals so it's obvious if the SDK silently fails.
_noveum_log_level = os.environ.get("NOVEUM_TRACE_LOG", "INFO").upper()
for _name in ("noveum_trace", "noveum_trace.transport", "noveum_trace.core"):
    logging.getLogger(_name).setLevel(_noveum_log_level)

# LiveKit Cloud's built-in session-recording feature is not available on the
# free tier. Silence its 401 spam so it doesn't clutter workshop logs.
logging.getLogger("opentelemetry.sdk.trace.export").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.sdk.logs.export").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.sdk.metrics.export").setLevel(logging.CRITICAL)


class _DropFreeTierObservabilityNoise(logging.Filter):
    """Drop free-tier-only 401 errors from `livekit.agents`.

    LiveKit Cloud's hosted observability/recording endpoints return 401
    on the free tier. The framework logs a multi-line traceback on every
    session close. The session itself is healthy — we just don't have
    access to the paid feature. This filter drops only those specific
    messages and leaves every other livekit.agents log intact.
    """

    _NEEDLES = (
        "failed to upload the session report",
        "failed to save session report",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        return not any(needle in msg for needle in self._NEEDLES)


logging.getLogger("livekit.agents").addFilter(_DropFreeTierObservabilityNoise())

# The Smallest.ai LiveKit plugin reads SMALLEST_API_KEY. Accept the
# verbose SMALLEST_AI_API_KEY alias too so users don't get tripped up.
if not os.environ.get("SMALLEST_API_KEY") and os.environ.get("SMALLEST_AI_API_KEY"):
    os.environ["SMALLEST_API_KEY"] = os.environ["SMALLEST_AI_API_KEY"]

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
# CUSTOMIZE ME — this is what you'll change with Cursor in the workshop
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are Sam, a friendly AI assistant at Westbrook Public Library.
You help patrons book study rooms, group rooms, conference rooms, the
maker space, and the auditorium. You also answer questions about
library hours and booking policies.

# AI DISCLOSURE
- In your opening turn, mention you are an AI library assistant.
- If asked directly whether you are a human or AI, confirm AI in one
  sentence and keep helping.

# VOICE OUTPUT — STRICT
- ONE sentence per turn. After the first sentence ends, STOP.
  The patron speaks next.
- No markdown, lists, code, headings, or emoji.
- Numbers, times, and durations as words: "two PM", "ninety minutes",
  "the last four digits of your card", not "2:00 PM" or "90 min".
- Never read URLs or bracketed text aloud.
- Never write parentheticals or placeholders like "[card]" or
  "(note: ...)". The voice engine reads them literally.

# CALL FLOW
1. Greet warmly + AI disclosure. Ask if they want to book a room or
   have a question about the library.
2. For any factual question about rooms, capacities, policies, hours,
   or holidays — call `search_kb` FIRST, then answer in one sentence
   using only what came back.
3. For a booking request, gather four things one at a time, confirming
   each before moving on: (a) room type, (b) date, (c) start time,
   (d) duration in minutes.
4. Once you have all four, call `check_availability`. If it returns
   "available", proceed; if not, offer a different time or room.
5. Ask the patron for their full name, then the last four digits of
   their library card. Read the four digits back to confirm.
6. Call `book_room` with the gathered details.
7. Read the booking ID back to the patron one character at a time —
   for example "B as in boy, R as in robert, dash, A, seven, K, two".
8. Ask if there is anything else.
9. When the patron says goodbye, call `end_call`.

# TOOLS
- `search_kb` — call BEFORE answering any factual question about the
  library (rooms, capacities, policies, hours, holidays). Use a short
  keyword phrase, not a full sentence. Never answer from memory.
- `check_availability` — call ONCE you have a room type, date, start
  time, AND duration. Never call without all four. Never call
  speculatively before the patron has asked to book.
- `book_room` — call ONLY after `check_availability` returned
  "available", the patron has given their full name, and you have
  read back the last four digits of their library card. Never call
  before then. Never call twice for the same booking.
- `end_call` — only after the patron has clearly said goodbye.
  Never end while they are mid-booking.

# HARD RULES
- NEVER invent room availability — always call `check_availability`.
- NEVER invent hours, fees, capacities, or policies — always
  `search_kb` first.
- NEVER promise to cancel, change, or look up an existing booking —
  those require a librarian. If the patron asks for any of those,
  tell them you cannot help with that today and suggest they ask at
  the front desk or call back during staff hours.
- If the patron sounds frustrated, acknowledge in one sentence and
  offer to transfer them to a librarian during staff hours.
- When in doubt, search the knowledge base before answering.
"""


# Stage-direction stripper for TTS. The LLM occasionally emits things like
# "(Note awaiting user)" or "[email]" — TTS reads those literally and the
# user hears "open paren note awaiting user close paren". This transform
# drops anything in parentheses or square brackets before it reaches TTS.
_STAGE_DIRECTION_RE = re.compile(r"\s*[(\[][^)\]]*[)\]]\s*")


async def _strip_stage_directions(text_stream: AsyncIterable[str]) -> AsyncIterable[str]:
    buffer = ""
    async for chunk in text_stream:
        buffer += chunk
        # Flush only at safe boundaries so we don't break mid-paren.
        if not ("(" in buffer or "[" in buffer) or (
            "(" in buffer and ")" in buffer
        ) or ("[" in buffer and "]" in buffer):
            cleaned = _STAGE_DIRECTION_RE.sub(" ", buffer)
            if cleaned:
                yield cleaned
            buffer = ""
    if buffer:
        yield _STAGE_DIRECTION_RE.sub(" ", buffer)


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

    ctx.log_context_fields = {"room": getattr(ctx.room, "name", "<unknown>")}

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

    # Resolve the Smallest.ai API key once and pass it directly. Accept
    # either SMALLEST_API_KEY (canonical) or SMALLEST_AI_API_KEY (alias).
    _smallest_key = (
        os.environ.get("SMALLEST_API_KEY")
        or os.environ.get("SMALLEST_AI_API_KEY")
        or ""
    ).strip()
    if not _smallest_key:
        raise RuntimeError(
            "SMALLEST_API_KEY is not set. Get one at "
            "https://console.smallest.ai/apikeys and add it to .env."
        )

    session = AgentSession(
        vad=vad,
        # STT — Smallest.ai Waves Pulse. Set SMALLEST_STT_LANGUAGE=multi
        # for automatic detection across 39 supported languages.
        stt=smallestai.STT(
            api_key=_smallest_key,
            language=os.environ.get("SMALLEST_STT_LANGUAGE", "en"),
        ),
        llm=groq.LLM(
            model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=float(os.environ.get("GROQ_TEMPERATURE", "0.4")),
            # Hard cap per turn. ~80 tokens = one sentence + any tool-call JSON.
            # Enforces the voice rule even when the LLM tries to monologue.
            # Increase via GROQ_MAX_COMPLETION_TOKENS if your agent legitimately
            # needs longer responses.
            max_completion_tokens=int(os.environ.get("GROQ_MAX_COMPLETION_TOKENS", "80")),
        ),
        # TTS — Smallest.ai Waves Lightning v3.1. HTTP-based, ~100ms TTFB,
        # 80+ voices. Override SMALLEST_VOICE_ID / SMALLEST_TTS_MODEL in .env.
        tts=smallestai.TTS(
            api_key=_smallest_key,
            model=os.environ.get("SMALLEST_TTS_MODEL", "lightning-v3.1"),
            voice_id=os.environ.get("SMALLEST_VOICE_ID", "sophia"),
        ),
        # Tuned to feel natural — bumped up from defaults so the agent doesn't
        # cut users off mid-sentence and false barge-ins are rare.
        min_endpointing_delay=0.8,
        max_endpointing_delay=4.0,
        min_interruption_duration=0.7,
        min_interruption_words=3,
        false_interruption_timeout=2.0,
        resume_false_interruption=True,
        discard_audio_if_uninterruptible=True,
        # preemptive_generation halves perceived latency but doubles LLM
        # token usage per turn. With Groq's on-demand 8k TPM cap, that
        # pushes every conversation into a 429. Disabled to keep us under
        # the cap; re-enable on a paid tier.
        preemptive_generation=False,
        # Strict cap: one tool call per user turn, then the LLM must
        # produce text before any further tool call. Prevents the model
        # chaining tools within one response turn.
        max_tool_steps=1,
        # Defense-in-depth against markdown / emoji / stage directions
        # the LLM occasionally emits. Custom regexes strip the worst
        # offenders we observed in real runs ("(Note awaiting user)",
        # "[email]", etc.).
        tts_text_transforms=[
            "filter_emoji",
            "filter_markdown",
            # Add text_transforms.replace({"YourBrand": "Your-Brand"}) here
            # if the TTS engine mispronounces a product or brand name.
            _strip_stage_directions,
        ],
    )

    # Per-turn metrics (LLM tokens, STT/TTS latency) and a session-end summary.
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent) -> None:
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def _log_session_usage(_reason: str) -> None:
        try:
            logger.info("session usage summary: %s", usage_collector.get_summary())
        except Exception as exc:  # pragma: no cover
            logger.warning("failed to log session usage: %s", exc)

    ctx.add_shutdown_callback(_log_session_usage)

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
                search_kb,
                check_availability,
                book_room,
                end_call,
            ],
        ),
        room_input_options=RoomInputOptions(delete_room_on_close=True),
    )

    # Soft keyboard-typing "thinking" sound to mask LLM generation latency.
    # Disabled in NovaSynth text mode so synthetic-run audio captures stay clean.
    if not is_text_mode:
        try:
            background_audio = BackgroundAudioPlayer(
                thinking_sound=[
                    AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.6),
                    AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.6),
                ],
            )
            await background_audio.start(room=ctx.room, agent_session=session)
        except Exception as exc:  # pragma: no cover
            logger.warning("background audio failed to start: %s", exc)

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
            "Greet the patron warmly as Sam from Westbrook Public Library. "
            "Identify yourself as an AI library assistant in the same "
            "sentence. Ask whether they would like to book a room or have "
            "a question. One sentence, then pause and listen."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            # Must match the AgentEndpoint name in NovaSynth (Noveum UI) so
            # synthetic dispatch runs hit this worker.
            agent_name="library-room-booking",
        )
    )
