from typing import Dict, List, Optional


class AggregatedStats:
    """Maintains incremental statistics for profiled requests."""

    __slots__ = (
        "endpoints",
        "methods",
        "total_requests",
        "total_time",
        "max_time",
        "_response_buffer",
        "_buffer_size",
        "_buffer_idx",
        "_sorted_times",
        "_stats_cache",
    )

    def __init__(self, buffer_size: int = 10000):
        self.endpoints: Dict[str, Dict] = {}
        self.methods: Dict[str, int] = {}
        self.total_requests = 0
        self.total_time = 0.0
        self.max_time = 0.0

        # For percentile calculations - use fixed-size circular buffer
        self._buffer_size = buffer_size
        self._response_buffer = [0.0] * buffer_size  # Pre-allocate buffer
        self._buffer_idx = 0  # Current position in buffer
        self._sorted_times: Optional[List[float]] = None
        self._stats_cache = {}

    def update(self, profile: Dict):
        """Update statistics with a new profile."""
        # Update endpoint stats
        key = f"{profile['method']} {profile['path']}"
        if key not in self.endpoints:
            self.endpoints[key] = {
                "method": profile["method"],
                "path": profile["path"],
                "count": 0,
                "total": 0.0,
                "min": float("inf"),
                "max": 0.0,
                # Store only the last 100 response times per endpoint to save memory
                "response_times": [0.0] * 100,
                "rt_idx": 0,
            }

        endpoint = self.endpoints[key]
        time_value = profile["total_time"]

        endpoint["count"] += 1
        endpoint["total"] += time_value
        endpoint["min"] = min(endpoint["min"], time_value)
        endpoint["max"] = max(endpoint["max"], time_value)

        # Store response time in circular buffer
        rt_idx = endpoint.get("rt_idx", 0)
        endpoint["response_times"][rt_idx] = time_value
        endpoint["rt_idx"] = (rt_idx + 1) % 100

        # Update method stats
        method = profile["method"]
        if method not in self.methods:
            self.methods[method] = 0
        self.methods[method] += 1

        # Update overall stats
        self.total_requests += 1
        self.total_time += time_value
        self.max_time = max(self.max_time, time_value)

        # Add to response times circular buffer for percentile calculations
        self._response_buffer[self._buffer_idx] = time_value
        self._buffer_idx = (self._buffer_idx + 1) % self._buffer_size

        # Invalidate cached calculations
        self._sorted_times = None
        self._stats_cache = {}

    def get_percentile(self, percentile: float) -> float:
        """Calculate the specified percentile of response times."""
        # Get valid response times (non-zero values)
        valid_times = [t for t in self._response_buffer if t > 0]
        if not valid_times:
            return 0.0

        # Cache the sorted list for multiple percentile calculations
        if self._sorted_times is None:
            self._sorted_times = sorted(valid_times)

        # Calculate percentile index
        idx = int(len(self._sorted_times) * (percentile / 100))
        # Ensure index is within bounds
        idx = min(idx, len(self._sorted_times) - 1)
        return self._sorted_times[idx]

    def get_endpoint_stats(self) -> List[Dict]:
        """Get calculated endpoint statistics."""
        if "endpoint_stats" in self._stats_cache:
            return self._stats_cache["endpoint_stats"]

        result = []
        for key, stats in self.endpoints.items():
            result.append(
                {
                    "method": stats["method"],
                    "path": stats["path"],
                    "count": stats["count"],
                    "avg": stats["total"] / stats["count"],
                    "min": stats["min"],
                    "max": stats["max"],
                }
            )

        self._stats_cache["endpoint_stats"] = result
        return result

    def get_slowest_endpoints(self, limit: int = 5) -> List[Dict]:
        """Get the slowest endpoints by average response time."""
        if f"slowest_{limit}" in self._stats_cache:
            return self._stats_cache[f"slowest_{limit}"]

        stats = self.get_endpoint_stats()
        result = sorted(stats, key=lambda x: x["avg"], reverse=True)[:limit]

        self._stats_cache[f"slowest_{limit}"] = result
        return result

    def get_method_distribution(self) -> List[Dict]:
        """Get the distribution of requests by HTTP method."""
        if "method_distribution" in self._stats_cache:
            return self._stats_cache["method_distribution"]

        result = [
            {"method": method, "count": count} for method, count in self.methods.items()
        ]

        self._stats_cache["method_distribution"] = result
        return result

    def get_endpoint_distribution(self, limit: int = 10) -> List[Dict]:
        """Get the top endpoints by request count."""
        if f"endpoint_distribution_{limit}" in self._stats_cache:
            return self._stats_cache[f"endpoint_distribution_{limit}"]

        stats = self.get_endpoint_stats()
        result = sorted(stats, key=lambda x: x["count"], reverse=True)[:limit]

        self._stats_cache[f"endpoint_distribution_{limit}"] = result
        return result

    def get_avg_response_time(self) -> float:
        """Get the average response time across all requests."""
        if not self.total_requests:
            return 0.0
        return self.total_time / self.total_requests
