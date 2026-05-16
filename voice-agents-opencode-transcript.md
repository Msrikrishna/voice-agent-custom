# Repo overview and architecture

**Session ID:** ses_1d6f0f3f0ffem3p1EEzq55DlgP
**Created:** 5/14/2026, 5:35:12 PM
**Updated:** 5/14/2026, 5:38:37 PM

---

## User

what is in the repo and how does everything connect? 

---

## Assistant (Build · DeepSeek V4 Pro · 182.9s)





**Tool: task**

**Input:**
```json
{
  "description": "Explore repo structure",
  "prompt": "Explore this repo thoroughly. I need to understand:\n1. The overall directory structure (list top-level and key subdirectories)\n2. What `agent.py` does — read it fully\n3. What's in `tools/` and `knowledge_sources/`\n4. What `build_knowledge.py` does\n5. What's in `.env` (redact secrets), `requirements.txt`, `CLAUDE.md`\n6. Any other important files (configs, deployment files, etc.)\n\nReturn a comprehensive summary of the repo's architecture: what each file does, how they connect, and what the overall workflow is.",
  "subagent_type": "explore"
}
```

**Output:**
```
task_id: ses_1d6f00f3bffeGU2aI1GSRGLOz3 (for resuming to continue this task if needed)

<task_result>
I now have a complete picture. Here is a comprehensive summary of the repository:

---

## Repository Architecture Summary

### 1. Overall Directory Structure

```
voice-agent-workshop-starter/
├── .claude/
│   └── settings.json          # Claude Code permissions/safety allowlist
├── .dockerignore
├── .env                        # ACTUAL secrets (LiveKit, Groq, Smallest.ai, Noveum keys)
├── .env.example                # Template for new users — same structure, empty values
├── .gitignore
├── .venv/                      # Python virtual environment (gitignored)
├── agent.py                    # ★ MAIN ENTRY POINT — the voice agent
├── build_knowledge.py          # ★ Knowledge index builder (RAG preprocessor)
├── CLAUDE.md                   # ★ AI instruction file for Cursor/Claude Code
├── Dockerfile                  # Container build for LiveKit Cloud deployment
├── knowledge/                  # Built output of build_knowledge.py (gitignored)
│   ├── index.json              # JSON index of knowledge pages {id, title, summary, body}
│   └── menu.md                 # Copied from knowledge_sources/
├── knowledge_sources/          # Editable domain knowledge (Markdown)
│   └── menu.md                 # Sunrise Café menu (starter content)
├── livekit.toml                # LiveKit CLI project config (subdomain + agent ID)
├── poster.svg                  # Workshop poster graphic
├── PROMPT_CHEATSHEET.md        # 7 numbered prompts to paste into Cursor/Claude Code
├── README.md                   # Setup instructions (6 steps)
├── recipes/                    # Idea templates for agent personas
│   ├── customer-support.md
│   ├── healthcare-triage.md
│   ├── pizza-bot.md
│   └── trivia-host.md
├── requirements.txt            # Python dependencies (8 packages)
├── tools/                      # Agent tool implementations
│   ├── __init__.py             # Tool registry (exports end_call, place_order)
│   ├── end_call.py             # Graceful call termination with goodbye validation
│   └── place_order.py          # Stub order-placing tool
├── verify_setup.py             # Pre-workshop setup verification script
└── WORKSHOP.md                 # Stage-by-stage 3-hour workshop runbook
```

---

### 2. `agent.py` — The Core Voice Agent (429 lines)

**Purpose:** The complete LiveKit voice agent. It orchestrates real-time voice conversation using a free-tier stack and is the single file workshop participants customize.

**Key sections:**

- **Lines 1-25 (docstring):** Explains the stack (Groq LLM, Smallest.ai STT/TTS, Silero VAD, Noveum tracing). Guides users to change only `SYSTEM_PROMPT`.

- **Lines 27-56 (imports):** Imports the LiveKit Agents framework, the three plugins (groq, silero, smallestai), Noveum tracing, and the two tools from `tools/`. Uses `python-dotenv` to load `.env`.

- **Lines 64-113 (logging setup):** Silences noise from LiveKit Cloud's free-tier recording 401 errors and OpenTelemetry warnings. Sets Noveum trace log level from env var. Handles `SMALLEST_AI_API_KEY` alias.

- **Lines 117-161 (`SYSTEM_PROMPT`):** The LLM's persona and instructions. Starter content is "Alex from Sunrise Café" — a café order-taking agent. Includes strict voice output rules (one sentence per turn, no markdown, numbers as words), AI disclosure mandate, tool-calling guidance, and a hardcoded menu of drinks and food with prices.

- **Lines 164-184 (`_strip_stage_directions`):** A TTS text transform that removes parentheticals like "(Note awaiting user)" and bracketed content before they reach TTS, preventing the engine from reading them literally.

- **Lines 187-193 (`prewarm`):** Loads Silero VAD once per worker process with tuned thresholds (`min_silence_duration=0.6`, `min_speech_duration=0.1`, `activation_threshold=0.5`) to reduce false barge-ins.

- **Lines 196-230 (NovaSynth metadata extraction):** `_parse_room_metadata` reads JSON from LiveKit room metadata. `_extract_novasynth_metadata` pulls out correlation IDs (`novasynth_run_id`, `novasynth_batch_run_id`, `novasynth_persona_id`, `novasynth_scenario_id`, `novasynth_project_id`) for trace correlation.

- **Lines 233-418 (`entrypoint`):** The main session handler:
  1. Connects to LiveKit, parses room metadata, detects NovaSynth text mode
  2. Initializes Noveum tracing if API key is present
  3. Configures `AgentSession` with:
     - **STT:** Smallest.ai Waves Pulse (language configurable via `SMALLEST_STT_LANGUAGE`)
     - **LLM:** Groq `openai/gpt-oss-120b` with `max_completion_tokens=80` (enforces one-sentence rule)
     - **TTS:** Smallest.ai Waves Lightning v3.1 (voice configurable via `SMALLEST_VOICE_ID`)
     - Tuned endpointing (`min_endpointing_delay=0.8`, `max_endpointing_delay=4.0`)
     - Tuned interruption handling (`min_interruption_duration=0.7`, `min_interruption_words=3`)
     - `preemptive_generation=False` (disabled to avoid Groq 429s on free tier)
     - `max_tool_steps=1` (one tool call per turn)
     - TTS text transforms: emoji filter, markdown filter, stage-direction stripper
  4. Sets up metrics collection and session-usage logging
  5. Wires Noveum tracing via `setup_livekit_tracing`
  6. Starts the session with `Agent(instructions=SYSTEM_PROMPT, tools=[place_order, end_call])`
  7. Plays keyboard-typing background audio during LLM generation (except in NovaSynth text mode)
  8. Propagates NovaSynth correlation IDs onto the trace
  9. Sends an opening greeting with AI disclosure via `session.generate_reply`

- **Lines 420-429 (CLI entry):** Uses `agents.cli.run_app` with `WorkerOptions`, registering the agent as `agent_name="workshop-starter-agent"`.

---

### 3. `tools/` — Agent Tool Implementations

| File | Purpose |
|------|---------|
| `__init__.py` | Exports `end_call` and `place_order` from their modules. This is the central registry — any new tool must be added here AND in `agent.py`'s `tools=[]` list. |
| `end_call.py` (140 lines) | The universal call-end tool. Includes a **programmatic validator** that checks the user's most recent message against 23 goodbye/DNC regex patterns. **Refuses** if the user didn't actually say goodbye (prevents LLM hallucination of "voicemail detected"). Implements a 1.5s delayed shutdown to let goodbye TTS finish. Background tasks are held in a strong-ref set to prevent GC. |
| `place_order.py` (29 lines) | A stubbed order-placing tool. Logs the order and returns a confirmation string. The docstring instructs the LLM to only call it after explicit user confirmation. |

The docstring pattern is critical: each `@function_tool`'s docstring serves as the LLM's calling instructions — they read like directives to a junior engineer.

---

### 4. `knowledge_sources/` — Domain Knowledge (Input)

| File | Content |
|------|---------|
| `menu.md` | Sunrise Café menu: 8 drinks ($3.50-$5.50), 6 food items ($3.50-$13.00), notes on milk alternatives, gluten-free options, and 10-15 minute order time |

These are Markdown files edited by participants. After editing, they run `python build_knowledge.py` to rebuild the index.

---

### 5. `build_knowledge.py` — Knowledge Index Builder (68 lines)

**Purpose:** A stripped-down RAG preprocessing pipeline. Reads all `.md` files from `knowledge_sources/` and produces output in `knowledge/` (which is gitignored).

**How it works:**
1. Clears the `knowledge/` output directory
2. Iterates sorted `*.md` files from `knowledge_sources/`
3. For each file: extracts the first heading as the title, derives a slug from the filename, generates a 240-char summary (first non-heading paragraph), copies the raw body
4. Writes two artifacts per page: a `{slug}.md` file and a single `index.json` containing `[{id, title, summary, body}]`

**Output:** `knowledge/index.json` + `knowledge/{slug}.md` for each source file.

---

### 6. `.env` — Environment Configuration

**Structure:** 4 service blocks:
- **LiveKit Cloud:** `LIVEKIT_URL` (wss://), `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- **Groq:** `GROQ_API_KEY`, optional `GROQ_MODEL` (default `openai/gpt-oss-120b`), `GROQ_TEMPERATURE` (0.4)
- **Smallest.ai:** `SMALLEST_API_KEY` (covers both STT and TTS), optional `SMALLEST_TTS_MODEL` (`lightning-v3.1`), `SMALLEST_VOICE_ID` (`sophia`), `SMALLEST_STT_LANGUAGE` (`en`)
- **Noveum:** `NOVEUM_API_KEY`, `NOVEUM_PROJECT` (`voice-workshop`), `NOVEUM_ENV` (`workshop`)

