# Prompt Cheatsheet

The prompts you'll paste into **Cursor** (or `claude` CLI) — in order through the workshop.

> Open Cursor in this repo (`cursor .`) or Claude Code (`claude`). Both read `CLAUDE.md`
> automatically and have all the context they need.

---

## PROMPT 1 — Sanity check

Use this first, as soon as you open Cursor. Confirms the AI can read the repo.

```
Read CLAUDE.md and tell me in 3 bullets:
1. What this repo is
2. Which file I customize for my agent's persona
3. What running `python agent.py dev` does

Don't change any code. Just confirm you understand the scaffold.
```

---

## PROMPT 2 — Make it yours

The big one. Describe what you want to build and let Cursor handle the rest.

```
I want to turn this generic voice agent into [YOUR PRODUCT].

What this agent does:
- <Describe your agent in detail. What is its job? Who does it talk to?
  What should it say? What should it never say? What tools does it need?>

First, read agent.py, tools/, and knowledge_sources/ to understand
the current state of the repo.

Then:
1. Rewrite SYSTEM_PROMPT in agent.py for this persona. Follow the voice
   agent prompt-writing rules in CLAUDE.md (AI disclosure, voice output
   rules, one thought per turn, when to call tools).
2. Update the opening greeting in `entrypoint()` (the `session.generate_reply`
   call near the bottom of agent.py) to match the new persona.
3. Replace the existing tools (place_order.py, end_call.py) with 2-3 tools my agent actually
   needs. Stub the implementations — log the call and return a plausible
   string. Update `tools/__init__.py` and the `tools=[]` list in agent.py.
   Keep `end_call.py` as-is unless you have a reason to change it.
4. Replace the existing knowledge files (menu.md) with 2-3 short markdown files
   of domain knowledge my agent should know.
5. Change `agent_name` in `WorkerOptions` to a short slug for my agent
   (e.g. "tonys-pizza-agent").

Don't touch the LiveKit / Groq / Smallest.ai / VAD / endpointing config.
Don't touch the Noveum tracing setup. Keep changes tight.
```

Test locally after this:
```bash
python build_knowledge.py
python agent.py dev
```

---

## PROMPT 3 — Pre-deploy checklist + deploy to LiveKit

Run this before every deployment. Catches mistakes before they go live.

```
Read agent.py, tools/__init__.py, and knowledge_sources/ first.

Then audit:
1. Is `agent_name` in WorkerOptions distinctive (not "workshop-starter-agent")?
2. Are all tools registered in BOTH tools/__init__.py AND the tools=[]
   list in agent.py?
3. Is SYSTEM_PROMPT under 2,500 tokens?
4. Are there any TODO / FIXME / "REPLACE WITH" placeholders left?
5. Does the opening greeting in `session.generate_reply` match the persona?

List any issues. After I review and confirm, run:
  python build_knowledge.py

Then check if the agent has been deployed before:
  lk agent list

- If the agent is NOT in the list, run: lk agent create
- If the agent IS already in the list, run: lk agent deploy

Then confirm the latest version shows up in `lk agent list`.
```

---

## PROMPT 4 — Set up NovaSynth + stress-test the deployed agent

After your agent is deployed. Cursor drives the entire setup via the Noveum MCP — no UI clicks needed.

```
Use the Noveum MCP to fully configure and stress-test my deployed agent.

First, read these from the repo — do NOT ask me to provide them:
- agent_name: read from WorkerOptions in agent.py
- SYSTEM_PROMPT: read in full from agent.py
- LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET: read from .env
- NOVEUM_PROJECT: read from .env (default: "voice-workshop")

━━━ PHASE 1: Project & Agent Config ━━━

Step 1 — Find the project.
Call getApiV1Projects. Find the project matching NOVEUM_PROJECT.
Save the projectId. Pass it on every subsequent call that accepts projectId.

Step 2 — Upsert agent config.
Call getApiV1NovasynthAgent-config to check current state.
Then call putApiV1NovasynthAgent-config with:
  - systemPrompt: the full SYSTEM_PROMPT you read from agent.py
  - agentName: agent_name from WorkerOptions
  - agentDescription: one sentence summarising what the agent does
This triggers Noveum's first-time eval/dataset auto-setup.

Step 3 — Check success criteria.
Call getApiV1NovasynthAgent-configSuccess-criteria.
List any scorers/metrics that are enabled. Note them — they'll appear in
the batch report after runs complete.

━━━ PHASE 2: Endpoint ━━━

Step 4 — Register (or reuse) the LiveKit endpoint.
Call getApiV1NovasynthAgent-endpoints to see if one already exists for
this agent. If one matches, reuse it.
Otherwise call postApiV1NovasynthAgent-endpoints with:
  - name: "[agent_name] (LiveKit)"
  - type: "livekit"
  - livekitUrl, livekitApiKey, livekitApiSecret: from .env
  - livekitAgentName: agent_name from WorkerOptions
Save the endpoint id.

━━━ PHASE 3: Personas & Scenarios ━━━

Step 5 — Generate 5 personas.
Call postApiV1NovasynthPersonasGenerate with projectId and a generation
prompt describing 5 diverse callers scoped to this agent's domain
(infer the domain from SYSTEM_PROMPT):
  - happy path / cooperative user
  - frustrated user
  - confused / first-time user
  - adversarial / off-script user
  - ESL speaker
Poll getApiV1NovasynthGeneration-jobs every 2 seconds until the job
reaches a terminal status. Save all returned persona ids.

Step 6 — Generate 5 scenarios.
Call postApiV1NovasynthScenariosGenerate with projectId and a generation
prompt for 5 scenarios scoped to this agent's domain:
  - happy path (user fully achieves their goal)
  - edge case (unusual but valid request)
  - error recovery (agent makes a mistake, user corrects it)
  - off-topic deflection (user asks about something outside scope)
  - adversarial (user tries to manipulate or confuse the agent)
Poll getApiV1NovasynthGeneration-jobs every 2 seconds until done.
Save all returned scenario ids.

━━━ PHASE 4: Smoke Test ━━━

Step 7 — Single test run (batch of 1).
Call postApiV1NovasynthRuns with:
  - endpointId: from Step 4
  - personaId: the happy path persona
  - scenarioId: the happy path scenario
  - mode: "voice"
  - maxCallDurationS: 120
  - projectId
Poll getApiV1NovasynthRunsById every 3 seconds until status is terminal
(completed / failed / cancelled).

Report the result — call duration, whether the agent responded in
character, any errors. Then STOP.

If it failed, tell me the error and do NOT continue.
If it passed, tell me it's ready and that I can paste PROMPT 5 to run
the full 10-pair batch.
```

