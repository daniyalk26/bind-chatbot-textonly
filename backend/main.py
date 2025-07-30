# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
import json
import logging
import os

from dotenv import load_dotenv

from backend.db import init_db, get_session
from backend.schemas import WebSocketMessage, ConversationState, UserResponse
from backend.conversation_engine import ConversationEngine
import backend.models as models
from backend.openai_client import OpenAIClient
import backend.crud as crud

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  FastAPI setup
# ------------------------------------------------------------------ #
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")

app = FastAPI(title="Bind IQ Chatbot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine    = ConversationEngine()
ai_client = OpenAIClient()
   # avoid shadowing the module name

# ------------------------------------------------------------------ #
#  WebSocket endpoint
# ------------------------------------------------------------------ #
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, db: AsyncSession = Depends(get_session)):
    await ws.accept()
    session_id = ws.headers.get("x-session-id", ws.client.host)

    try:
        user = await crud.get_or_create_user(db, session_id)

        # --- Initial bot message ---
        init_state  = ConversationState.start
        init_prompt = engine.get_prompt(init_state)
        init_reply  = await ai_client.generate_response(init_state.value, init_prompt)

        await ws.send_json({"type": "bot_message", "content": init_reply, "data": {"state": init_state.value}})
        await crud.save_message(db, user.id, "assistant", init_reply)
        await crud.update_session_state(db, user.id, ConversationState.collecting_zip.value)

        # --- Main loop ---
        while True:
            data = await ws.receive_json()
            if data.get("type") != "user_message":
                continue

            user_msg = data.get("content", "")
            await crud.save_message(db, user.id, "user", user_msg)

            session = await crud.get_session(db, user.id)
            current = ConversationState(session.current_state)
            state_data = json.loads(session.state_data)

            # Validate
            ok, parsed, err = engine.validate_input(current, user_msg)
            if not ok:
                err_reply = await ai_client.generate_error_response(current.value, user_msg, err)
                await ws.send_json({"type": "bot_message", "content": err_reply, "data": {"state": current.value}})
                await crud.save_message(db, user.id, "assistant", err_reply)
                continue

            # Persist & decide next state
            await _apply_valid_input(db, user, current, parsed, state_data)
            next_state = engine.get_next_state(current, parsed, state_data)

            # Respond
            next_prompt = engine.get_prompt(next_state)
            reply = await ai_client.generate_response(next_state.value, next_prompt, user.full_name)

            await crud.update_session_state(db, user.id, next_state.value, state_data)
            await ws.send_json({"type": "bot_message", "content": reply, "data": {"state": next_state.value}})

            progress = engine.calculate_progress(next_state)
            await ws.send_json({"type": "state_update", "data": {"current_state": next_state.value, "progress": progress}})
            await crud.save_message(db, user.id, "assistant", reply)

    except WebSocketDisconnect:
        logger.info("Client %s disconnected", session_id)
    except Exception as exc:
        logger.exception("WebSocket error: %s", exc)
        await ws.close()

# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #
async def _apply_valid_input(
    db: AsyncSession,
    user,
    state: ConversationState,
    parsed,
    state_data: dict,
):
    """Write validated data to DB / session_state."""
    if state == ConversationState.collecting_zip:
        await crud.update_user(db, user.id, zip_code=parsed)

    elif state == ConversationState.collecting_name:
        await crud.update_user(db, user.id, full_name=parsed)

    elif state == ConversationState.collecting_email:
        await crud.update_user(db, user.id, email=parsed)

    elif state == ConversationState.collecting_vehicle_info:
        state_data["current_vehicle"] = parsed

    elif state == ConversationState.collecting_vehicle_use:
        state_data["current_vehicle"]["vehicle_use"] = parsed

    elif state == ConversationState.collecting_blind_spot:
        state_data["current_vehicle"]["blind_spot_warning"] = parsed

    elif state == ConversationState.collecting_commute_days:
        state_data["current_vehicle"]["days_per_week"] = parsed

    elif state == ConversationState.collecting_commute_miles:
        state_data["current_vehicle"]["one_way_miles"] = parsed
        await crud.save_vehicle(db, user.id, state_data["current_vehicle"])
        state_data["current_vehicle"] = {}

    elif state == ConversationState.collecting_annual_mileage:
        state_data["current_vehicle"]["annual_mileage"] = parsed
        await crud.save_vehicle(db, user.id, state_data["current_vehicle"])
        state_data["current_vehicle"] = {}

    elif state == ConversationState.collecting_license_type:
        await crud.update_user(db, user.id, license_type=models.LicenseType(parsed))

    elif state == ConversationState.collecting_license_status:
        await crud.update_user(db, user.id, license_status=models.LicenseStatus(parsed))

# ------------------------------------------------------------------ #
#  Simple health‑check
# ------------------------------------------------------------------ #
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Bind IQ Chatbot"}

