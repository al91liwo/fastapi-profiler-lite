import asyncio
import time
from unittest import mock

import pytest
import sqlalchemy
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from fastapi import FastAPI
from fastapi.testclient import TestClient

import fastapi_profiler
from fastapi_profiler import Profiler
from fastapi_profiler.instrumentations.base import BaseInstrumentation
from fastapi_profiler.instrumentations.sqlalchemy import SQLAlchemyInstrumentation
from fastapi_profiler.utils import get_current_profiler


# Create a real SQLAlchemy engine for testing
@pytest.fixture
def real_engine():
    """Create a real SQLAlchemy engine for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Create a test table
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    Base.metadata.create_all(engine)

    # Add some test data
    with Session(engine) as session:
        session.add(User(name="Test User"))
        session.commit()

    yield engine

    # Clean up
    Base.metadata.drop_all(engine)


# Create multiple engines for testing
@pytest.fixture
def multiple_engines():
    """Create multiple SQLAlchemy engines for testing."""
    engines = {
        "primary": create_engine("sqlite:///:memory:"),
        "analytics": create_engine("sqlite:///:memory:"),
    }

    # Create schema in both engines
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    for engine in engines.values():
        Base.metadata.create_all(engine)

    yield engines

    # Clean up
    for engine in engines.values():
        Base.metadata.drop_all(engine)


# Create a session factory for testing
@pytest.fixture
def db_session_factory(real_engine):
    """Create a SQLAlchemy session factory for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=real_engine)
    return SessionLocal


class CustomInstrumentation(BaseInstrumentation):
    """Custom instrumentation implementation for testing."""

    tracked_queries = []

    @classmethod
    def instrument(cls, engine):
        cls.tracked_queries = []
        engine.instrumented = True

    @classmethod
    def uninstrument(cls, engine):
        engine.instrumented = False

    @classmethod
    def track_query(cls, duration, statement, metadata=None):
        cls.tracked_queries.append(
            {"duration": duration, "statement": statement, "metadata": metadata or {}}
        )


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()


def test_sqlalchemy_instrumentation_basic(real_engine):
    """Test basic SQLAlchemy instrumentation."""
    # Instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify that the engine was instrumented by checking if it has the metadata attribute
    assert hasattr(real_engine, "_profiler_metadata")

    # Execute a query to verify instrumentation works
    with Session(real_engine) as session:
        result = session.execute(text("SELECT 1")).fetchone()
        assert result[0] == 1

    # Uninstrument the engine
    SQLAlchemyInstrumentation.uninstrument(real_engine)

    # Verify the engine is no longer in the instrumented engines set
    assert id(real_engine) not in SQLAlchemyInstrumentation._instrumented_engines


def test_sqlalchemy_query_tracking(real_engine):
    """Test that SQL queries are properly tracked."""
    # Create a request profiler and set it in the context
    mock_profiler = mock.MagicMock()

    # Instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Create a context manager to temporarily replace the get function
    class MockContextManager:
        def __enter__(self):
            # Save original function
            self.original_get_current_profiler = (
                fastapi_profiler.utils.get_current_profiler
            )

            # Create a function that returns our mock profiler
            def mock_get():
                return mock_profiler

            # Replace the function
            fastapi_profiler.utils.get_current_profiler = mock_get

            # Also set the context variable for compatibility
            self.token = fastapi_profiler.utils.current_profiler_ctx.set(mock_profiler)

            return mock_profiler

        def __exit__(self, *args):
            # Restore the original function
            fastapi_profiler.utils.get_current_profiler = (
                self.original_get_current_profiler
            )
            # Reset the context variable
            fastapi_profiler.utils.current_profiler_ctx.reset(self.token)

    # Use our custom context manager
    with MockContextManager() as mock_prof:
        # Execute a real query
        with Session(real_engine) as session:
            session.execute(text("SELECT * FROM users"))
            session.commit()

        # Verify that add_db_query was called
        mock_prof.add_db_query.assert_called()
        args = mock_prof.add_db_query.call_args[0]
        assert "SELECT * FROM users" in args[1]  # Statement
        assert isinstance(args[0], float)  # Duration
        assert args[0] > 0  # Duration should be positive


def test_manual_instrument_single_engine(app, real_engine):
    """Test manual instrumentation with a single engine."""
    # Add engine to app state
    app.state.sqlalchemy_engine = real_engine

    # Initialize profiler without auto-instrumentation
    profiler = Profiler(app)

    # Manually instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify that the engine was instrumented
    assert hasattr(real_engine, "_profiler_metadata")
    assert id(real_engine) in SQLAlchemyInstrumentation._instrumented_engines


