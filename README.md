# FastAPI Profiler Lite

<p align="center">
  <img src="https://github.com/al91liwo/fastapi-profiler/raw/main/docs/images/logo.png" alt="FastAPI Profiler Lite Logo" width="150"/>
</p>

<p align="center">
  <a href="https://pypi.org/project/fastapi-profiler-lite/"><img src="https://img.shields.io/pypi/v/fastapi-profiler-lite?color=blue" alt="PyPI version"></a>
  <a href="https://github.com/al91liwo/fastapi-profiler/blob/main/LICENSE"><img src="https://img.shields.io/github/license/al91liwo/fastapi-profiler" alt="License"></a>
  <a href="https://github.com/al91liwo/fastapi-profiler/stargazers"><img src="https://img.shields.io/github/stars/al91liwo/fastapi-profiler" alt="GitHub stars"></a>
  <a href="https://github.com/al91liwo/fastapi-profiler/actions/workflows/python-package.yml"><img src="https://github.com/al91liwo/fastapi-profiler/actions/workflows/python-package.yml/badge.svg" alt="CI Status"></a>
  <a href="https://github.com/al91liwo/fastapi-profiler/actions/workflows/release.yml"><img src="https://github.com/al91liwo/fastapi-profiler/actions/workflows/release.yml/badge.svg" alt="Release Status"></a>
</p>

A lightweight, zero-configuration performance profiler for FastAPI applications. Monitor your API performance in real-time without external dependencies.

<p align="center">
  <img src="https://github.com/al91liwo/fastapi-profiler/raw/main/docs/images/dashboard-demo.gif" alt="Dashboard Demo" width="800"/>
</p>

## Why FastAPI Profiler?

Monitoring API performance shouldn't require complex setups or external services. FastAPI Profiler gives you instant visibility into your application's performance with just one line of code.

- **Instant insights** - See which endpoints are slow without complex instrumentation
- **Zero configuration** - Works out of the box with sensible defaults
- **No external dependencies** - Everything runs within your FastAPI app
- **Developer-friendly** - Designed for both development and lightweight production use

## Installation

```bash
pip install fastapi-profiler-lite
```

For more installation options, see the [Installation Guide](docs/installation.md).

## Quick Start

```python
from fastapi import FastAPI
from fastapi_profiler import Profiler

app = FastAPI()

# Add the profiler with just one line
Profiler(app)

@app.get("/")
async def read_root():
    return {"Hello": "World"}
```

That's it! Visit `/profiler` to see the performance dashboard.

## Features

- **One-line integration** - Add to any FastAPI app with minimal code
- **Real-time dashboard** - Live updates with automatic refresh
- **Response time tracking** - Measure execution time of each request
- **Endpoint analysis** - Identify your slowest and most used endpoints
- **Request filtering** - Search and sort through captured requests
- **Visual metrics** - Charts for response times and request distribution
- **Minimal overhead** - Designed to have low performance impact

## Documentation

- [Installation](https://github.com/al91liwo/fastapi-profiler/blob/main/docs/installation.md)
- [Configuration](https://github.com/al91liwo/fastapi-profiler/blob/main/docs/configuration.md)
- [Contributing](https://github.com/al91liwo/fastapi-profiler/blob/main/docs/contributing.md)
- [Extending](https://github.com/al91liwo/fastapi-profiler/blob/main/docs/extending.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
