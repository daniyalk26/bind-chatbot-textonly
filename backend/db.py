# backend/db.py
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@postgres:5432/bindiq_db")

print("🛠  DEBUG: Using DATABASE_URL =", DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ─── THE TWO FUNCTIONS main.py EXPECTS ──────────────────────────────
async def init_db() -> None:
    """Create tables at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables created")

async def get_session() -> AsyncGenerator[AsyncSession, None]:  # Fixed return type
    """FastAPI dependency"""
    async with async_session() as session:
        yield session