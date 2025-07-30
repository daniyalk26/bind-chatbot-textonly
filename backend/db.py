# db.py
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os, asyncio

DATABASE_URL = os.getenv("DATABASE_URL")

print("🛠  DEBUG: Using DATABASE_URL =", DATABASE_URL)


engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ─── THE TWO FUNCTIONS main.py EXPECTS ──────────────────────────────
async def init_db() -> None:
    """Create tables at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:   # FastAPI dependency
    async with async_session() as session:
        yield session
