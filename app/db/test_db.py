from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for testing."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_test_db():
    """Initialize the test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_test_db():
    """Drop all tables in the test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) 