Actual keys are present. The `.env.example` mirrors this structure with empty values.

---

### 7. `requirements.txt` — Dependencies (8 packages)

| Package | Version | Role |
|---------|---------|------|
| `livekit-agents` | 1.5.8 | Core voice agent framework |
| `livekit-plugins-silero` | 1.5.8 | Silero VAD plugin |
| `livekit-plugins-groq` | 1.5.8 | Groq LLM plugin |
| `livekit-plugins-smallestai` | 1.5.8 | Smallest.ai STT+TTS plugin |
| `noveum-trace[livekit]` | 1.5.13 | Noveum tracing SDK with LiveKit integration |
| `aiohttp` | 3.13.5 | Async HTTP client |
| `python-dotenv` | 1.2.2 | `.env` file loader |
| `requests` | 2.34.0 | Sync HTTP client (verify_setup.py) |

---

### 8. `CLAUDE.md` — AI Instruction File

This is read automatically by Cursor and Claude Code. It gives the AI:
- **What the repo is:** A LiveKit voice AI agent scaffold for a 3-hour workshop
- **The Noveum MCP tool catalog:** 16 tool functions listed in a table with their purposes
- **Stack details:** What to change vs. what must stay as-is (VAD tuning, endpointing, interruption thresholds, tracing setup)
- **Voice agent prompt-writing rules:** 5 mandatory sections for SYSTEM_PROMPT rewrites
- **Tool docstring convention:** Write them as LLM calling instructions
- **Commands:** How to run locally, deploy, redeploy
- **Troubleshooting:** Common workshop questions answered
- **Style guidelines:** No unnecessary comments, no over-refactoring, keep SYSTEM_PROMPT under 2,500 tokens

