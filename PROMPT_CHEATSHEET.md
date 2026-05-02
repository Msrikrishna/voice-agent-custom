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

Don't touch the LiveKit / Groq / Deepgram / ElevenLabs / VAD / endpointing
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

## PROMPT 4 — Generate NovaSynth personas + scenarios

For Stage 3 (stress-testing).

```
Generate 5 NovaSynth personas and 5 scenarios for testing my voice agent.

My agent does: [1-sentence description]

For each persona, output a JSON object that fits this shape:
- name, description, goal, personalityTraits[], tonePreference,
  primaryLanguage[], knowledgeBase[], age, occupation, location,
  educationLevel, gender, interruptionLevel (0-1), speakingSpeed (0.5-1.5)

Make personas DIVERSE: different ages, occupations, knowledge levels,
languages where relevant. At least one should be:
- A frustrated / impatient user
- A confused user who asks clarifying questions
- An adversarial / off-script user (testing edge cases)

For each scenario, output a JSON object with:
- name, description, scenarioType (workflow|conversation|knowledge_base),
  interruptionLevel, metadata, and an `events` array. Each event has:
  id, parent_id (for branching), action (what the synthetic user does),
  condition (when this fires, or null), fixed (boolean).

Pair the 5 personas with 5 scenarios as 10 explicit pairs (some personas
fit multiple scenarios). I'll paste the JSONs into the Noveum NovaSynth UI.
```

---

## PROMPT 5 — Make the system prompt shorter / faster

System prompt too long → high latency. Run this before deploying.

```
My SYSTEM_PROMPT in agent.py is too long. Shorten it without losing the
critical sections (AI disclosure, voice output rules, tool calling rules).

Constraints:
- Must stay under 1,500 tokens
- Keep the AI disclosure section verbatim
- Keep the voice output rules section verbatim
- Reorder so the most-load-bearing instructions come first
- Drop redundant rephrasings
```

---

## PROMPT 6 — Apply NovaPilot's recommendations

Stage 5 — turn the AI analyst's report into a code change.

```
NovaPilot in Noveum gave me this recommendation after evaluating my agent:

[PASTE THE RECOMMENDATION HERE — copy from the NovaPilot UI]

Update SYSTEM_PROMPT (or the relevant tool docstring) in this repo to address
the recommendation. Show me the diff. Don't make any other changes.

If the recommendation is about a tool that doesn't exist yet, scaffold the
tool too.
```

---

## PROMPT 7 — Debug a latency issue from a Noveum trace

When traces show high latency on a specific span.

```
My Noveum trace shows that the [STT|LLM|TTS] span takes [N] ms on average
for my voice agent. That's too slow for sub-500ms turns.

Help me reduce it. Look at:
- agent.py for any config flags I can tune for that provider
- Whether I should switch model / voice / streaming setting
- Whether anything in the system prompt or tool calls is bloating the
  request to that provider

Show me the smallest change that should help. Don't refactor anything else.
```

---

## PROMPT 8 — Pre-deploy checklist

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
