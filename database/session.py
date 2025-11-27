"""
Async database session management with SQLAlchemy and asyncpg.
Provides connection pooling, dependency injection, and automatic session lifecycle.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from loguru import logger

from config import get_settings

settings = get_settings()

# Build async connection string for asyncpg
# Format: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.database.user}:{settings.database.password}"
    f"@{settings.database.host}:{settings.database.port}/{settings.database.database}"
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.logging.level == "DEBUG",  # Log all SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using (handles stale connections)
    pool_size=20,  # Maximum number of connections to keep in pool
    max_overflow=10,  # Additional connections beyond pool_size during high load
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
    future=True,  # Use SQLAlchemy 2.0 style
)

# Session factory for creating async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (better for APIs)
    autoflush=False,  # Manual control over when to flush
    autocommit=False,  # Transactions must be explicit
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI route handlers.
    Creates async session, yields it, and ensures cleanup.

    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session for the request

    Notes:
        - Session is automatically committed on success
        - Session is rolled back on exception
        - Session is always closed after request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit if no exception
        except Exception as e:
            await session.rollback()  # Rollback on any error
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables defined in models.
    Should be called on application startup.

    Note:
        In production, use Alembic migrations instead of create_all.
    """
    from database.models import Base
    
    async with engine.begin() as conn:
        # Create all tables (only for dev/testing)
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """
    Cleanup database connections on application shutdown.
    Should be called on application shutdown event.
    """
    await engine.dispose()
    logger.info("Database connections closed")