---

### 9. Other Important Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build (Python 3.12 slim). Installs deps in a venv, copies the app, runs `agent.py download-files` during build. Final stage runs as non-root `appuser`. CMD: `python agent.py start`. |
| `livekit.toml` | LiveKit CLI config. Empty by default — filled after `lk agent create` with project subdomain and agent ID. |
| `verify_setup.py` | Pre-workshop checker. Validates: Python version >=3.10, all 6 env vars present (no placeholders), live API pings to Groq/Smallest.ai/Noveum, LiveKit CLI availability. Returns exit code 1 on any failure. |
| `PROMPT_CHEATSHEET.md` | 7 numbered prompts for the workshop workflow, plus 2 bonus prompts. These are pasted verbatim into Cursor/Claude Code. |
| `WORKSHOP.md` | Stage-by-stage 3-hour runbook: Stage 0 (pre-flight), Stage 1 (deploy), Stage 2 (customize), Stage 3 (NovaSynth stress test via MCP), Stage 4 (debug traces), Stage 5 (NovaPilot fix loop), Stage 6 (demos). |
| `recipes/` | 4 idea templates: customer support, healthcare triage, pizza bot, trivia host. Each includes a ready-to-paste PROMPT 2 variant, suggested tools, knowledge files, voice IDs, and NovaSynth persona ideas. |
| `.claude/settings.json` | Claude Code permission allowlist — whitelists specific bash commands (pip, python, curl) and web fetches to pypi.org, smallest.ai, docs.livekit.io. Also allows `/tmp` directory access. |

