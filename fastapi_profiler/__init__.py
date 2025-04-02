from fastapi_profiler.profiler import Profiler
from fastapi_profiler.utils import add_external_call, get_current_profiler

__version__ = "0.2.1"
__all__ = ["Profiler", "get_current_profiler", "add_external_call"]
