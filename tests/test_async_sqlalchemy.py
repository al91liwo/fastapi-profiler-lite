import asyncio
import pytest
import sqlalchemy
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_profiler import Profiler
from fastapi_profiler.instrumentations.sqlalchemy import SQLAlchemyInstrumentation
from fastapi_profiler.utils import get_current_profiler, current_profiler_ctx


# Create a base model class
Base = declarative_base()


# Define a test model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)


@pytest.fixture(scope="function")
async def async_engine():
    """Create an async SQLAlchemy engine for testing."""
    # Use SQLite with aiosqlite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Add some test data
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        session.add(User(name="Test User"))
        await session.commit()

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()


@pytest.mark.asyncio
async def test_async_engine_instrumentation(app, async_engine):
    """Test that AsyncEngine can be instrumented properly."""
    # We need to await the async_engine fixture to get the actual engine
    engine = await anext(async_engine.__aiter__())

    # Make sure we have a proper AsyncEngine instance
    assert hasattr(engine, "sync_engine"), "Expected AsyncEngine instance"

    # Add engine to app state
    app.state.async_engine = engine

    # Initialize profiler
    profiler = Profiler(app)

    # Manually instrument the engine
    SQLAlchemyInstrumentation.instrument(engine)

    # Create a mock profiler for tracking
    from unittest.mock import MagicMock

    mock_profiler = MagicMock()
    token = current_profiler_ctx.set(mock_profiler)

    try:
        # Create a session and execute a query
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )

        async with async_session() as session:
            # Execute a simple query
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

            # Execute a query against the users table
            result = await session.execute(text("SELECT * FROM users"))
            users = result.all()
            assert len(users) > 0
    finally:
        # Reset the context
        current_profiler_ctx.reset(token)

    # Verify that add_db_query was called
    assert mock_profiler.add_db_query.called

    # Verify that the engine was properly instrumented
    # For AsyncEngine, we should have instrumented the sync_engine
    assert id(engine.sync_engine) in SQLAlchemyInstrumentation._instrumented_engines


@pytest.mark.asyncio
async def test_async_engine_with_fastapi(app, async_engine):
    """Test AsyncEngine instrumentation with FastAPI endpoints."""
    # We need to await the async_engine fixture to get the actual engine
    engine = await anext(async_engine.__aiter__())

    # Make sure we have a proper AsyncEngine instance
    assert hasattr(engine, "sync_engine"), "Expected AsyncEngine instance"

    # Add engine to app state
    app.state.async_engine = engine

    # Create an async session factory
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Add a dependency to get a session
    async def get_session():
        async with async_session() as session:
            yield session

    # Add a test endpoint
    @app.get("/users")
    async def get_users(session: AsyncSession = Depends(get_session)):
        result = await session.execute(text("SELECT * FROM users"))
        users = result.all()
        return {"count": len(users)}

    # Initialize profiler
    profiler = Profiler(app)

    # Manually instrument the engine
    SQLAlchemyInstrumentation.instrument(engine)

    # Test the endpoint
    client = TestClient(app)
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json()["count"] > 0

    # Check that we have profiles with database queries
    assert len(profiler.middleware.profiles) > 0

    # At least one profile should have db_queries
    has_db_queries = False
    for profile in profiler.middleware.profiles:
        if profile.get("db_queries"):
            has_db_queries = True
            break

    assert has_db_queries, "No database queries were tracked"
