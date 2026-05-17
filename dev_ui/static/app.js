// Voice agent dev console — connects to LiveKit, swaps persona on the fly.

const PRESETS = {
  "tonys-pizza": {
    label: "Tony's Pizza (default)",
    greeting: "Greet the customer warmly as Tony from Tony's Pizza. Identify yourself as an AI assistant in the same sentence. Ask what they would like to order tonight. One sentence, then pause and listen.",
    systemPrompt: `You are Tony, the friendly AI voice assistant at Tony's Pizza.
You take phone orders for pizzas, sides, and drinks.

# AI DISCLOSURE
- In your opening turn, mention you are an AI assistant.
- If asked directly, confirm in one sentence.

# VOICE OUTPUT — STRICT
- ONE short sentence per turn. After the sentence ends, STOP.
- No markdown, lists, code, headings, or emoji.
- Numbers as words: "twelve dollars", "twenty to twenty five minutes".

# CALL FLOW
1. Greet warmly + AI disclosure. Ask what they would like to order.
2. For each pizza, confirm size and toppings before moving on.
3. When done, read back full order, ask if it is correct.
4. Once confirmed, call place_order with every item and quantity.
5. Tell them pickup time. Ask if anything else.
6. On goodbye, call end_call.

# MENU
Sizes: small ten inch twelve dollars, medium fourteen inch sixteen dollars, large eighteen inch twenty dollars.
Classic pies: Margherita, Pepperoni, Hawaiian, Veggie Supreme, Meat Lovers.
Toppings two dollars each.
Sides: garlic knots six, caesar salad eight, wings ten.
Drinks: soda three, water two.
Pickup ready in twenty to twenty five minutes.`,
  },
  "library-booking": {
    label: "Library Room Booking",
    greeting: "Greet the caller as Sam from Central Library Booking. Identify yourself as an AI assistant. Ask how you can help with their room booking today. One sentence, then pause.",
    systemPrompt: `You are Sam, the AI voice assistant for Central Library's room booking line.
You help patrons reserve study rooms and answer policy questions.

# AI DISCLOSURE
- In your opening turn, mention you are an AI assistant.
- If asked directly, confirm in one sentence.

# VOICE OUTPUT — STRICT
- ONE short sentence per turn. Then STOP.
- No markdown, lists, code, headings, or emoji.
- Numbers as words: "two hours", "from three to five PM".

# CALL FLOW
1. Greet + AI disclosure. Ask how you can help.
2. Ask for desired date, time, and group size.
3. Confirm a matching room before booking.
4. Once confirmed, call book_room with all details.
5. Read back confirmation. Ask if anything else.
6. On goodbye, call end_call.

# POLICIES
- Rooms hold two to twelve people.
- Maximum two hour booking per group.
- Same-day bookings allowed if rooms free.
- No food in rooms; water OK.
- Library hours: nine AM to nine PM weekdays, ten AM to six PM weekends.`,
  },
  "tech-support": {
    label: "Friendly Tech Support",
    greeting: "Greet the caller warmly as Riley from CloudWidget support. Identify yourself as an AI assistant in the same sentence. Ask what you can help them with today.",
    systemPrompt: `You are Riley, an AI voice support agent at CloudWidget.
You help customers troubleshoot login, billing, and dashboard problems.

# AI DISCLOSURE
- Mention you are an AI assistant in the opening turn.
- Confirm on direct ask in one sentence.

# VOICE OUTPUT — STRICT
- ONE short sentence per turn. Then STOP.
- No markdown, lists, code, headings, or emoji.
- Numbers as words.

# CALL FLOW
1. Greet + AI disclosure. Ask how to help.
2. Ask one diagnostic question at a time, never two.
3. Suggest one fix at a time and ask if it worked.
4. If a fix works, confirm and ask if anything else.
5. If stuck after three attempts, offer to escalate to a human and call end_call.

# COMMON FIXES
- Login loop: clear browser cookies for the site.
- Dashboard slow: check if user is on the legacy plan.
- Billing failed: card may be expired or in wrong currency.`,
  },
  "sales-sdr": {
    label: "Sales SDR Discovery",
    greeting: "Open with: Hi, this is Morgan, an AI assistant calling from NorthStar. Do you have a quick minute to chat about your team's analytics stack?",
    systemPrompt: `You are Morgan, an AI sales development rep at NorthStar Analytics.
Your goal: discover whether the prospect has a pain point worth a demo.

# AI DISCLOSURE
- Identify as an AI in the opening turn.
- Confirm on direct ask in one sentence.

# VOICE OUTPUT — STRICT
- ONE short sentence per turn. Then STOP.
- No markdown, no jargon dump.
- Numbers as words.

# CALL FLOW
1. Open + AI disclosure + ask if they have a minute.
2. If yes, ask one discovery question at a time:
   - What analytics tools do they currently use?
   - What is the most painful part of their reporting today?
   - How big is the data team?
3. If they show interest, offer to book a demo and call end_call.
4. If they decline, thank them politely and call end_call.

# DO NOT
- Pitch features unprompted.
- Push past a "no".
- Ask more than one question at a time.`,
  },
  "custom": {
    label: "Custom (edit prompt below)",
    greeting: "",
    systemPrompt: "You are a helpful AI voice assistant.\n\n# AI DISCLOSURE\n- Identify as an AI in the opening turn.\n\n# VOICE OUTPUT — STRICT\n- ONE short sentence per turn. Then STOP.\n- No markdown, lists, code, headings, or emoji.\n- Numbers as words.",
  },
};