---

## PROMPT 5 — Run the full batch

Only paste this after PROMPT 4's smoke test passes.

```
Use the Noveum MCP to run the full stress-test batch.

Use the projectId, endpointId, and persona/scenario ids from our current
conversation (printed at the end of PROMPT 4).

Call postApiV1NovasynthBatch-runs with 10 thoughtful persona-scenario
pairings (NOT a cartesian product — each pair should make narrative sense):
  - endpointId: from PROMPT 4
  - projectId: from PROMPT 4
  - mode: "voice"
  - concurrencyLimit: 3
  - maxCallDurationS: 180
  - pairs: array of { personaId, scenarioId } — 10 pairs, each pair
    chosen because the persona's background fits the scenario

Print the batch run id. Poll getApiV1NovasynthBatch-runsById every 4
seconds and show a running progress count (e.g. "3 / 10 complete").
Tell me when the batch finishes or when the first run completes.
```

---

## PROMPT 6 — Poll the batch + find the worst traces

Use while the batch from PROMPT 5 is running, or after it finishes.

```
Analyse the active NovaSynth batch run via the Noveum MCP.

Use the batch run id from our current conversation (printed at end of
PROMPT 5). If unavailable, call getApiV1NovasynthBatch-runs and pick
the most recent one.

1. Poll getApiV1NovasynthBatch-runsById every 4 seconds until status
   is terminal (completed / failed / cancelled / partial_failure).

2. Once done, fetch individual run results:
   Call getApiV1NovasynthRuns filtered by the batch run id.
   For each run call getApiV1NovasynthRunsById and summarise:
   - Total call duration
   - STT / LLM / TTS span times (the latency budget)
   - Tool calls made and whether arguments looked correct
   - Whether the agent stayed in character
   - Eval scores from success criteria (if present)

3. Try to fetch the batch-level NovaPilot analysis:
   Call getApiV1NovasynthBatch-analysisByBatchRunId.
   If not ready, call postApiV1NovasynthBatch-analysisByBatchRunIdRebuild
   and poll every 4 seconds until done.

4. Tell me which 2-3 runs look the worst (slowest, off-script,
   lowest scores). I'll inspect those in the Noveum UI.
```

---

## PROMPT 7 — Apply NovaPilot's fixes + redeploy + re-run

The full improvement loop.

```
Run the full NovaPilot fix loop via the Noveum MCP.

Use the batch run id from our current conversation (printed at end of
PROMPT 5). If unavailable, call getApiV1NovasynthBatch-runs and pick
the most recent completed one.

1. Fetch the NovaPilot batch analysis:
   Call getApiV1NovasynthBatch-analysisByBatchRunId.
   If the analysis isn't ready, call
   postApiV1NovasynthBatch-analysisByBatchRunIdRebuild and poll
   getApiV1NovasynthBatch-analysisByBatchRunId every 4 seconds
   until status is terminal.

2. Read the failure-pattern recommendations from the report.

3. Read the current SYSTEM_PROMPT and tools from this repo.
   For each recommendation, propose a specific code change to
   SYSTEM_PROMPT or a tool's docstring/implementation. Show the diff.

4. After I approve each change, apply it.

5. Run `lk agent deploy` to push the new version.

6. Trigger a NEW batch run via postApiV1NovasynthBatch-runs using
   the SAME persona-scenario pairs as the previous batch
   (call getApiV1NovasynthBatch-runsById to retrieve them).
   Use mode: "voice", concurrencyLimit: 3, maxCallDurationS: 180.

7. Poll the new batch every 4 seconds until terminal.
   Then call getApiV1NovasynthBatch-analysisByBatchRunId on BOTH
   batches and compare scores per scorer. Did we improve?
```

---

## Bonus: Add a specific tool

When you realize you need one more capability.

```
Add a new tool to my agent called `[tool_name]`.

What it should do: [1-2 sentences]
Arguments: [list args, types, descriptions]
Returns: [what the LLM gets back]

First read tools/ and agent.py to understand the existing tool pattern.

Stub the implementation — log the call and return a plausible string.
Don't call any real external API.

Drop the file in tools/, register it in tools/__init__.py, and add it
to the tools=[] list in agent.py. Write the docstring as instructions
to the LLM about WHEN and WHY to call this tool.
```

---

## Bonus: Fix a broken agent

Use this if the agent stopped working after a change.

```
The agent broke. Here's the error:

[PASTE ERROR HERE]

Read the repo first — agent.py, tools/__init__.py, and any recently
changed files — then check:
1. Whether tools are registered in BOTH tools/__init__.py and agent.py
2. Whether SYSTEM_PROMPT references a tool that doesn't exist
3. Whether build_knowledge.py was re-run after editing knowledge_sources/

Apply the smallest fix that makes the error go away. Don't refactor.
```