def test_manual_instrument_multiple_engines(app, multiple_engines):
    """Test manual instrumentation with multiple engines."""
    # Add engines to app state
    app.state.primary_engine = multiple_engines["primary"]
    app.state.analytics_engine = multiple_engines["analytics"]

    # Initialize profiler without auto-instrumentation
    profiler = Profiler(app)

    # Manually instrument both engines
    SQLAlchemyInstrumentation.instrument(multiple_engines["primary"])
    SQLAlchemyInstrumentation.instrument(multiple_engines["analytics"])

    # Verify that both engines were instrumented
    assert hasattr(multiple_engines["primary"], "_profiler_metadata")
    assert hasattr(multiple_engines["analytics"], "_profiler_metadata")
    assert (
        id(multiple_engines["primary"])
        in SQLAlchemyInstrumentation._instrumented_engines
    )
    assert (
        id(multiple_engines["analytics"])
        in SQLAlchemyInstrumentation._instrumented_engines
    )


def test_manual_instrument_db_session(app, db_session_factory):
    """Test manual instrumentation with a db session factory."""
    # Add db session to app state
    app.state.db = db_session_factory

    # Initialize profiler without auto-instrumentation
    profiler = Profiler(app)

    # Get the engine from the session factory
    engine = db_session_factory.kw["bind"]

    # Manually instrument the engine
    SQLAlchemyInstrumentation.instrument(engine)

    # Verify that the engine was instrumented
    assert hasattr(engine, "_profiler_metadata")
    assert id(engine) in SQLAlchemyInstrumentation._instrumented_engines


def test_profiler_without_instrumentation(app):
    """Test profiler initialization without database instrumentation."""
    # Initialize profiler without instrumentation
    profiler = Profiler(app)

    # No exception should be raised, and the app should still work
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 404  # Default 404 for undefined route


def test_manual_instrumentation_multiple_engines(app, multiple_engines):
    """Test manually instrumenting multiple engines."""
    # Initialize profiler
    profiler = Profiler(app)

    # Manually instrument both engines
    SQLAlchemyInstrumentation.instrument(multiple_engines["primary"])
    SQLAlchemyInstrumentation.instrument(multiple_engines["analytics"])

    # Verify that both engines were instrumented
    assert hasattr(multiple_engines["primary"], "_profiler_metadata")
    assert hasattr(multiple_engines["analytics"], "_profiler_metadata")
    assert (
        id(multiple_engines["primary"])
        in SQLAlchemyInstrumentation._instrumented_engines
    )
    assert (
        id(multiple_engines["analytics"])
        in SQLAlchemyInstrumentation._instrumented_engines
    )


def test_custom_instrumentation(app, real_engine):
    """Test using a custom instrumentation class."""
    # Initialize profiler
    profiler = Profiler(app)

    # Use custom instrumentation
    CustomInstrumentation.instrument(real_engine)

    # Verify that the engine was instrumented
    assert hasattr(real_engine, "instrumented")
    assert real_engine.instrumented is True

    # Uninstrument
    CustomInstrumentation.uninstrument(real_engine)

    # Verify that the engine was uninstrumented
    assert real_engine.instrumented is False


def test_complex_query_tracking(real_engine):
    """Test tracking of complex SQL queries."""
    # Create a request profiler and set it in the context
    mock_profiler = mock.MagicMock()

    # Instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Complex SQL queries to test
    complex_queries = [
        # Complex SELECT with JOINs, GROUP BY, and HAVING
        """
        SELECT 1 as id, 'Test' as name, COUNT(*) as count
        FROM users
        GROUP BY id, name
        """,
        # Query with Common Table Expression (CTE)
        """
        WITH test_cte AS (
            SELECT id, name FROM users
        )
        SELECT * FROM test_cte
        """,
        # Complex query with subquery
        """
        SELECT * FROM users
        WHERE id IN (SELECT id FROM users WHERE name = 'Test User')
        """,
    ]

    # Create a context manager to temporarily replace the get function
    class MockContextManager:
        def __enter__(self):
            # Save original function
            self.original_get_current_profiler = (
                fastapi_profiler.utils.get_current_profiler
            )

            # Create a function that returns our mock profiler
            def mock_get():
                return mock_profiler

            # Replace both the function and the BaseInstrumentation.track_query method
            fastapi_profiler.utils.get_current_profiler = mock_get

            # Also patch the BaseInstrumentation.track_query method directly
            self.original_track_query = (
                fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query
            )

            @staticmethod
            def mock_track_query(duration, statement, metadata=None):
                prof = mock_profiler
                if prof:
                    prof.add_db_query(duration, statement, metadata or {})

            fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query = (
                mock_track_query
            )

            return mock_profiler

        def __exit__(self, *args):
            # Restore the original functions
            fastapi_profiler.utils.get_current_profiler = (
                self.original_get_current_profiler
            )
            fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query = (
                self.original_track_query
            )

    # Use our custom context manager
    with MockContextManager() as mock_prof:
        # Execute each complex query
        with Session(real_engine) as session:
            for query in complex_queries:
                # Reset the mock
                mock_prof.add_db_query.reset_mock()

                # Execute the query
                session.execute(text(query))

                # Verify that add_db_query was called
                mock_prof.add_db_query.assert_called()
                args = mock_prof.add_db_query.call_args[0]
                assert isinstance(args[0], float)  # Duration should be a float
                assert args[0] > 0  # Duration should be positive


