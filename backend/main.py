# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from .db import init_db, get_session
from .schemas import WebSocketMessage, ConversationState, UserResponse
from .conversation_engine import ConversationEngine
from .openai_client import OpenAIClient
from . import crud
from .models import LicenseType, LicenseStatus

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down")

app = FastAPI(
    title="Bind IQ Chatbot",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_engine = ConversationEngine()
openai_client = OpenAIClient()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_session)):
    await websocket.accept()
    session_id = websocket.headers.get("x-session-id", websocket.client.host)
    
    try:
        # Initialize user
        user = await crud.get_or_create_user(db, session_id)
        
        # Send initial message
        initial_state = ConversationState.start
        initial_prompt = conversation_engine.get_prompt(initial_state)
        initial_response = await openai_client.generate_response(
            initial_state.value, initial_prompt
        )
        
        await websocket.send_json({
            "type": "bot_message",
            "content": initial_response,
            "data": {"state": initial_state.value}
        })
        
        await crud.save_message(db, user.id, "assistant", initial_response)
        await crud.update_session_state(db, user.id, ConversationState.collecting_zip.value)
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if data.get("type") == "user_message":
                user_message = data.get("content", "")
                
                # Save user message
                await crud.save_message(db, user.id, "user", user_message)
                
                # Get current state
                session = await crud.get_session(db, user.id)
                current_state = ConversationState(session.current_state)
                state_data = json.loads(session.state_data)
                
                # Validate input
                is_valid, parsed_data, error_msg = conversation_engine.validate_input(
                    current_state, user_message
                )
                
                if not is_valid:
                    # Send error response
                    error_response = await openai_client.generate_error_response(
                        current_state.value, user_message, error_msg
                    )
                    
                    await websocket.send_json({
                        "type": "bot_message",
                        "content": error_response,
                        "data": {"state": current_state.value}
                    })
                    
                    await crud.save_message(db, user.id, "assistant", error_response)
                    continue
                
                # Process valid input
                await process_valid_input(
                    db, user, current_state, parsed_data, state_data
                )
                
                # Get next state
                next_state = conversation_engine.get_next_state(
                    current_state, parsed_data, state_data
                )
                
                # Generate response
                next_prompt = conversation_engine.get_prompt(next_state)
                response = await openai_client.generate_response(
                    next_state.value, next_prompt, user.full_name
                )
                
                # Update session
                await crud.update_session_state(db, user.id, next_state.value, state_data)
                
                # Send response
                await websocket.send_json({
                    "type": "bot_message",
                    "content": response,
                    "data": {"state": next_state.value}
                })
                
                # Send progress update
                progress = conversation_engine.calculate_progress(next_state)
                await websocket.send_json({
                    "type": "state_update",
                    "data": {
                        "current_state": next_state.value,
                        "progress": progress
                    }
                })
                
                await crud.save_message(db, user.id, "assistant", response)
                
    except WebSocketDisconnect:
        logger.info(f"Client {session_id} disconnected")
    except Exception as e:
        logger.error(f"Error in websocket: {str(e)}")
        await websocket.close()

async def process_valid_input(
    db: AsyncSession,
    user,
    state: ConversationState,
    parsed_data,
    state_data: dict
):
    """Update database with validated input"""
    
    if state == ConversationState.collecting_zip:
        await crud.update_user(db, user.id, zip_code=parsed_data)
        
    elif state == ConversationState.collecting_name:
        await crud.update_user(db, user.id, full_name=parsed_data)
        
    elif state == ConversationState.collecting_email:
        await crud.update_user(db, user.id, email=parsed_data)
        
    elif state == ConversationState.collecting_vehicle_info:
        state_data["current_vehicle"] = parsed_data
        
    elif state == ConversationState.collecting_vehicle_use:
        state_data["current_vehicle"]["vehicle_use"] = parsed_data
        
    elif state == ConversationState.collecting_blind_spot:
        state_data["current_vehicle"]["blind_spot_warning"] = parsed_data
        
    elif state == ConversationState.collecting_commute_days:
        state_data["current_vehicle"]["days_per_week"] = parsed_data
        
    elif state == ConversationState.collecting_commute_miles:
        state_data["current_vehicle"]["one_way_miles"] = parsed_data
        await crud.save_vehicle(db, user.id, state_data["current_vehicle"])
        state_data["current_vehicle"] = {}
        
    elif state == ConversationState.collecting_annual_mileage:
        state_data["current_vehicle"]["annual_mileage"] = parsed_data
        await crud.save_vehicle(db, user.id, state_data["current_vehicle"])
        state_data["current_vehicle"] = {}
        
    elif state == ConversationState.collecting_license_type:
        await crud.update_user(db, user.id, license_type=LicenseType(parsed_data))
        
    elif state == ConversationState.collecting_license_status:
        await crud.update_user(db, user.id, license_status=LicenseStatus(parsed_data))

@app.get("/api/users/{session_id}", response_model=UserResponse)
async def get_user(session_id: str, db: AsyncSession = Depends(get_session)):
    user = await crud.get_or_create_user(db, session_id)
    return user

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Bind IQ Chatbot"}