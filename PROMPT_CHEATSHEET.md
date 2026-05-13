# Claude Code Prompt Cheatsheet

The 8 prompts you'll paste into **Claude Code** (or Cursor) at each workshop
stage. Each prompt is self-contained — copy, fill the bracketed sections,
paste.

> Tip: open Claude Code in this repo's directory (`claude`). It will read
> `CLAUDE.md` automatically and have all the context it needs.

---

## PROMPT 1 — Sanity check that everything is wired up

Use this first to make sure Claude Code can read the repo.

```
Read CLAUDE.md and tell me in 3 bullets:
1. What this repo is
2. Which file I customize for my agent's persona
3. What runs `python agent.py dev` does

Don't change any code. Just confirm you understand the scaffold.
```

---

## PROMPT 2 — Reshape the agent into YOUR product

The big one. Replace `[YOUR PRODUCT]` with what you want to build.

```
I want to turn this generic voice agent into [YOUR PRODUCT].

Examples of [YOUR PRODUCT]:
- A friendly pizza-ordering voice agent for a SF pizzeria called "Tony's"
- A healthcare triage agent that asks 5 symptom questions and recommends
  emergency / urgent care / primary care
- A trivia game host that asks Pokemon questions and tracks score
- A customer support agent for [your actual SaaS company]

Please:
1. Rewrite SYSTEM_PROMPT in agent.py for this persona. Follow the voice agent
   prompt-writing rules in CLAUDE.md (AI disclosure, voice output rules, one
   thought per turn, when to call tools).
2. Update the agent's opening greeting in `entrypoint()` (the
   `session.generate_reply` call near the bottom of agent.py) to fit.
3. Replace `tools/example_tool.py` with 2-3 tools my agent actually needs.
   Stub the implementations with print() and a return string for now.
   Update `tools/__init__.py` and the `tools=[]` list in agent.py.
4. Replace `knowledge_sources/example.md` with 2-3 short markdown files of
   domain knowledge my agent should know.
5. Change `agent_name` in `WorkerOptions` to a slug for my agent.

Don't touch the LiveKit / Groq / ElevenLabs / VAD / endpointing
config. Don't touch the Noveum tracing setup. Keep the changes tight.
```

---

## PROMPT 3 — Add a specific tool

When you realize you need one more tool. Replace the bracketed section.

```
Add a new tool to my agent called `[tool_name]`.

What it should do: [describe in 1-2 sentences]

Arguments: [list the args, types, brief descriptions]

Returns: [what the LLM should get back]

Stub the implementation — don't actually call any external API. Just
log the call and return a plausible string.

Drop the file in tools/, register it in tools/__init__.py, and add
it to the tools=[] list in agent.py. Make sure the docstring reads as
instructions to the LLM about WHEN to call this tool.
```

---

## PROMPT 4 — Set up NovaSynth + run the batch (via Noveum MCP)

For Stage 3 (stress-testing). Claude Code drives the entire NovaSynth setup through the Noveum MCP — no UI clicks required.

```
Use the Noveum MCP to run a stress-test batch against my deployed agent.
My agent: [1-sentence description of what it does, e.g., "voice ordering
agent for Tony's Pizza Palace"]
My LiveKit URL: <from .env, like wss://noveum-ai-peg9ygln.livekit.cloud>
My agent_name (from WorkerOptions in agent.py): voice-workshop-agent

Step 1 — Make sure the project exists. Use getApiV1Projects, find or
create one called "voice-workshop". Save the projectId.

Step 2 — Register the LiveKit agent endpoint via
postApiV1NovasynthAgent-endpoints with:
- name: "Workshop Agent (LiveKit)"
- type: livekit
- livekitUrl, livekitApiKey, livekitApiSecret from my env (read .env)
- livekitAgentName: voice-workshop-agent
Save the returned endpoint.id.

Step 3 — Generate 5 personas via postApiV1NovasynthPersonasGenerate.
Make them DIVERSE: at least one frustrated user, one confused user,
one adversarial / off-script user, one ESL speaker, one happy path.
All scoped to my agent's domain.

Step 4 — Generate 5 scenarios via postApiV1NovasynthScenariosGenerate.
Cover: happy path, edge case, error recovery, off-topic deflection,
adversarial. Each with branching events (id, parent_id, action,
condition, fixed).

Step 5 — Trigger a batch run via postApiV1NovasynthBatch-analysis...
with explicit pairs (NOT cartesian) — 10 thoughtful pairings.
mode: text (cheaper than voice for this dev loop), concurrencyLimit: 3,
maxCallDurationS: 180.

Step 6 — Print the batch run id + status. Tell me when the first call
completes so I know it's working.
```