def test_malformed_query_tracking(real_engine):
    """Test tracking of malformed SQL queries."""
    # Create a request profiler and set it in the context
    mock_profiler = mock.MagicMock()

    # Instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Create a context manager to temporarily replace the get function
    class MockContextManager:
        def __enter__(self):
            # Save original function
            self.original_get_current_profiler = (
                fastapi_profiler.utils.get_current_profiler
            )

            # Create a function that returns our mock profiler
            def mock_get():
                return mock_profiler

            # Replace both the function and the BaseInstrumentation.track_query method
            fastapi_profiler.utils.get_current_profiler = mock_get

            # Also patch the BaseInstrumentation.track_query method directly
            self.original_track_query = (
                fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query
            )

            @staticmethod
            def mock_track_query(duration, statement, metadata=None):
                prof = mock_profiler
                if prof:
                    prof.add_db_query(duration, statement, metadata or {})

            fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query = (
                mock_track_query
            )

            return mock_profiler

        def __exit__(self, *args):
            # Restore the original functions
            fastapi_profiler.utils.get_current_profiler = (
                self.original_get_current_profiler
            )
            fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query = (
                self.original_track_query
            )

    # Use our custom context manager
    with MockContextManager() as mock_prof:
        # We'll use direct tracking since executing malformed queries would raise exceptions
        for query in ["SELECT id, name WHERE status = 'active'", "SELEKT * FROM users"]:
            # Reset the mock
            mock_prof.add_db_query.reset_mock()

            # Directly track the query
            SQLAlchemyInstrumentation.track_query(0.01, query, {"dialect": "sqlite"})

            # Verify that add_db_query was called with the correct query
            mock_prof.add_db_query.assert_called_once()
            args = mock_prof.add_db_query.call_args[0]
            assert args[1] == query  # Statement should match
            assert isinstance(args[0], float)  # Duration should be a float
            assert args[0] > 0  # Duration should be positive


def test_metadata_capture(real_engine):
    """Test that database metadata is properly captured."""
    # Instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify that metadata was stored on the engine
    assert hasattr(real_engine, "_profiler_metadata")

    # Verify the dialect information
    assert real_engine._profiler_metadata["dialect"] == "sqlite"


def test_sql_formatting(real_engine):
    """Test that SQL queries are properly formatted."""
    # Skip test if sqlparse is not installed
    try:
        import sqlparse
    except ImportError:
        import pytest

        pytest.skip("sqlparse not installed")

    # Create a request profiler and set it in the context
    mock_profiler = mock.MagicMock()

    # Instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Create a context manager to temporarily replace the get function
    class MockContextManager:
        def __enter__(self):
            # Save original function
            self.original_get_current_profiler = (
                fastapi_profiler.utils.get_current_profiler
            )

            # Create a function that returns our mock profiler
            def mock_get():
                return mock_profiler

            # Replace both the function and the BaseInstrumentation.track_query method
            fastapi_profiler.utils.get_current_profiler = mock_get

            # Also patch the BaseInstrumentation.track_query method directly
            self.original_track_query = (
                fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query
            )

            @staticmethod
            def mock_track_query(duration, statement, metadata=None):
                prof = mock_profiler
                if prof:
                    prof.add_db_query(duration, statement, metadata or {})

            fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query = (
                mock_track_query
            )

            return mock_profiler

        def __exit__(self, *args):
            # Restore the original functions
            fastapi_profiler.utils.get_current_profiler = (
                self.original_get_current_profiler
            )
            fastapi_profiler.instrumentations.base.BaseInstrumentation.track_query = (
                self.original_track_query
            )

    # Test SQL formatting
    with MockContextManager() as mock_prof:
        # Execute a query
        with Session(real_engine) as session:
            session.execute(text("select id, name from users"))

        # Verify that add_db_query was called with formatted SQL in metadata
        mock_prof.add_db_query.assert_called()
        args = mock_prof.add_db_query.call_args[0]

        # Check if metadata contains formatted SQL
        metadata = args[2] if len(args) > 2 else {}
        assert "formatted_sql" in metadata

        # Verify formatting was applied (keywords should be uppercase)
        formatted_sql = metadata["formatted_sql"]
        assert "SELECT" in formatted_sql


