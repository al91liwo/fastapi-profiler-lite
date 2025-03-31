# FastAPI Profiler Lite Documentation

This directory contains detailed documentation for the FastAPI Profiler.

## Contents

- [Installation](installation.md)
- [Configuration](configuration.md)
- [Extending](extending.md)

## Quick Links

- [GitHub Repository](https://github.com/al91liwo/fastapi-profiler)
- [PyPI Package](https://pypi.org/project/fastapi-profiler-lite/)
- [Issue Tracker](https://github.com/al91liwo/fastapi-profiler/issues)

## Overview

FastAPI Profiler Lite is a lightweight performance monitoring tool for FastAPI applications. It provides real-time insights into your API's performance without requiring external services or complex setup.

### Key Features

- **One-line integration** - Add to any FastAPI app with minimal code
- **Real-time dashboard** - Live updates with automatic refresh
- **Response time tracking** - Measure execution time of each request
- **Endpoint analysis** - Identify your slowest and most used endpoints
- **Request filtering** - Search and sort through captured requests
- **Visual metrics** - Charts for response times and request distribution
- **Minimal overhead** - Designed to have low performance impact

## Architecture

FastAPI Profiler consists of three main components:

1. **Middleware** - Captures timing data for each request
2. **API Endpoints** - Serve the captured profiling data
3. **Dashboard** - Visualizes the profiling data

The middleware intercepts incoming requests, measures their execution time, and stores the data. The dashboard then fetches this data via the API endpoints and displays it in a user-friendly interface.

## Getting Started

See the [Installation](installation.md) and [Configuration](configuration.md) guides to get started.