---

## PROMPT 5 — Poll the batch + summarize traces (via MCP)

Use this while the batch from PROMPT 4 is running, or after it finishes.

```
Tail the active NovaSynth batch run via the Noveum MCP.

1. Use getApiV1NovasynthBatch-analysisByBatchRunId to poll the batch.
   Wait until all calls reach a terminal state (completed/failed).
2. Once done, use getApiV1Traces filtered by novasynth.batch_run_id
   to fetch every trace from the run.
3. For each trace, summarize:
   - Total duration
   - STT span time, LLM span time, TTS span time (the latency budget)
   - Tool calls made + whether arguments looked correct
   - Whether the agent stayed in character (look at full I/O)
4. Tell me which 2-3 traces look the worst (longest latency,
   off-script, hallucinated). I'll inspect those visually.
```

---

## PROMPT 6 — Apply NovaPilot's recommendations (full round-trip via MCP)

Stage 5 — Claude Code drives NovaPilot, applies fixes, redeploys, re-runs.

```
Run the full NovaPilot fix loop for my last batch run id [BATCH_ID].

1. Use getApiV1NovasynthRun-analysisByBatchRunId to fetch the
   NovaPilot report. If empty, call
   postApiV1NovasynthBatch-analysisByBatchRunIdRebuild first and poll
   until ready.
2. Read the failure-pattern recommendations.
3. For each recommendation, propose a code change to SYSTEM_PROMPT or
   a tool's docstring/implementation in this repo. Show me the diff.
4. After I approve, apply the changes.
5. Run `lk agent deploy` to push the new version.
6. Trigger a NEW batch run via postApiV1NovasynthBatch-analysis...
   with the SAME persona-scenario pairs as the previous batch
   (so we can compare apples to apples).
7. Once done, use getApiV1NovasynthRun-analysisByRunId on both batches
   and tell me the score deltas per scorer. Did we improve?
```

---

## PROMPT 7 — Shorten / speed up the system prompt

Long system prompts hurt latency. Run this before any deploy.

```
My SYSTEM_PROMPT in agent.py is too long. Shorten it without losing the
critical sections (AI disclosure, voice output rules, tool calling rules).

Constraints:
- Must stay under 1,500 tokens
- Keep the AI disclosure section verbatim
- Keep the voice output rules section verbatim
- Reorder so the most-load-bearing instructions come first
- Drop redundant rephrasings

After editing, run `lk agent deploy` and confirm the new agent registered.
```

---

## PROMPT 8 — Debug a latency issue from a trace span

When PROMPT 5 surfaces high latency on a specific span.

```
My Noveum trace shows that the [STT|LLM|TTS] span takes [N] ms on average
for my voice agent. That's too slow for sub-500ms turns.

Help me reduce it. Look at:
- agent.py for config flags I can tune for that provider
- Whether I should switch model / voice / streaming setting
- Whether the system prompt or tool calls are bloating the request

Show me the smallest change that should help. Don't refactor anything else.
After editing, run `lk agent deploy`.
```

---

## PROMPT 9 — Pre-deploy checklist

Run this before each `lk agent deploy`.

```
Before I deploy, audit:
1. Is `agent_name` in WorkerOptions distinctive (not the default
   "voice-workshop-agent")?
2. Are all my tools registered in BOTH tools/__init__.py AND the
   tools=[] list in agent.py?
3. Is SYSTEM_PROMPT under 2,500 tokens?
4. Did I leave any TODO / FIXME / "REPLACE WITH" placeholders?
5. Does the opening greeting `session.generate_reply` make sense for
   my agent's persona?

Show me a list of issues, no fixes needed unless I ask.
```

---

## Bonus: The "fix everything Claude saw" prompt

Use this if the agent broke after a complex change.

```
The agent broke. Here's the error: [PASTE ERROR]

Look at:
1. The most recent files you changed
2. Whether tools are registered consistently in tools/__init__.py and agent.py
3. Whether SYSTEM_PROMPT references any tool that doesn't exist
4. Whether build_knowledge.py was re-run after editing knowledge_sources/

Apply the smallest fix that makes the error go away. Don't refactor.
```