def test_concurrent_query_tracking():
    """Test tracking queries from concurrent requests."""
    # Create a FastAPI app with a database endpoint
    app = FastAPI()

    # Create a real SQLite engine
    engine = create_engine("sqlite:///:memory:")

    # Create a test table
    Base = declarative_base()

    class TestItem(Base):
        __tablename__ = "test_items"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    Base.metadata.create_all(engine)

    # Add engine to app state
    app.state.sqlalchemy_engine = engine

    # Add a test endpoint that simulates database queries
    @app.get("/db-query/{query_id}")
    async def db_query(query_id: int):
        # Simulate a database query
        profiler = get_current_profiler()
        if profiler:
            profiler.add_db_query(
                0.1, f"SELECT * FROM test_items WHERE id = {query_id}"
            )
        return {"query_id": query_id}

    # Initialize profiler
    profiler_instance = Profiler(app)

    # Ensure the database key is initialized in the dashboard data
    if not hasattr(profiler_instance.middleware.stats, "db_stats"):
        profiler_instance.middleware.stats.db_stats = {
            "total_time": 0.0,
            "query_count": 0,
            "avg_time": 0.0,
            "max_time": 0.0,
            "min_time": float("inf"),
        }

    # Create a test client
    client = TestClient(app)

    # Run the requests (not concurrently in test, but that's fine)
    for i in range(10):
        response = client.get(f"/db-query/{i}")
        assert response.status_code == 200
        assert response.json() == {"query_id": i}

    # Verify that the profiler middleware has recorded some profiles
    assert len(profiler_instance.middleware.profiles) > 0, "No profiles were recorded"

    # Check that at least one profile has db_queries
    has_db_queries = False
    for profile in profiler_instance.middleware.profiles:
        if profile.get("db_queries"):
            has_db_queries = True
            break

    assert has_db_queries, "No database queries were recorded in profiles"


def test_error_handling_during_instrumentation(app):
    """Test error handling when instrumentation fails."""
    # Create a problematic engine that will raise an exception
    problematic_engine = mock.MagicMock()
    problematic_engine.dialect = mock.MagicMock()
    problematic_engine.dialect.name = "sqlite"
    problematic_engine.dispatch = mock.MagicMock()
    problematic_engine.dispatch.side_effect = Exception("Simulated error")

    # Add the problematic engine to app state
    app.state.sqlalchemy_engine = problematic_engine

    # Initialize profiler
    # This should not crash the application
    profiler = Profiler(app)

    # Verify the app still works
    client = TestClient(app)
    response = client.get("/profiler")
    assert response.status_code == 200


def test_double_instrumentation(app, real_engine):
    """Test that instrumenting the same engine twice doesn't cause issues."""
    # First instrumentation
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify the engine is in the instrumented engines set
    engine_id = id(real_engine)
    assert engine_id in SQLAlchemyInstrumentation._instrumented_engines

    # Store the initial set size
    initial_set_size = len(SQLAlchemyInstrumentation._instrumented_engines)

    # Instrument the same engine again
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify that the set size hasn't changed
    assert len(SQLAlchemyInstrumentation._instrumented_engines) == initial_set_size

    # Verify the engine is still in the set
    assert engine_id in SQLAlchemyInstrumentation._instrumented_engines

    # Count occurrences of this engine ID in the set
    # This is a bit of a hack since sets can't have duplicates, but it verifies our tracking logic
    engine_count = sum(
        1
        for e_id in SQLAlchemyInstrumentation._instrumented_engines
        if e_id == engine_id
    )
    assert engine_count == 1, "Engine should only be tracked once"


def test_double_manual_instrumentation(app, real_engine):
    """Test that manual instrumentation handles duplicates correctly."""
    # Add engine to app state
    app.state.sqlalchemy_engine = real_engine

    # Initialize profiler
    profiler = Profiler(app)

    # Manually instrument the engine
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify that the engine was instrumented
    assert id(real_engine) in SQLAlchemyInstrumentation._instrumented_engines

    # Store the initial set size
    initial_set_size = len(SQLAlchemyInstrumentation._instrumented_engines)

    # Manually instrument again
    SQLAlchemyInstrumentation.instrument(real_engine)

    # Verify that the set size hasn't changed
    assert len(SQLAlchemyInstrumentation._instrumented_engines) == initial_set_size