// Verified valid Smallest.ai lightning-v3.1 voice IDs. Full list (234 voices):
//   curl https://waves-api.smallest.ai/api/v1/lightning-v3.1/get_voices \
//        -H "Authorization: Bearer $SMALLEST_API_KEY"
const VOICES = [
  { id: "default",  label: "Default (Sophia, US female)" },
  { id: "sophia",   label: "Sophia — US female" },
  { id: "mia",      label: "Mia — US female" },
  { id: "quinn",    label: "Quinn — US female" },
  { id: "hannah",   label: "Hannah — US female" },
  { id: "john",     label: "John — US male" },
  { id: "daniel",   label: "Daniel — US male" },
  { id: "lucas",    label: "Lucas — US male" },
  { id: "poppy",    label: "Poppy — British female" },
  { id: "julia",    label: "Julia — British female" },
  { id: "liam",     label: "Liam — British male" },
  { id: "noah",     label: "Noah — British male" },
  { id: "anika",    label: "Anika — Indian female" },
  { id: "maya",     label: "Maya — Indian female" },
  { id: "arjun",    label: "Arjun — Indian male" },
  { id: "kunal",    label: "Kunal — Indian male" },
  { id: "cooper",   label: "Cooper — Australian male" },
  { id: "sienna",   label: "Sienna — Australian female" },
];

const MODELS = [
  { id: "default", label: "Default (gpt-oss-120b)" },
  { id: "openai/gpt-oss-120b", label: "openai/gpt-oss-120b" },
  { id: "openai/gpt-oss-20b", label: "openai/gpt-oss-20b" },
  { id: "llama-3.3-70b-versatile", label: "llama-3.3-70b-versatile" },
  { id: "llama-3.1-8b-instant", label: "llama-3.1-8b-instant" },
  { id: "meta-llama/llama-4-scout-17b-16e-instruct", label: "llama-4-scout-17b" },
];

const $ = (id) => document.getElementById(id);
const presetSel = $("preset");
const voiceSel = $("voice");
const modelSel = $("model");
const tempInput = $("temperature");
const tempVal = $("tempVal");
const greetingTa = $("greeting");
const sysPromptTa = $("systemPrompt");
const connectBtn = $("connectBtn");
const disconnectBtn = $("disconnectBtn");
const muteBtn = $("muteBtn");
const statusEl = $("status");
const transcript = $("transcript");
const micIndicator = $("micIndicator");
const hint = $("hint");

Object.entries(PRESETS).forEach(([id, p]) => {
  const opt = document.createElement("option");
  opt.value = id;
  opt.textContent = p.label;
  presetSel.appendChild(opt);
});
VOICES.forEach((v) => {
  const o = document.createElement("option");
  o.value = v.id; o.textContent = v.label;
  voiceSel.appendChild(o);
});
MODELS.forEach((m) => {
  const o = document.createElement("option");
  o.value = m.id; o.textContent = m.label;
  modelSel.appendChild(o);
});