---

### 10. Overall Workflow — How Everything Connects

```
┌───────────────────────────────────────────────────────────────┐
│                     WORKSHOP FLOW                             │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  1. SETUP: Clone repo → pip install → copy .env.example       │
│     to .env → fill in 4 API keys (LiveKit/Groq/Smallest.ai/   │
│     Noveum) → python verify_setup.py (all green)             │
│                                                               │
│  2. RUN LOCALLY: python build_knowledge.py (reads              │
│     knowledge_sources/*.md → writes knowledge/index.json)     │
│     → python agent.py dev (starts LiveKit worker, connects    │
│     to LiveKit Cloud) → test via agents-playground.livekit.io │
│                                                               │
│  3. CUSTOMIZE WITH CURSOR: Paste PROMPT 2 from                │
│     PROMPT_CHEATSHEET.md → Cursor/Claude reads CLAUDE.md,    │
│     agent.py, tools/, knowledge_sources/ → rewrites:          │
│       - SYSTEM_PROMPT in agent.py                             │
│       - Tools in tools/ + register in __init__.py + agent.py  │
│       - Knowledge in knowledge_sources/*.md                   │
│       - agent_name in WorkerOptions                           │
│                                                               │
│  4. DEPLOY: python build_knowledge.py → lk agent create       │
│     or lk agent deploy → agent live on LiveKit Cloud          │
│                                                               │
│  5. STRESS TEST (NovaSynth via MCP): Paste PROMPT 4 → Cursor  │
│     calls Noveum MCP tools to:                                │
│       - Upsert agent config + register endpoint               │
│       - Generate personas + scenarios                         │
│       - Run single smoke test → PROMPT 5 for full batch       │
│                                                               │
│  6. DEBUG: PROMPT 6 → fetch traces via MCP, find worst runs,  │
│     inspect in Noveum browser UI                              │
│                                                               │
│  7. FIX + RE-RUN: PROMPT 7 → NovaPilot analysis → Cursor      │
│     applies fixes → lk agent deploy → re-run batch → compare  │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                     DATA FLOW AT RUNTIME                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Caller (voice)                                               │
│      │                                                        │
│      ▼                                                        │
│  LiveKit Cloud (WebRTC orchestration)                         │
│      │                                                        │
│      ▼                                                        │
│  agent.py entrypoint()                                        │
│      │                                                        │
│      ├──► Room metadata parsed for NovaSynth correlation IDs  │
│      │                                                        │
│      ├──► Silero VAD (voice activity detection)               │
│      │    prewarmed per worker, tuned thresholds              │
│      │                                                        │
│      ├──► Smallest.ai Waves Pulse (STT)                       │
│      │    Speech → text                                       │
│      │                                                        │
│      ├──► Groq openai/gpt-oss-120b (LLM)                      │
│      │    Text → response + potential tool calls              │
│      │    Guided by SYSTEM_PROMPT                             │
│      │    May call: place_order(), end_call()                 │
│      │    Hard capped at 80 output tokens                     │
│      │                                                        │
│      ├──► Smallest.ai Waves Lightning v3.1 (TTS)              │
│      │    Text → speech (with text transforms applied)        │
│      │                                                        │
│      └──► Noveum tracing (noveum-trace)                       │
│           Every span recorded: STT latency, LLM latency,      │
│           TTS latency, tool calls. Enriched with NovaSynth     │
│           correlation IDs for batch-run filtering.             │
│                                                               │
│  Caller hears agent's spoken response                         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Key architectural decisions visible in the code:**
- **`max_completion_tokens=80`** — enforces the one-sentence-per-turn rule at the LLM level
- **`max_tool_steps=1`** — prevents tool chaining within a single turn
- **`preemptive_generation=False`** — intentionally disabled to keep Groq free-tier within 8k TPM ratelimit
- **`end_call` has a programmatic validator** — inspects user's actual last message against regex patterns rather than trusting the LLM's `reason` argument (defense against hallucinated "voicemail detected" triggers)
- **`_strip_stage_directions` TTS transform** — cleans parentheticals and bracketed text before TTS to prevent literal reading
- **NovaSynth metadata extraction** — pulls correlation IDs from room metadata at session start and propagates them onto traces, enabling batch-run filtering in the Noveum dashboard
- **The entire workshop is designed to be driven from Cursor/Claude Code** via the Noveum MCP — no browser UI clicks needed for configuration, testing, or analysis
</task_result>
```

