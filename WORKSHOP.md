# Workshop Runbook — Vibe-Code a Voice AI Agent

> Frontier Tower, 9th Floor Annex · May 7, 2026 · 4:30–7:30 PM PT

This is the runbook we'll follow together. Each stage has a single goal, a
time-box, and one Claude Code prompt (from `PROMPT_CHEATSHEET.md`). Don't
get stuck on any stage — if something breaks, raise your hand, we'll move on
together.

---

## Stage 0 — Pre-flight (4:30–4:45)

**Goal:** Everyone has the starter cloned, `verify_setup.py` passes, agent runs
locally.

1. Welcome + intros (60 sec each)
2. The voice AI failure mode story (5 min)
3. Confirm: `python verify_setup.py` shows green checks for everyone
4. Quick demo of the unmodified Nova-template agent in
   https://agents-playground.livekit.io

---

## Stage 1 — Fork & Deploy (4:45–5:15)

**Goal:** Your generic starter agent is live on LiveKit Cloud and you've
placed your first call.

1. Run `python agent.py dev` locally
2. Open https://agents-playground.livekit.io, paste LiveKit credentials
3. Place a call → verify the generic agent greets you
4. Deploy to LiveKit Cloud:
   ```bash
   lk cloud auth
   lk agent create   # follow prompts
   lk agent list     # confirm "voice-workshop-agent" is up
   ```

✅ **Checkpoint:** You can place a call against your deployed agent and hear it speak.

---

## Stage 2 — Customize with Claude (5:15–5:45)

**Goal:** Your agent is now YOUR product (pizza bot, healthcare triage,
trivia host, customer support — whatever you brought).

1. Decide what your agent does. If stuck, pick a recipe from `recipes/`.
2. Open Claude Code in this repo: `claude`
3. Paste **PROMPT 2** from `PROMPT_CHEATSHEET.md` with your idea filled in
4. Claude will rewrite `SYSTEM_PROMPT`, add tools, generate knowledge files
5. Run `python build_knowledge.py && python agent.py dev`
6. Place another call → confirm the agent now plays YOUR persona
7. Re-deploy: `lk agent deploy`

✅ **Checkpoint:** Your agent introduces itself as your custom persona and
answers domain questions.

---

## Stage 3 — Stress-Test with NovaSynth (5:45–6:30)

**Goal:** 10 synthetic callers placed against your live agent.

1. Go to https://noveum.ai → NovaSynth → Agent Endpoints → New → LiveKit
2. Configure the endpoint (URL, key, secret, agent name = `voice-workshop-agent`)
3. Use **PROMPT 4** in Claude Code to generate 5 personas + 5 scenarios
4. Paste the generated configs into NovaSynth → Personas + Scenarios
5. Create a Batch Run with 10 explicit pairs (NOT Cartesian — see below)
6. Click Run

**Why explicit pairs:** each persona's background only fits some scenarios.
10 thoughtful pairs > 25 noisy ones for signal quality.

✅ **Checkpoint:** Batch run is in progress, you can see calls being placed
in NovaSynth's "Active Runs" view.

---

## Stage 4 — Debug with Three-Pane Traces (6:30–7:00)

**Goal:** Find your agent's actual latency budget and quality failures.

1. Go to Noveum → Traces → filter by `voice-workshop` project
2. Pick a recent call → open the three-pane trace view
3. Expand the span tree: STT → LLM → TTS
4. Note the slowest span (usually LLM or TTS)
5. Look for failures: hallucinated facts, wrong tool calls, off-script responses

✅ **Checkpoint:** You can name (a) your worst latency span and (b) one
quality failure your agent made.

---

## Stage 5 — Fix with NovaPilot + Claude (7:00–7:20)

**Goal:** Ship a fix and re-run the batch.

1. Go to Noveum → Eval Jobs → run the auto-created job for your batch
2. Click NovaPilot → Generate Report
3. Read the failure pattern recommendations
4. Copy the recommendation into Claude Code with **PROMPT 6**
5. Claude updates `SYSTEM_PROMPT` (or tools) to address it
6. Re-deploy: `lk agent deploy`
7. Re-run the NovaSynth batch
8. Compare scores before/after in NovaPilot

✅ **Checkpoint:** Your second NovaPilot report shows improvement on the
metric you targeted.

---

## Stage 6 — Demos + Q&A (7:20–7:30)

**Goal:** Show off your agent. 30 seconds each. Snacks open.

1. 3 attendees demo their agents live
2. Q&A
3. Keep building — your free Noveum tier covers continuous experimentation
4. Stick around for 1:1 debugging if you want

---

## Cheatsheet locations

- **Claude Code prompts** → `PROMPT_CHEATSHEET.md`
- **Recipe ideas** → `recipes/*.md`
- **Stuck?** → ask out loud, or DM #voice-workshop on the Frontier Discord

## Post-workshop

- Repo is yours — fork, ship, sell
- Free Noveum tier covers ~50k traces/mo + 1k eval credits/mo
- Office hours every Wednesday 5–6 PM PT on Discord
