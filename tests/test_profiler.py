from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_profiler import Profiler


def test_profiler_initialization():
    """Test that the profiler can be initialized."""
    app = FastAPI()
    profiler = Profiler(app)
    assert profiler.enabled is True
    assert profiler.dashboard_path == "/profiler"


def test_dashboard_endpoint():
    """Test that the dashboard endpoint returns HTML."""
    app = FastAPI()
    Profiler(app)

    client = TestClient(app)
    response = client.get("/profiler")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "FastAPI Profiler" in response.text


def test_api_endpoint():
    """Test that the API endpoint returns JSON."""
    app = FastAPI()
    Profiler(app)

    client = TestClient(app)
    response = client.get("/profiler/api/profiles")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert isinstance(response.json(), list)


def test_exclude_paths():
    """Test that excluded paths are not profiled."""
    app = FastAPI()

    @app.get("/excluded")
    def excluded_route():
        return {"message": "This route should be excluded"}

    @app.get("/included")
    def included_route():
        return {"message": "This route should be included"}

    Profiler(app, exclude_paths=["/excluded"])

    client = TestClient(app)
    client.get("/excluded")
    client.get("/included")

    response = client.get("/profiler/api/profiles")
    profiles = response.json()

    # Check that only the included path is in the profiles
    paths = [profile["path"] for profile in profiles]
    assert "/included" in paths
    assert "/excluded" not in paths


def test_disabled_profiler():
    """Test that disabled profiler doesn't add routes."""
    app = FastAPI()
    Profiler(app, enabled=False)

    client = TestClient(app)
    response = client.get("/profiler")

    # Dashboard should not be available
    assert response.status_code == 404


def test_context_isolation():
    """Test that the context isolation works correctly."""
    import asyncio

    from fastapi_profiler.utils import (
        RequestProfiler,
        current_profiler_ctx,
        get_current_profiler,
    )

    async def task1():
        # Create and set a profiler in this task's context
        profiler1 = RequestProfiler(request_id="task1", path="/test1", method="GET")
        token1 = current_profiler_ctx.set(profiler1)

        # Should get the profiler we just set
        assert get_current_profiler() == profiler1

        # Create a subtask with its own context
        task2_result = await task2()

        # Our context should still have our profiler
        assert get_current_profiler() == profiler1

        # Clean up
        current_profiler_ctx.reset(token1)
        return task2_result

    async def task2():
        # This task should have its own isolated context
        profiler2 = RequestProfiler(request_id="task2", path="/test2", method="GET")
        token2 = current_profiler_ctx.set(profiler2)

        # Should get the profiler we just set
        assert get_current_profiler() == profiler2

        # Clean up
        current_profiler_ctx.reset(token2)
        return profiler2.request_id

    # Run the test
    task2_id = asyncio.run(task1())
    assert task2_id == "task2"
