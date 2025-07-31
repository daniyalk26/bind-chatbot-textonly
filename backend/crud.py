from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional, List
import json

from .models import User, ChatMessage, Vehicle, Session as SessionModel
from .schemas import ConversationState


async def get_or_create_user(db: AsyncSession, session_id: str) -> User:
    result = await db.execute(
        select(User).where(User.session_id == session_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(session_id=session_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # create initial session
        session = SessionModel(
            user_id=user.id,
            current_state=ConversationState.start.value,
            state_data="{}",
        )
        db.add(session)
        await db.commit()

    return user


async def save_message(
    db: AsyncSession, user_id: int, role: str, content: str
) -> ChatMessage:
    message = ChatMessage(user_id=user_id, role=role, content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_messages(db: AsyncSession, user_id: int) -> List[ChatMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.timestamp)
    )
    return result.scalars().all()


async def get_session(db: AsyncSession, user_id: int) -> Optional[SessionModel]:
    result = await db.execute(
        select(SessionModel).where(SessionModel.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_session_state(
    db: AsyncSession,
    user_id: int,
    state: str,
    state_data: Optional[dict] = None,
) -> SessionModel:
    session = await get_session(db, user_id)
    if session:
        session.current_state = state
        if state_data is not None:
            session.state_data = json.dumps(state_data)
        await db.commit()
        await db.refresh(session)
    return session


async def save_vehicle(
    db: AsyncSession, user_id: int, vehicle_data: dict
) -> Vehicle:
    vehicle = Vehicle(user_id=user_id, **vehicle_data)
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def update_user(db: AsyncSession, user_id: int, **kwargs) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user