function applyPreset(id) {
  const p = PRESETS[id];
  if (!p) return;
  greetingTa.value = p.greeting;
  sysPromptTa.value = p.systemPrompt;
}
presetSel.addEventListener("change", () => applyPreset(presetSel.value));
applyPreset("tonys-pizza");

tempInput.addEventListener("input", () => { tempVal.textContent = tempInput.value; });

function setStatus(state, text) {
  statusEl.className = state;
  statusEl.textContent = text;
}

function addBubble(kind, text) {
  const div = document.createElement("div");
  div.className = `bubble ${kind}`;
  div.textContent = text;
  transcript.appendChild(div);
  transcript.scrollTop = transcript.scrollHeight;
  return div;
}

let room = null;

async function connect() {
  connectBtn.disabled = true;
  setStatus("connecting", "connecting…");
  addBubble("system", "Requesting token + dispatching agent…");

  let tokenData;
  try {
    const res = await fetch("/api/token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_prompt: sysPromptTa.value.trim(),
        greeting: greetingTa.value.trim(),
        voice_id: voiceSel.value,
        groq_model: modelSel.value,
        groq_temperature: tempInput.value,
      }),
    });
    if (!res.ok) throw new Error(`token endpoint ${res.status}`);
    tokenData = await res.json();
  } catch (err) {
    addBubble("error", `Failed to mint token: ${err.message}`);
    setStatus("error", "error");
    connectBtn.disabled = false;
    return;
  }

  addBubble("system", `Joining room ${tokenData.room_name} → ${tokenData.agent_name}`);

  room = new LivekitClient.Room({
    adaptiveStream: true,
    dynacast: true,
  });

  room.on(LivekitClient.RoomEvent.Disconnected, () => {
    setStatus("disconnected", "disconnected");
    micIndicator.classList.remove("active");
    connectBtn.disabled = false;
    disconnectBtn.disabled = true;
    muteBtn.disabled = true;
    muteBtn.textContent = "Mute";
    muteBtn.classList.remove("muted");
    hint.textContent = "Disconnected. Click Connect to start a new session.";
  });

  room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, pub, participant) => {
    if (track.kind === LivekitClient.Track.Kind.Audio) {
      const el = track.attach();
      el.style.display = "none";
      document.body.appendChild(el);
    }
  });

  room.on(LivekitClient.RoomEvent.TranscriptionReceived, (segments, participant) => {
    const speaker = participant?.isLocal ? "user" : "agent";
    for (const seg of segments) {
      const id = `${participant?.identity || "x"}-${seg.id}`;
      let bubble = document.getElementById(id);
      if (!bubble) {
        bubble = addBubble(speaker, seg.text);
        bubble.id = id;
      } else {
        bubble.textContent = seg.text;
        transcript.scrollTop = transcript.scrollHeight;
      }
    }
  });

  try {
    await room.connect(tokenData.url, tokenData.token);
    await room.localParticipant.setMicrophoneEnabled(true);
    setStatus("connected", "connected");
    micIndicator.classList.add("active");
    disconnectBtn.disabled = false;
    muteBtn.disabled = false;
    muteBtn.textContent = "Mute";
    muteBtn.classList.remove("muted");
    hint.textContent = "Speak whenever you are ready. The agent should greet you shortly.";
  } catch (err) {
    addBubble("error", `Connect failed: ${err.message}`);
    setStatus("error", "error");
    connectBtn.disabled = false;
  }
}

async function disconnect() {
  if (room) {
    await room.disconnect();
    room = null;
  }
}

async function toggleMute() {
  if (!room || !room.localParticipant) return;
  const currentlyEnabled = room.localParticipant.isMicrophoneEnabled;
  muteBtn.disabled = true;
  try {
    await room.localParticipant.setMicrophoneEnabled(!currentlyEnabled);
    const nowMuted = !room.localParticipant.isMicrophoneEnabled;
    muteBtn.textContent = nowMuted ? "Unmute" : "Mute";
    muteBtn.classList.toggle("muted", nowMuted);
    micIndicator.classList.toggle("active", !nowMuted);
  } finally {
    muteBtn.disabled = false;
  }
}

connectBtn.addEventListener("click", connect);
disconnectBtn.addEventListener("click", disconnect);
muteBtn.addEventListener("click", toggleMute);
