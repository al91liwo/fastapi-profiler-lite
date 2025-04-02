import time
from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_profiler.middleware import ProfilerMiddleware
from fastapi_profiler.utils import get_current_profiler


class Profiler:
    """Main profiler class for FastAPI applications."""

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
        self.dashboard_template = self._load_template()

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

        # Add the get_current_profiler function to app state for easy access
        self.app.state.get_current_profiler = get_current_profiler

    def _load_template(self):
        """Load the dashboard HTML template once during initialization."""
        template_path = (
            Path(__file__).parent / "static" / "templates" / "dashboard.html"
        )
        with open(template_path) as f:
            template = f.read()

        # Pre-render the template
        return (
            template.replace(
                "{{css_path}}", f"{self.dashboard_path}/static/css/styles.css"
            )
            .replace("{{js_path}}", f"{self.dashboard_path}/static/js/dashboard.js")
            .replace("{{dashboard_path}}", self.dashboard_path)
        )

    def _render_dashboard(self):
        """Return the pre-rendered dashboard HTML."""
        return self.dashboard_template

    def _setup_routes(self):
        """Add dashboard routes to the FastAPI app."""
        router = APIRouter()

        # Serve the dashboard HTML (using preloaded template)
        @router.get("")
        async def dashboard():
            """Serve the profiler dashboard."""
            return HTMLResponse(content=self.dashboard_template)

        # API endpoints
        @router.get("/api/profiles")
        async def get_profiles():
            """Return recent profile data as JSON."""
            return self.middleware.profiles if self.middleware else []

        @router.get("/api/dashboard-data")
        async def get_dashboard_data():
            """Return pre-calculated data for the dashboard."""
            try:
                if not self.middleware or not self.middleware.profiles:
                    return {
                        "timestamp": time.time(),
                        "overview": {
                            "total_requests": 0,
                            "avg_response_time": 0,
                            "max_response_time": 0,
                            "p90_response_time": 0,
                            "p95_response_time": 0,
                            "unique_endpoints": 0,
                        },
                        "time_series": {"response_times": []},
                        "endpoints": {
                            "stats": [],
                            "distribution": [],
                            "slowest": [],
                            "by_method": [],
                        },
                        "requests": {"recent": []},
                    }

                # Get pre-aggregated stats
                stats = self.middleware.stats

                # Get raw profiles for time series and recent requests
                profiles = list(self.middleware.profiles)

                # Prepare time series data
                sorted_profiles = sorted(profiles, key=lambda p: p["start_time"])
                response_times = [
                    {
                        "timestamp": p["start_time"],
                        "value": p["total_time"] * 1000,  # Convert to ms
                        "key": p["method"] + " " + p["path"],
                    }
                    for p in sorted_profiles
                    if p.get("total_time") is not None
                ]

                # Recent requests (last 100)
                recent_requests = sorted(
                    [p for p in profiles if p.get("total_time") is not None],
                    key=lambda p: p["start_time"],
                    reverse=True,
                )[:100]

                # Get endpoint stats from aggregated data
                endpoint_stats = stats.get_endpoint_stats()

                return {
                    "timestamp": time.time(),
                    "overview": {
                        "total_requests": stats.total_requests,
                        "avg_response_time": stats.get_avg_response_time()
                        * 1000,  # Convert to ms
                        "max_response_time": stats.max_time * 1000,  # Convert to ms
                        "p90_response_time": stats.get_percentile(90)
                        * 1000,  # 90th percentile
                        "p95_response_time": stats.get_percentile(95)
                        * 1000,  # 95th percentile
                        "unique_endpoints": len(stats.endpoints),
                    },
                    "time_series": {"response_times": response_times},
                    "endpoints": {
                        "stats": endpoint_stats,
                        "slowest": stats.get_slowest_endpoints(5),
                        "distribution": stats.get_endpoint_distribution(10),
                        "by_method": stats.get_method_distribution(),
                    },
                    "requests": {"recent": recent_requests},
                }
            except Exception as e:
                print(f"Error generating dashboard data: {str(e)}")
                # Return minimal data structure to prevent dashboard errors
                return {
                    "timestamp": time.time(),
                    "overview": {
                        "total_requests": 0,
                        "avg_response_time": 0,
                        "max_response_time": 0,
                        "p90_response_time": 0,
                        "p95_response_time": 0,
                        "unique_endpoints": 0,
                    },
                    "time_series": {"response_times": []},
                    "endpoints": {
                        "stats": [],
                        "distribution": [],
                        "slowest": [],
                        "by_method": [],
                    },
                    "requests": {"recent": []},
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
