# Voice AI Agent Workshop Starter

> A working LiveKit voice agent on **Groq + Deepgram + ElevenLabs**, pre-wired with **Noveum** tracing, ready to be reshaped into your product with **Claude Code** in 3 hours.

This is the starter repo for the **Vibe-Code a Voice AI Agent** workshop at Frontier Tower (May 7, 2026, 4:30–7:30 PM PT).

## What you get

- A complete LiveKit agent (`agent.py`) with sub-500ms turn latency
- Pre-wired Noveum tracing (debug latency + quality from minute one)
- A clean tools framework (`tools/`) ready to extend
- A simple knowledge base loader (`build_knowledge.py` + `knowledge_sources/`)
- 4 example "customization recipes" in `recipes/` you can hand to Claude Code
- A `verify_setup.py` script that pings every API to confirm your keys work
- `CLAUDE.md` so your Claude Code instance knows what this repo is

## Quick start (BEFORE the workshop)

```bash
git clone <this-repo-url> voice-agent-workshop-starter
cd voice-agent-workshop-starter

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your keys

python verify_setup.py
# green checks = you're ready
```

## Required API keys (all free tiers — $0 total)

| Service | Sign up | Used for |
|---------|---------|----------|
| [Anthropic](https://console.anthropic.com) | Claude Code |
| [LiveKit Cloud](https://cloud.livekit.io) | Real-time voice infra + free deploys |
| [Deepgram](https://console.deepgram.com) | Streaming STT |
| [Groq](https://console.groq.com) | Sub-200ms LLM inference |
| [ElevenLabs](https://elevenlabs.io) | Natural low-latency TTS |
| [Noveum](https://noveum.ai) | Tracing + synthetic users + AI debugging |

## Running locally

```bash
python build_knowledge.py
python agent.py dev
```

Open https://agents-playground.livekit.io, paste your LiveKit credentials, place a call.

## Deploying to LiveKit Cloud

```bash
brew install livekit-cli
lk cloud auth
lk agent create
lk agent logs <agent-id> -f
```

## Workshop runbook

- `WORKSHOP.md` — the 6 stages we go through together
- `PROMPT_CHEATSHEET.md` — exact Claude Code prompts at each stage
- `recipes/` — example product ideas you can fork instantly

## Stack

```
Caller ─► LiveKit ─► Deepgram (STT) ─► Groq gpt-oss-120b (LLM) ─► ElevenLabs (TTS) ─► Caller
                                            │
                                            └─► Noveum (traces, NovaSynth, NovaPilot)
```

## License

MIT — fork it, ship it, sell it.