---

## Assistant (Build · DeepSeek V4 Pro · 21.8s)

Here's an overview of the repo and how everything connects:

---

## What's in this repo

A **LiveKit voice AI agent scaffold** for a 3-hour workshop — a café order-taking bot (Sunrise Café) by default, built to be customized into any voice agent (pizza bot, healthcare triage, trivia host, etc.).

---

## Directory structure

```
voice-agent-workshop-starter/
├── agent.py                  ★ Main entry — the complete voice agent
├── build_knowledge.py        ★ RAG preprocessor (markdown → knowledge index)
├── tools/                    Agent tool implementations
│   ├── __init__.py            Tool registry
│   ├── end_call.py            Graceful call termination (with goodbye validator)
│   └── place_order.py         Stub order-placing tool
├── knowledge_sources/         Editable domain knowledge (input)
│   └── menu.md                Sunrise Café menu
├── knowledge/                 Built index (output, gitignored)
├── recipes/                   Idea templates (customer-support, pizza-bot, etc.)
├── CLAUDE.md                  AI instruction file for Cursor/Claude Code
├── PROMPT_CHEATSHEET.md       7 numbered prompts for workshop workflow
├── WORKSHOP.md                Stage-by-stage workshop runbook
├── Dockerfile                 Container build for LiveKit Cloud deployment
├── livekit.toml               LiveKit CLI project config
├── requirements.txt           8 Python dependencies
├── verify_setup.py            Pre-workshop setup validation
└── .env.example              Template for API keys
```

---

## How everything connects at runtime

```
Caller (voice/synthetic user)
    │
    ▼
LiveKit Cloud (WebRTC orchestration)
    │
    ▼
agent.py entrypoint()
    │
    ├─ Silero VAD (voice activity detection, tuned thresholds)
    ├─ Smallest.ai Waves Pulse (STT: speech → text)
    ├─ Groq gpt-oss-120b (LLM: text → response, guided by SYSTEM_PROMPT)
    │     └─ may call: place_order() or end_call() from tools/
    ├─ Smallest.ai Waves Lightning v3.1 (TTS: text → speech)
    └─ Noveum tracing (every span recorded, enriched with correlation IDs)
```

## What to customize

| Change | File |
|--------|------|
| Agent persona, tone, rules | `agent.py` → `SYSTEM_PROMPT` |
| Tools the agent can use | `tools/` + register in `__init__.py` + `agent.py` |
| Domain knowledge | `knowledge_sources/*.md` |
| Agent name for deployment | `agent.py` → `agent_name` in `WorkerOptions` |
| Voice | `SMALLEST_VOICE_ID` in `.env` |

The free-tier stack (Groq + Smallest.ai + Silero) and all tuned thresholds stay as-is — they're already optimized for natural conversation. CLAUDE.md enforces strict prompt-writing rules (AI disclosure, one sentence per turn, no markdown, tool-calling guidelines, end_call conditions).

---

