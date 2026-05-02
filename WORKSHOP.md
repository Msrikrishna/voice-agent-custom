# Workshop Runbook — Vibe-Code a Voice AI Agent

> Frontier Tower, 9th Floor Annex · Thu May 14, 2026 · 4:30–7:30 PM PT
>
> 🍕 Pizza and drinks provided · 🤝 50 builders · 💻 BYO laptop · free

This is the runbook we'll follow together. Each stage has a single goal, a
time-box, and one Claude Code prompt (from `PROMPT_CHEATSHEET.md`). Don't
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

## Stage 1 — Fork & Deploy (4:45–5:15)

**Goal:** Your generic starter agent is live on LiveKit Cloud as a registered worker.

```bash
python agent.py dev          # local — keep this running in one terminal
```

You should see `registered worker {agent_name: voice-workshop-agent, ...}`. The agent is now alive on LiveKit Cloud waiting for room dispatch.

Then in a second terminal, deploy a persistent copy:

```bash
lk cloud auth                # one-time browser OAuth (fast)
lk agent create              # interactive — picks up agent.py + .env
lk agent list                # confirm "voice-workshop-agent" registered
```

(Optional: place a call from agents-playground.livekit.io if you want to hear it. But for the rest of the workshop we'll dispatch synthetic calls via the Noveum MCP — no browser needed.)

✅ **Checkpoint:** `lk agent list` shows your agent. Worker logs show it's connected to LiveKit Cloud.

---

## Stage 2 — Customize with Claude (5:15–5:45)

**Goal:** Your agent is now YOUR product (pizza bot, healthcare triage,
trivia host, customer support — whatever you brought).

1. Decide what your agent does. If stuck, pick a recipe from `recipes/`.
2. Open Claude Code in this repo: `claude`
3. Paste **PROMPT 2** from `PROMPT_CHEATSHEET.md` with your idea filled in
4. Claude rewrites `SYSTEM_PROMPT`, adds tools, generates knowledge files
5. Rebuild + reload locally: `python build_knowledge.py && python agent.py dev`
6. Re-deploy to LiveKit Cloud: `lk agent deploy`

✅ **Checkpoint:** Your local + deployed agent both register with the new persona.

---

## Stage 3 — Stress-Test via Noveum MCP (5:45–6:30)

**Goal:** 10 synthetic callers placed against your deployed agent — zero clicks, all from Claude Code.

The Noveum MCP exposes the entire NovaSynth API as tools Claude Code can call directly:
- `postApiV1NovasynthAgent-endpoints` — register your LiveKit agent
- `postApiV1NovasynthPersonasGenerate` — AI-generate diverse personas
- `postApiV1NovasynthScenariosGenerate` — AI-generate scenarios
- `postApiV1NovasynthBatch-analysis...` — kick off the batch run
- `getApiV1NovasynthRun-analysisByRunId` — read results

1. Make sure the Noveum MCP is connected in Claude Code (it's set up by default if `NOVEUM_API_KEY` is in your env)
2. Paste **PROMPT 4** from `PROMPT_CHEATSHEET.md` into Claude Code — it tells Claude to:
   - Register `voice-workshop-agent` as a NovaSynth Agent Endpoint
   - Generate 5 personas + 5 scenarios for your specific use case
   - Create a 10-pair batch run
   - Trigger it
3. Claude Code drives all of the above through MCP tool calls. You watch.
4. Run **PROMPT 5** to poll status and tail the active run

**Why explicit pairs:** each persona's background only fits some scenarios. 10 thoughtful pairs > 25 noisy ones for signal quality.

✅ **Checkpoint:** Claude Code reports "batch run started, ID: bxr_..." and you can see calls completing one by one.

---

## Stage 4 — Debug Traces (6:30–7:00)

**Goal:** Find your agent's actual latency budget and quality failures.

Two ways to read traces — pick whichever fits your style:

**Option A — via MCP (terminal):** Paste **PROMPT 6** to Claude Code. It calls `getApiV1Traces` filtered by `novasynth.run_id`, summarizes the per-span latency budget (STT vs LLM vs TTS), and flags the slowest spans across the run. Faster for batch summaries.

**Option B — via browser:** Open https://noveum.ai → Traces → filter by `voice-workshop` project. The three-pane view is genuinely better for inspecting a single trace visually (timeline, audio playback, full I/O at each step).

For workshop purposes: do A first to find the worst trace, then B to inspect it.

✅ **Checkpoint:** You can name (a) your worst latency span and (b) one quality failure your agent made.

---

## Stage 5 — Fix with NovaPilot + Claude (7:00–7:20)

**Goal:** Ship a fix and re-run the batch — round-trip, terminal-only.

Paste **PROMPT 7** to Claude Code. It does the full loop:

1. Calls `postApiV1NovasynthRun-analysisByRunIdRebuild` (or polls `getApiV1NovasynthRun-analysisByRunId`) to fetch the NovaPilot report
2. Reads the failure-pattern recommendations
3. Updates `SYSTEM_PROMPT` (or tools) in `agent.py` to address them
4. Tells you the diff before applying
5. After you approve, runs `lk agent deploy`
6. Triggers a fresh batch run via `postApiV1NovasynthBatch-analysis...`
7. Polls until done, summarizes before/after scores

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

- **Claude Code prompts** → `PROMPT_CHEATSHEET.md`
- **Recipe ideas** → `recipes/*.md`
- **Stuck?** → ask out loud, or DM #voice-workshop on the Frontier Discord

## Post-workshop

- Repo is yours — fork, ship, sell
- Free Noveum tier covers ~50k traces/mo + 1k eval credits/mo
- Office hours every Wednesday 5–6 PM PT on Discord
