"""
FastAPI Profiler Demo with Automatic Browser Launch

This script:
1. Starts a FastAPI server with the profiler enabled
2. Opens the profiler dashboard in your default browser
3. Makes a series of API requests with varying response times
4. Shows real-time profiling data in the dashboard
"""

import asyncio
import random
import sys
import threading
import time
import webbrowser

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_profiler import Profiler

app = FastAPI(title="FastAPI Profiler Interactive Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    """Fast endpoint - responds immediately"""
    return {"message": "Welcome to the FastAPI Profiler demo!"}


@app.get("/fast")
async def fast_endpoint():
    """Fast endpoint with minimal delay"""
    await asyncio.sleep(0.01)
    return {"status": "completed quickly"}


@app.get("/medium")
async def medium_endpoint():
    """Medium speed endpoint"""
    await asyncio.sleep(random.uniform(0.1, 0.3))
    return {"status": "completed with medium speed"}


@app.get("/slow")
async def slow_endpoint():
    """Slow endpoint"""
    await asyncio.sleep(random.uniform(0.5, 0.8))
    return {"status": "completed slowly"}


@app.get("/very-slow")
async def very_slow_endpoint():
    """Very slow endpoint"""
    await asyncio.sleep(random.uniform(1.0, 1.5))
    return {"status": "completed very slowly"}


@app.get("/random")
async def random_endpoint():
    """Endpoint with random response time"""
    category = random.choice(["fast", "medium", "slow", "very-slow"])

    if category == "fast":
        delay = random.uniform(0.01, 0.05)
    elif category == "medium":
        delay = random.uniform(0.1, 0.3)
    elif category == "slow":
        delay = random.uniform(0.5, 0.8)
    else:
        delay = random.uniform(1.0, 1.5)

    await asyncio.sleep(delay)
    return {"status": f"random delay ({category})", "delay": delay}


@app.get("/error")
async def error_endpoint():
    """Endpoint that sometimes raises an error"""
    if random.random() < 0.3:
        raise ValueError("Random error occurred")
    await asyncio.sleep(0.2)
    return {"status": "completed successfully"}


# Additional HTTP methods for testing
@app.post("/items")
async def create_item(item: dict):
    """POST endpoint to create an item"""
    await asyncio.sleep(random.uniform(0.1, 0.4))
    return {"item_id": random.randint(1, 1000), **item}


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: dict):
    """PUT endpoint to update an item"""
    await asyncio.sleep(random.uniform(0.2, 0.5))
    return {"item_id": item_id, "updated": True, **item}


@app.patch("/items/{item_id}")
async def partial_update_item(item_id: int, item: dict):
    """PATCH endpoint for partial updates"""
    await asyncio.sleep(random.uniform(0.1, 0.3))
    return {"item_id": item_id, "patched": True, **item}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """DELETE endpoint to remove an item"""
    await asyncio.sleep(random.uniform(0.05, 0.2))
    return {"item_id": item_id, "deleted": True}


@app.head("/status")
async def check_status():
    """HEAD endpoint for status checks"""
    await asyncio.sleep(0.01)
    return {}


@app.options("/options")
async def options_endpoint():
    """OPTIONS endpoint"""
    await asyncio.sleep(0.01)
    return {}


# Initialize the profiler
Profiler(app)


# Function to make requests to the API
async def make_requests(base_url: str, num_requests: int = 50):
    """Make a series of requests to the API endpoints"""
    # Define endpoints with their HTTP methods
    endpoint_configs = [
        {"method": "GET", "url": "/", "weight": 0.1},
        {"method": "GET", "url": "/fast", "weight": 0.1},
        {"method": "GET", "url": "/medium", "weight": 0.1},
        {"method": "GET", "url": "/slow", "weight": 0.05},
        {"method": "GET", "url": "/very-slow", "weight": 0.05},
        {"method": "GET", "url": "/random", "weight": 0.05},
        {"method": "GET", "url": "/error", "weight": 0.05},
        {
            "method": "POST",
            "url": "/items",
            "weight": 0.1,
            "data": {"name": "Test Item", "price": 19.99},
        },
        {
            "method": "PUT",
            "url": "/items/42",
            "weight": 0.1,
            "data": {"name": "Updated Item", "price": 29.99},
        },
        {
            "method": "PATCH",
            "url": "/items/42",
            "weight": 0.1,
            "data": {"price": 24.99},
        },
        {"method": "DELETE", "url": "/items/42", "weight": 0.1},
        {"method": "HEAD", "url": "/status", "weight": 0.05},
        {"method": "OPTIONS", "url": "/options", "weight": 0.05},
    ]

    weights = [config["weight"] for config in endpoint_configs]

    print(f"\nMaking {num_requests} requests to demonstrate the profiler...")

    async with httpx.AsyncClient() as client:
        for i in range(num_requests):
            # Choose a random endpoint config based on weights
            config = random.choices(endpoint_configs, weights=weights)[0]

            try:
                method = config["method"]
                url = f"{base_url}{config['url']}"
                data = config.get("data")

                print(f"Request {i + 1}/{num_requests}: {method} {config['url']}")

                if method == "GET":
                    await client.get(url)
                elif method == "POST":
                    await client.post(url, json=data)
                elif method == "PUT":
                    await client.put(url, json=data)
                elif method == "PATCH":
                    await client.patch(url, json=data)
                elif method == "DELETE":
                    await client.delete(url)
                elif method == "HEAD":
                    await client.head(url)
                elif method == "OPTIONS":
                    await client.options(url)

                await asyncio.sleep(random.uniform(0.1, 0.5))

            except Exception as e:
                print(f"Error making request to {config['url']}: {e}")


def open_browser(url: str, delay: float = 1.0):
    """Open the browser after a short delay"""
    time.sleep(delay)
    print(f"Opening dashboard in browser: {url}")
    webbrowser.open(url)


def run_server():
    """Run the uvicorn server"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


async def main():
    """Main function to run the demo"""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    browser_thread = threading.Thread(
        target=open_browser, args=("http://127.0.0.1:8000/profiler",), daemon=True
    )
    browser_thread.start()

    await asyncio.sleep(2)

    await make_requests("http://127.0.0.1:8000", num_requests=50)

    print("\nDemo completed! The profiler dashboard shows the performance data.")
    print("Press Ctrl+C to exit.")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    print("FastAPI Profiler Interactive Demo")
    print("=================================")
    print("Starting server at http://127.0.0.1:8000")
    print("Dashboard will be available at http://127.0.0.1:8000/profiler")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
