"""Local dev UI server — chat with the agent in a browser, not the LiveKit playground.

Run alongside `python agent.py dev`:

    python dev_ui/server.py

Open http://127.0.0.1:8080.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

from aiohttp import web
from dotenv import load_dotenv
from livekit.api import AccessToken, LiveKitAPI, VideoGrants
from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
from livekit.protocol.room import CreateRoomRequest

_DIR = Path(__file__).resolve().parent
load_dotenv(_DIR.parent / ".env")

logging.basicConfig(level=logging.INFO, format="[dev_ui] %(message)s")
logger = logging.getLogger("dev_ui")

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]
AGENT_NAME = os.environ.get("AGENT_NAME", "tonys-pizza-agent")


async def _mint_token(request: web.Request) -> web.Response:
    body = await request.json()
    persona_config = {
        k: v for k, v in {
            "system_prompt": body.get("system_prompt"),
            "greeting": body.get("greeting"),
            "voice_id": body.get("voice_id"),
            "groq_model": body.get("groq_model"),
            "groq_temperature": body.get("groq_temperature"),
        }.items()
        if v not in (None, "", "default")
    }
    agent_name = body.get("agent_name") or AGENT_NAME

    room_name = f"dev-ui-{uuid.uuid4().hex[:8]}"
    metadata_str = json.dumps(persona_config)

    lkapi = LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    try:
        await lkapi.room.create_room(CreateRoomRequest(
            name=room_name,
            metadata=metadata_str,
            empty_timeout=60,
            max_participants=4,
        ))
        await lkapi.agent_dispatch.create_dispatch(CreateAgentDispatchRequest(
            agent_name=agent_name,
            room=room_name,
        ))
    finally:
        await lkapi.aclose()

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(f"user-{uuid.uuid4().hex[:6]}")
        .with_name("Dev User")
        .with_grants(VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
        .to_jwt()
    )

    logger.info("room=%s agent=%s overrides=%s", room_name, agent_name, list(persona_config))
    return web.json_response({
        "token": token,
        "url": LIVEKIT_URL,
        "room_name": room_name,
        "agent_name": agent_name,
    })


async def _index(request: web.Request) -> web.Response:
    return web.FileResponse(_DIR / "static" / "index.html")


def main() -> None:
    app = web.Application()
    app.router.add_get("/", _index)
    app.router.add_post("/api/token", _mint_token)
    app.router.add_static("/static", path=_DIR / "static", show_index=False)
    web.run_app(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
