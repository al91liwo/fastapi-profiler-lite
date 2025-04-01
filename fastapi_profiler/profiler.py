import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRouter
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_profiler.dashboard import generate_dashboard_html


class RequestProfiler:
    """Tracks performance metrics for a single request.

    This class is responsible for capturing timing and other performance
    data for a single HTTP request. It's instantiated by the middleware
    for each incoming request that isn't excluded.

    Attributes:
        request_id: Unique identifier for the request
        path: The URL path of the request
        method: The HTTP method (GET, POST, etc.)
        start_time: When the request processing started (perf_counter)
        timestamp: Unix timestamp for frontend display
        end_time: When the request processing completed (perf_counter)
        total_time: Total processing time in seconds
        status_code: HTTP status code of the response
        db_queries: List of database queries made during the request
        external_calls: List of external API calls made during the request
    """

    def __init__(self, request_id: str, path: str, method: str):
        self.request_id = request_id
        self.path = path
        self.method = method
        self.start_time = time.perf_counter()
        self.timestamp = time.time()  # Unix timestamp for frontend
        self.end_time: Optional[float] = None
        self.total_time: Optional[float] = None
        self.status_code: Optional[int] = None

        # Performance data
        self.external_calls: List[Dict[str, Any]] = []

    def set_status_code(self, status_code: int) -> None:
        """Set the response status code."""
        self.status_code = status_code

    def complete(self) -> None:
        """Mark the request as complete and calculate total time."""
        self.end_time = time.perf_counter()
        self.total_time = self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert profiler data to a dictionary.

        Returns:
            Dict containing all the profiling data for this request.
        """
        return {
            "request_id": self.request_id,
            "path": self.path,
            "method": self.method,
            "start_time": self.timestamp,
            "end_time": self.end_time
            and self.timestamp + (self.end_time - self.start_time),
            "total_time": self.total_time,
            "status_code": self.status_code,
            "external_calls": self.external_calls,
            "external_call_count": len(self.external_calls),
        }

    # Methods to track additional metrics
    def add_external_call(self, url: str, method: str, duration: float) -> None:
        """Add an external API call to the profile.

        Args:
            url: URL of the external API
            method: HTTP method used
            duration: Call execution time in seconds
        """
        self.external_calls.append({"url": url, "method": method, "duration": duration})


class ProfilerMiddleware(BaseHTTPMiddleware):
    """Middleware to profile incoming requests.

    This middleware intercepts all incoming requests, creates a RequestProfiler
    instance for each one, and stores the profiling data.

    Attributes:
        profiles: List of profile data dictionaries
        exclude_paths: List of URL paths to exclude from profiling
    """

    def __init__(
        self, app: FastAPI, exclude_paths: List[str] = None, max_profiles: int = 500
    ):
        super().__init__(app)
        self.profiles: Deque[Dict[str, Any]] = deque(maxlen=max_profiles)
        self.exclude_paths = exclude_paths or []
        self.current_profiler = None

    async def dispatch(self, request: Request, call_next):
        # Check if path should be excluded from profiling
        for exclude in self.exclude_paths:
            if request.url.path.startswith(exclude):
                return await call_next(request)

        # Create profiler for this request
        request_id = str(uuid.uuid4())
        profiler = RequestProfiler(
            request_id=request_id, path=request.url.path, method=request.method
        )

        try:
            # Process the request
            response = await call_next(request)

            # Record the status code
            profiler.set_status_code(response.status_code)

            # Complete profiling
            profiler.complete()

            # Store the current profiler for potential access by extensions
            self.current_profiler = profiler

            # Store profiling data (deque automatically handles the size limit)
            self.profiles.append(profiler.to_dict())

            return response

        except Exception:
            # Complete profiling even if there's an error
            profiler.set_status_code(500)  # Internal Server Error
            profiler.complete()

            # Store profiling data for failed requests too
            self.profiles.append(profiler.to_dict())

            # Clear the current profiler reference
            self.current_profiler = None

            # Re raise the exception
            raise


class Profiler:
    """Main profiler class for FastAPI applications.

    This is the main class that users interact with. It sets up the middleware
    and routes for the profiler dashboard.

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_profiler import Profiler

        app = FastAPI()
        Profiler(app)
        ```

    Attributes:
        app: The FastAPI application instance
        dashboard_path: URL path where the dashboard will be served
        enabled: Whether the profiler is enabled
        middleware: Instance of ProfilerMiddleware
        exclude_paths: List of URL paths to exclude from profiling
    """

    def __init__(
        self,
        app: FastAPI,
        dashboard_path: str = "/profiler",
        enabled: bool = True,
        exclude_paths: List[str] = None,
    ):
        self.app = app
        self.dashboard_path = dashboard_path
        self.enabled = enabled
        self.middleware = None
        self.exclude_paths = exclude_paths or []

        # Always exclude the dashboard path from profiling
        if dashboard_path not in self.exclude_paths:
            self.exclude_paths.append(dashboard_path)

        if enabled:
            self._setup_middleware()
            self._setup_routes()

    def _setup_middleware(self):
        """Add profiler middleware to the FastAPI app."""
        self.middleware = ProfilerMiddleware(self.app, exclude_paths=self.exclude_paths)
        # Use the middleware instance directly instead of creating a new one
        self.app.add_middleware(BaseHTTPMiddleware, dispatch=self.middleware.dispatch)

        # Store middleware in app state for extensions like SQLAlchemy integration
        if not hasattr(self.app, "state"):
            self.app.state = type("AppState", (), {})()
        self.app.state.profiler_middleware = self.middleware

    def _setup_routes(self):
        """Add dashboard routes to the FastAPI app.

        This method sets up the following routes:
        - {dashboard_path} - The main dashboard UI
        - {dashboard_path}/api/profiles - API endpoint for profile data
        - {dashboard_path}/api/profile/{profile_id} - API endpoint for specific profile
        - {dashboard_path}/static/* - Static files for the dashboard
        """
        from pathlib import Path

        from fastapi.staticfiles import StaticFiles

        router = APIRouter()

        # Serve the dashboard HTML
        @router.get("")
        async def dashboard():
            """Serve the profiler dashboard."""
            html_content = generate_dashboard_html(dashboard_path=self.dashboard_path)
            return HTMLResponse(content=html_content)

        # API endpoints
        @router.get("/api/profiles")
        async def get_profiles():
            """Return recent profile data as JSON."""
            return self.middleware.profiles if self.middleware else []

        @router.get("/api/dashboard-data")
        async def get_dashboard_data():
            """Return pre-calculated data for the dashboard."""
            if not self.middleware or not self.middleware.profiles:
                return {
                    "timestamp": time.time(),
                    "overview": {
                        "total_requests": 0,
                        "avg_response_time": 0,
                        "max_response_time": 0,
                        "unique_endpoints": 0,
                    },
                    "time_series": {"response_times": []},
                    "endpoints": {"stats": [], "distribution": []},
                    "requests": {"recent": []},
                }

            profiles = list(self.middleware.profiles)

            # Calculate overview stats
            total_requests = len(profiles)
            avg_time = (
                sum(p["total_time"] for p in profiles) / total_requests
                if total_requests
                else 0
            )
            max_time = max(p["total_time"] for p in profiles) if profiles else 0
            unique_endpoints = len(
                set((p["method"] + " " + p["path"]) for p in profiles)
            )

            # Calculate endpoint stats
            endpoint_map = {}
            for profile in profiles:
                key = profile["method"] + " " + profile["path"]
                if key not in endpoint_map:
                    endpoint_map[key] = {
                        "method": profile["method"],
                        "path": profile["path"],
                        "count": 0,
                        "total": 0,
                        "min": float("inf"),
                        "max": 0,
                    }

                stats = endpoint_map[key]
                stats["count"] += 1
                stats["total"] += profile["total_time"]
                stats["min"] = min(stats["min"], profile["total_time"])
                stats["max"] = max(stats["max"], profile["total_time"])

            endpoint_stats = []
            for stats in endpoint_map.values():
                endpoint_stats.append(
                    {
                        "method": stats["method"],
                        "path": stats["path"],
                        "count": stats["count"],
                        "avg": stats["total"] / stats["count"],
                        "min": stats["min"],
                        "max": stats["max"],
                    }
                )

            # Sort by average time for slowest endpoints
            slowest_endpoints = sorted(
                endpoint_stats, key=lambda x: x["avg"], reverse=True
            )

            # Prepare time series data
            sorted_profiles = sorted(profiles, key=lambda p: p["start_time"])
            response_times = [
                {
                    "timestamp": p["start_time"],
                    "value": p["total_time"] * 1000,  # Convert to ms
                    "key": p["method"] + " " + p["path"],
                }
                for p in sorted_profiles
            ]

            # Count requests by method
            method_counts = {}
            for profile in profiles:
                method = profile["method"]
                if method not in method_counts:
                    method_counts[method] = 0
                method_counts[method] += 1

            method_distribution = [
                {"method": method, "count": count}
                for method, count in method_counts.items()
            ]

            # Endpoint distribution (top 10 by count)
            endpoint_distribution = sorted(
                endpoint_stats, key=lambda x: x["count"], reverse=True
            )[:10]

            # Recent requests (last 100)
            recent_requests = sorted(
                profiles, key=lambda p: p["start_time"], reverse=True
            )[:100]

            return {
                "timestamp": time.time(),
                "overview": {
                    "total_requests": total_requests,
                    "avg_response_time": avg_time * 1000,  # Convert to ms
                    "max_response_time": max_time * 1000,  # Convert to ms
                    "unique_endpoints": unique_endpoints,
                },
                "time_series": {"response_times": response_times},
                "endpoints": {
                    "stats": endpoint_stats,
                    "slowest": slowest_endpoints[:5],
                    "distribution": endpoint_distribution,
                    "by_method": method_distribution,
                },
                "requests": {"recent": recent_requests},
            }

        @router.get("/api/profile/{profile_id}")
        async def get_profile(profile_id: str):
            """Return a specific profile by ID."""
            if self.middleware:
                for profile in self.middleware.profiles:
                    if profile["request_id"] == profile_id:
                        return profile
            return JSONResponse(
                status_code=404, content={"detail": f"Profile {profile_id} not found"}
            )

        # Include the router
        self.app.include_router(router, prefix=self.dashboard_path)

        # Mount static files directory
        static_dir = Path(__file__).parent / "static"
        self.app.mount(
            f"{self.dashboard_path}/static",
            StaticFiles(directory=static_dir),
            name="profiler_static",
        )
