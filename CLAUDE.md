# CLAUDE.md — instructions for Claude Code working in this repo

This file is read automatically by Claude Code when you open this repo. It
gives Claude the context it needs to help you customize the agent at the
workshop.

## What this repo is

A **LiveKit voice AI agent** scaffold. The user is at a 3-hour workshop
where they will:

1. Customize this agent into their own voice product (pizza bot, healthcare
   assistant, sales SDR, customer support, trivia host — whatever they bring)
2. Deploy it to LiveKit Cloud (`lk agent create` / `lk agent deploy`)
3. Stress-test it with synthetic users via Noveum NovaSynth
4. Read traces to debug latency / quality
5. Apply NovaPilot's AI-suggested fixes back through Claude Code

## The Noveum MCP — your primary integration surface

The Noveum MCP exposes the entire NovaSynth + traces + NovaPilot API as
tools. The user expects YOU (Claude Code) to drive setup, batch runs,
report fetching, and round-trip fixes — they shouldn't need to click
through the Noveum UI. The browser is *only* useful for visually
inspecting individual traces.

Tools you'll commonly call:

| MCP tool | What it does |
|---|---|
| `mcp__noveum__getApiV1Projects` | List projects; find/create the workshop project |
| `mcp__noveum__postApiV1NovasynthAgent-endpoints` | Register the deployed LiveKit agent |
| `mcp__noveum__postApiV1NovasynthPersonasGenerate` | AI-generate diverse personas |
| `mcp__noveum__postApiV1NovasynthScenariosGenerate` | AI-generate branching scenarios |
| `mcp__noveum__postApiV1NovasynthBatch-analysisByBatchRu...` | Trigger or rebuild batch analysis |
| `mcp__noveum__getApiV1NovasynthBatch-analysisByBatchRunId` | Poll batch progress |
| `mcp__noveum__getApiV1Traces` | Fetch traces (filter by `novasynth.run_id` etc.) |
| `mcp__noveum__getApiV1NovasynthRun-analysisByRunId` | NovaPilot report for a run |
| `mcp__noveum__postApiV1NovasynthRun-analysisByRunIdRebuild` | Force-regenerate the report |

When the user pastes PROMPT 4-6 from `PROMPT_CHEATSHEET.md`, you should
chain these MCP calls without asking the user to do anything in a browser.

If the MCP isn't connected, tell the user how to add it: their `NOVEUM_API_KEY`
in `.env` is the same key the MCP uses; the connection is configured per
Claude Code instance.

## Stack (already wired — DO NOT change unless asked)

- **LiveKit** for real-time voice (WebRTC orchestration)
- **Deepgram nova-2** for STT
- **Groq `openai/gpt-oss-120b`** for LLM
- **ElevenLabs eleven_turbo_v2_5** for TTS
- **Silero** for VAD
- **Noveum** (`noveum-trace`) for tracing — emits traces, supports NovaSynth
  correlation IDs in room metadata

## What the user customizes

| File | What to change |
|---|---|
| `agent.py` → `SYSTEM_PROMPT` | Rewrite for their agent's persona, job, tone |
| `agent.py` → `agent_name` in `WorkerOptions` | Match their NovaSynth endpoint |
| `agent.py` → `ELEVENLABS_VOICE_ID` env / `ElevenLabs voice_id` | Pick a voice that fits |
| `tools/` | Add tools their agent needs (replace/duplicate `example_tool.py`) |
| `knowledge_sources/*.md` | Domain knowledge their agent looks up |

## What stays as-is

- All the LiveKit / Groq / Deepgram / ElevenLabs plugin config
- VAD tuning (`min_silence_duration=0.6`, etc.)
- Endpointing thresholds (`min_endpointing_delay=0.8`, etc.)
- Interruption handling (`min_interruption_duration=0.7`, etc.)
- Noveum tracing setup (`setup_livekit_tracing`)
- NovaSynth correlation ID propagation (`_extract_novasynth_metadata`)

These are tuned for natural conversation. Don't regress them.

## Voice agent prompt-writing rules (CRITICAL)

When rewriting `SYSTEM_PROMPT`, ALWAYS include these sections:

1. **AI disclosure** — agent must identify as AI in turn 1 and on direct ask
2. **Voice output rules** — 1–2 sentences/turn, no markdown/lists/headings,
   numbers spoken as words ("twenty-five dollars", not "$25")
3. **One thought per turn** — pause and listen, never monologue
4. **When to call tools** — describe each tool's trigger conditions
5. **When to call `end_call`** — user goodbye, task complete, DNC, voicemail,
   call >4 min

Markdown, bullet lists, and code blocks DO NOT WORK in voice — TTS reads them
literally. The agent must produce conversational speech.

## Tool docstrings = LLM instructions

Every `@function_tool` decorated function's docstring is read by the LLM as
the tool's calling instructions. Write docstrings as if they're directives to
a junior engineer who only ever reads the docstring.

## Running the agent

```bash
python build_knowledge.py    # rebuild knowledge index (run after editing knowledge_sources/)
python agent.py dev          # local dev mode (connects to LiveKit Cloud)
```

Test via https://agents-playground.livekit.io.

## Deploying

```bash
lk cloud auth                # one-time
lk agent create              # interactive — uses agent.py + .env
lk agent logs <id> -f        # tail logs
```

## Re-deploying after changes

```bash
lk agent deploy              # rolls a new version on the existing agent
```

## When the user asks for a customization

1. Read the recipe they pick (or ask them what their agent does)
2. Rewrite `SYSTEM_PROMPT` following the rules above
3. Update tools if needed (drop a new file in `tools/`, register in `tools/__init__.py` and `agent.py`)
4. Update `knowledge_sources/` if their agent needs domain facts
5. Update `agent_name` in `WorkerOptions` if asked
6. Tell them to run `python build_knowledge.py` then `python agent.py dev`

## Common workshop questions

- **"My agent isn't responding"** → Check `python agent.py dev` is running and
  the LiveKit room is connected. Check the agent name in `lk agent list`.
- **"How do I see my traces?"** → https://noveum.ai → Traces → filter by
  `voice-workshop` project.
- **"NovaSynth runs aren't reaching my agent"** → Verify `agent_name` in
  `WorkerOptions` exactly matches the LiveKit AgentEndpoint in NovaSynth.
- **"Latency is too high"** → Open trace in Noveum, expand the span tree,
  find the slow span (usually LLM or TTS), tune that provider.

## Style

- Default to writing no comments; only add one when the WHY is non-obvious.
- Don't add error handling for scenarios that can't happen.
- Don't refactor beyond what was asked.
- Keep `SYSTEM_PROMPT` under 2,500 tokens — long prompts hurt latency.
