# Workshop Runbook — Vibe-Code a Voice AI Agent

> Frontier Tower, 10th Floor Annex · Thu May 14, 2026 · 4:30–7:30 PM PT
>
> 🍕 Pizza and drinks provided · 🤝 50 builders · 💻 BYO laptop · free

This is the runbook we'll follow together. Each stage has a single goal, a
time-box, and one Cursor prompt (from `PROMPT_CHEATSHEET.md`). Don't
get stuck on any stage — if something breaks, raise your hand, we'll move on
together.

---

## Stage 0 — Pre-flight (4:30–4:45) 🍕

**Goal:** Everyone has the starter cloned, `verify_setup.py` passes, agent runs
locally. Pizza is hot, drinks are open — grab a slice and let's go.

1. Welcome + intros (60 sec each)
2. The voice AI failure mode story (5 min)
3. Confirm: `python verify_setup.py` shows green checks for everyone
4. Quick demo of the unmodified starter agent in
   https://agents-playground.livekit.io

---

## Stage 1 — Deploy the starter agent (4:45–5:15)

**Goal:** Your generic starter agent is live on LiveKit Cloud as a registered worker.

```bash
python agent.py dev          # local — keep this running in one terminal
```

You should see `registered worker {agent_name: workshop-starter-agent, ...}`. The agent is now alive on LiveKit Cloud waiting for room dispatch.

Then in a second terminal, deploy a persistent copy:

```bash
lk cloud auth                # one-time browser OAuth (if not done already)
lk agent create              # interactive — picks up agent.py + .env
lk agent list                # confirm "workshop-starter-agent" registered
```

(Optional: place a call from the LiveKit console or agents-playground.livekit.io to hear the unmodified starter agent.)

✅ **Checkpoint:** `lk agent list` shows your agent. Worker logs show it's connected to LiveKit Cloud.

> 💡 **One-time gotcha if you ever change a key in `.env` later:** `lk agent deploy` redeploys the **code** but does **not** push new secrets. If you rotate an API key or add a new env var, update it in https://cloud.livekit.io → your agent → Secrets, or re-run `lk agent create` against a fresh slug. First-time setup via `lk agent create` (above) handles all secrets correctly.

---

## Stage 2 — Customize with Cursor (5:15–5:45)

**Goal:** Your agent is now YOUR product (pizza bot, healthcare triage,
trivia host, customer support — whatever you brought).

1. Decide what your agent does. If stuck, pick a recipe from `recipes/`.
2. Open Cursor in this repo's folder (`cursor .`) or Claude Code (`claude`)
3. Paste **PROMPT 1** — quick sanity check that the AI can read the repo
4. Paste **PROMPT 2** with your idea filled in
5. Cursor rewrites `SYSTEM_PROMPT`, replaces tools, updates knowledge files
6. Paste **PROMPT 3** — pre-deploy audit + rebuild + first deploy of your
   customised agent (`python build_knowledge.py` → `lk agent create` for
   a new agent name, or `lk agent deploy` if name is unchanged)

✅ **Checkpoint:** Your deployed agent registers with the new persona. Make a test call via the LiveKit console to confirm it sounds right.

---

## Stage 3 — Stress-Test via Noveum MCP (5:45–6:30)

**Goal:** 10 synthetic callers placed against your deployed agent — zero clicks, all from Cursor.

The Noveum MCP exposes the entire NovaSynth API as tools Cursor can call directly. Key tools used in this stage:

- `putApiV1NovasynthAgent-config` — upsert your agent's system prompt + metadata (triggers eval auto-setup)
- `postApiV1NovasynthAgent-endpoints` — register your LiveKit agent as a callable endpoint
- `postApiV1NovasynthPersonasGenerate` / `postApiV1NovasynthScenariosGenerate` — AI-generate callers + situations
- `postApiV1NovasynthRuns` — single smoke-test run before the full batch
- `postApiV1NovasynthBatch-runs` — launch all 10 runs with controlled concurrency
- `getApiV1NovasynthBatch-runsById` — poll batch progress

1. Make sure the Noveum MCP is connected in Cursor (see README Step 3 if you haven't done it yet)
2. Paste **PROMPT 4** from `PROMPT_CHEATSHEET.md` into Cursor — it will:
   - Read `agent_name`, `SYSTEM_PROMPT`, and keys directly from the repo files
   - Upsert your agent config in Noveum (triggers eval/dataset setup)
   - Register (or reuse) your LiveKit endpoint
   - Generate 5 diverse personas + 5 scenarios for your use case
   - Run a **single smoke-test call** — then stop and report pass/fail
3. If the smoke test passes, paste **PROMPT 5** to launch the full 10-pair batch
4. Paste **PROMPT 6** to poll status and get a trace summary once done

**Why explicit pairs:** each persona's background only fits some scenarios. 10 thoughtful pairs > 25 noisy ones for signal quality.

✅ **Checkpoint:** Smoke test (PROMPT 4) passes. Cursor reports "batch run started, ID: ..." (PROMPT 5) and you can see calls completing one by one.

---

## Stage 4 — Debug Traces (6:30–7:00)

**Goal:** Find your agent's actual latency budget and quality failures.

Two ways to read traces — pick whichever fits your style:

**Option A — via MCP (terminal):** Paste **PROMPT 6** to Cursor. It polls the batch, fetches all traces, summarizes the per-span latency budget (STT vs LLM vs TTS), and flags the worst calls.

**Option B — via browser:** Open https://noveum.ai → Traces → filter by `voice-workshop` project. The three-pane view is genuinely better for inspecting a single trace visually (timeline, audio playback, full I/O at each step).

For workshop purposes: do A first to find the worst trace, then B to inspect it.

✅ **Checkpoint:** You can name (a) your worst latency span and (b) one quality failure your agent made.

---

## Stage 5 — Fix with NovaPilot + Cursor (7:00–7:20)

**Goal:** Ship a fix and re-run the batch — round-trip, terminal-only.

Paste **PROMPT 7** to Cursor. It does the full loop:

1. Calls `getApiV1NovasynthBatch-analysisByBatchRunId` to fetch (or `postApiV1NovasynthBatch-analysisByBatchRunIdRebuild` to rebuild) the batch NovaPilot analysis report
2. Reads the failure-pattern recommendations
3. Updates `SYSTEM_PROMPT` (or tools) in `agent.py` to address them
4. Tells you the diff before applying
5. After you approve, runs `lk agent deploy`
6. Triggers a fresh batch run via `postApiV1NovasynthBatch-runs` using the same pairs
7. Polls until done, summarizes before/after scores per scorer

✅ **Checkpoint:** Second batch shows score improvement on the metric you targeted.

---

## Stage 6 — Demos + Q&A (7:20–7:30) 🍕🍻

**Goal:** Show off your agent. 30 seconds each. More pizza, drinks, networking.

1. 3 attendees demo their agents live
2. Q&A
3. Keep building — your free Noveum tier covers continuous experimentation
4. Stick around for 1:1 debugging if you want — we'll be there till they kick us out

---

## Cheatsheet locations

- **Cursor prompts** → `PROMPT_CHEATSHEET.md`
- **Recipe ideas** → `recipes/*.md`
- **Stuck?** → ask out loud, or DM #voice-workshop on the Frontier Discord

## Post-workshop

- Repo is yours — fork, ship, sell
- Free Noveum tier covers ~50k traces/mo + 1k eval credits/mo
- Office hours every Wednesday 5–6 PM PT on Discord
