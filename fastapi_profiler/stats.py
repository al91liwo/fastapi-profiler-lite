import json
from typing import Dict, List

from rustcore import PyAggregatedStats


class AggregatedStats:
    """Maintains incremental statistics for profiled requests."""

    def __init__(self, buffer_size: int = 10000):
        self._impl = PyAggregatedStats(buffer_size)

    def update(self, profile: Dict):
        """Update statistics with a new profile."""
        self._impl.update(json.dumps(profile))

    def get_percentile(self, percentile: float) -> float:
        """Calculate the specified percentile of response times."""
        return self._impl.get_percentile(percentile)

    def get_endpoint_stats(self) -> List[Dict]:
        """Get calculated endpoint statistics."""
        return json.loads(self._impl.get_endpoint_stats())

    def get_slowest_endpoints(self, limit: int = 5) -> List[Dict]:
        """Get the slowest endpoints by average response time."""
        return json.loads(self._impl.get_slowest_endpoints(limit))

    def get_method_distribution(self) -> List[Dict]:
        """Get the distribution of requests by HTTP method."""
        return json.loads(self._impl.get_method_distribution())

    def get_endpoint_distribution(self, limit: int = 10) -> List[Dict]:
        """Get the top endpoints by request count."""
        return json.loads(self._impl.get_endpoint_distribution(limit))

    def get_avg_response_time(self) -> float:
        """Get the average response time across all requests."""
        return self._impl.get_avg_response_time()

    @property
    def total_requests(self) -> int:
        """Get the total number of requests."""
        return self._impl.get_total_requests()

    @property
    def max_time(self) -> float:
        """Get the maximum response time."""
        return self._impl.get_max_time()

    @property
    def endpoints(self) -> Dict:
        """Get the endpoints dictionary (compatibility property)."""
        # This is just for compatibility with code that might access this directly
        return {"__count__": self._impl.get_unique_endpoints()}
