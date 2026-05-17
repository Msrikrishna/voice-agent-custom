# Voice Agent — Local Dev

A LiveKit voice agent (Smallest.ai STT + TTS, Groq LLM) with a local
browser-based dev console. No need to use the LiveKit playground —
talk to your agent at `http://127.0.0.1:8080`, swap persona / voice /
model / temperature per session from dropdowns.

## 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in keys
```

Required `.env` keys: `LIVEKIT_URL`, `LIVEKIT_API_KEY`,
`LIVEKIT_API_SECRET`, `GROQ_API_KEY`, `SMALLEST_API_KEY`,
`NOVEUM_API_KEY`.

Sanity check:

```bash
python verify_setup.py
```

Build the knowledge index from `knowledge_sources/`:

```bash
python build_knowledge.py
```

## 2. Run locally — two terminals

**Terminal A — agent worker (connects to LiveKit Cloud):**

```bash
python agent.py dev
```

Wait for `registered worker {agent_name: tonys-pizza-agent, ...}`.

**Terminal B — local dev UI:**

```bash
python dev_ui/server.py
```

Then open **http://127.0.0.1:8080** in your browser.

## 3. Using the dev UI

1. Pick a **preset** (Tony's Pizza, Library Booking, Tech Support,
   Sales SDR, or Custom). Greeting + system prompt autofill.
2. Pick **voice**, **LLM model**, **temperature**. Edit the system
   prompt or greeting freely.
3. Click **Connect**. The UI:
   - Mints a LiveKit token
   - Creates a fresh room with your settings as room metadata
   - Dispatches the `tonys-pizza-agent` worker into it
4. Speak. Transcripts stream into the chat pane.
5. **Mute** toggles your local mic. **Disconnect** ends the session.
6. **Reconnect** with different settings → brand-new room, agent
   uses the new persona/voice/model — no worker restart.

## How the persona override works

`dev_ui/server.py` JSON-encodes `{system_prompt, greeting, voice_id,
groq_model, groq_temperature}` into the LiveKit room metadata.
`agent.py` reads those keys in `entrypoint()` and overrides
`SYSTEM_PROMPT`, the opening greeting, the TTS voice, and the Groq
model/temperature. Missing keys fall back to the env or hardcoded
defaults, so NovaSynth and the official playground keep working.

## Files

- `agent.py` — LiveKit worker. Reads persona overrides from
  `room.metadata`.
- `dev_ui/server.py` — aiohttp on `:8080`. Serves the page; mints
  tokens; creates room + dispatches the agent.
- `dev_ui/static/{index.html, app.js, styles.css}` — the chat UI.
- `tools/` — agent function tools (`place_order`, `end_call`).
- `knowledge_sources/` — markdown the agent looks up (rebuild with
  `python build_knowledge.py`).
