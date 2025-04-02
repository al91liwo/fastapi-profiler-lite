from collections import deque
from typing import Any, Deque, Dict, List

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_profiler.stats import AggregatedStats
from fastapi_profiler.utils import (
    RequestProfiler,
    current_profiler_ctx,
    generate_request_id,
)


class ProfilerMiddleware(BaseHTTPMiddleware):
    """Middleware to profile incoming requests."""

    def __init__(
        self, app: FastAPI, exclude_paths: List[str] = None, max_profiles: int = 500
    ):
        super().__init__(app)
        # Use circular buffer to store profiles
        self.profiles: Deque[Dict[str, Any]] = deque(maxlen=max_profiles)
        self.exclude_paths = exclude_paths or []

        # Aggregated statistics for efficient dashboard rendering
        self.stats = AggregatedStats()

    async def dispatch(self, request: Request, call_next):
        # Fast path: check if path should be excluded from profiling
        path = request.url.path
        for exclude in self.exclude_paths:
            if path.startswith(exclude):
                return await call_next(request)

        # Create profiler for this request
        request_id = generate_request_id()
        profiler = RequestProfiler(
            request_id=request_id, path=path, method=request.method
        )

        # Store profiler in context variable for this request
        token = current_profiler_ctx.set(profiler)

        try:
            # Process the request
            response = await call_next(request)

            # Record the status code
            profiler.set_status_code(response.status_code)
            return response

        except Exception as e:
            # Complete profiling even if there's an error
            profiler.set_status_code(500)  # Internal Server Error
            raise e

        finally:
            # Always complete profiling and store data regardless of success/failure
            profiler.complete()

            try:
                # Store minimal profile data without external calls to save memory
                profile_dict = profiler.to_dict(include_external=False)

                # Store profiling data (deque automatically handles the size limit)
                self.profiles.append(profile_dict)

                # Update aggregated statistics
                self.stats.update(profile_dict)
            except Exception as e:
                # Ensure any errors in profiling don't affect the application
                print(f"Error in profiler: {str(e)}")

            # Always reset the context variable to avoid leaks
            current_profiler_ctx.reset(token)
