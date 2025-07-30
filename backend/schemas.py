from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"

class ConversationState(str, Enum):
    start = "start"
    collecting_zip = "collecting_zip"
    collecting_name = "collecting_name"
    collecting_email = "collecting_email"
    vehicle_intro = "vehicle_intro"
    collecting_vehicle_info = "collecting_vehicle_info"
    collecting_vehicle_use = "collecting_vehicle_use"
    collecting_blind_spot = "collecting_blind_spot"
    collecting_commute_days = "collecting_commute_days"
    collecting_commute_miles = "collecting_commute_miles"
    collecting_annual_mileage = "collecting_annual_mileage"
    ask_more_vehicles = "ask_more_vehicles"
    collecting_license_type = "collecting_license_type"
    collecting_license_status = "collecting_license_status"
    completed = "completed"

class WebSocketMessage(BaseModel):
    type: str
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    state: ConversationState
    progress: float

class UserResponse(BaseModel):
    id: int
    session_id: str
    zip_code: Optional[str]
    full_name: Optional[str]
    email: Optional[EmailStr]
    license_type: Optional[str]
    license_status: Optional[str]
    vehicles: List[Dict[str, Any]]
    created_at: datetime