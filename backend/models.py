from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class VehicleUse(str, Enum):
    commuting  = "commuting"
    business   = "business"
    commercial = "commercial"
    farming    = "farming"

class LicenseType(str, Enum):
    foreign    = "foreign"
    personal   = "personal"
    commercial = "commercial"

class LicenseStatus(str, Enum):
    valid     = "valid"
    suspended = "suspended"

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str   = Field(unique=True, index=True)
    zip_code: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str]     = None
    license_type: Optional[LicenseType]   = None
    license_status: Optional[LicenseStatus] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    messages: List["ChatMessage"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    vehicles: List["Vehicle"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    session: Optional["Session"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )

class ChatMessage(SQLModel, table=True):
    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int    = Field(foreign_key="users.id", index=True)
    role: str       = Field(nullable=False)  # 'user' or 'assistant'
    content: str    = Field(nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="messages")

class Vehicle(SQLModel, table=True):
    __tablename__ = "vehicles"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int      = Field(foreign_key="users.id", index=True)
    vin: Optional[str]       = None
    year: Optional[int]      = None
    make: Optional[str]      = None
    model: Optional[str]     = None
    body_type: Optional[str] = None
    vehicle_use: Optional[VehicleUse] = None
    blind_spot_warning: Optional[bool] = None
    days_per_week: Optional[int]      = None
    one_way_miles: Optional[float]    = None
    annual_mileage: Optional[int]     = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="vehicles")

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int      = Field(foreign_key="users.id", unique=True, index=True)
    current_state: str
    state_data: str = "{}"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(
        back_populates="session", sa_relationship_kwargs={"uselist": False}
    )
