# Recipe: Pizza Ordering Bot 🍕

A friendly voice agent for a SF pizzeria called "Tony's". Takes orders,
quotes prices, confirms delivery address.

## Claude Code prompt to use

Paste this as PROMPT 2 from `PROMPT_CHEATSHEET.md`:

```
I want to turn this generic voice agent into a friendly pizza-ordering
voice agent for a SF pizzeria called "Tony's Pizza Palace".

The agent (call her "Mia") should:
- Greet warmly + AI disclosure
- Ask what the customer wants to order
- Quote prices for menu items (small/medium/large/XL pizzas, sides, drinks)
- Take a delivery address and confirm it back
- Confirm total + estimated delivery time (~35 min)
- End the call after confirming

Tools needed:
1. get_menu(category) — returns pizza/sides/drinks options + prices
2. add_to_order(item, size, quantity) — accumulates the running order
3. confirm_order(address) — locks in the order, returns confirmation #

Knowledge to add to knowledge_sources/:
- menu.md (pizzas with sizes/prices, classic toppings, sides, drinks)
- delivery-zones.md (which SF neighborhoods, delivery time, fees)

Voice ID: pNInz6obpgDQGcFmaJgB (default Adam) — or pick a friendlier voice
from https://elevenlabs.io/voice-library and update ELEVENLABS_VOICE_ID.

agent_name: "tonys-pizza"

Follow CLAUDE.md voice agent rules. Keep prices under ~$25.
```

## Persona ideas for NovaSynth testing

- **Hungry college student** — wants the cheapest large pizza, asks about
  student discounts, slightly impatient
- **Picky vegan** — asks about every topping's animal content, frustrated
  if it's not labeled clearly
- **Confused grandma** — asks the same question twice, slow speaker, gets
  the address wrong on the first try
- **Repeat customer** — assumes the agent remembers them ("the usual"),
  tests whether it admits it doesn't have memory
- **Adversarial prankster** — orders 99 pizzas, fake address, tries to
  make the agent break character
