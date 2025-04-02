"""
FastAPI Profiler Real-time Demo

This script creates a continuous stream of requests to demonstrate the real-time
capabilities of the FastAPI Profiler dashboard:

1. Starts a FastAPI server with the profiler enabled
2. Opens the profiler dashboard in your default browser
3. Continuously sends requests at a controlled rate
4. Shows real-time profiling data in the dashboard
"""

import asyncio
import random
import sys
import threading
import time
import webbrowser
from datetime import datetime

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from fastapi_profiler import Profiler, add_external_call

# Create FastAPI app
app = FastAPI(title="FastAPI Profiler Real-time Demo")

# Add CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated database
DB = {
    "items": {},
    "users": {i: {"id": i, "name": f"User {i}"} for i in range(1, 100)},
    "counter": 0,
}


# Endpoint with variable response time
@app.get("/")
async def read_root():
    """Fast endpoint"""
    return {"message": "Welcome to the FastAPI Profiler Real-time Demo"}


@app.get("/fast")
async def fast_endpoint():
    """Fast endpoint with minimal delay"""
    await asyncio.sleep(random.uniform(0.001, 0.01))
    DB["counter"] += 1
    return {"status": "completed quickly", "counter": DB["counter"]}


@app.get("/medium")
async def medium_endpoint():
    """Medium speed endpoint"""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    # Simulate external API call
    start_time = time.perf_counter()
    await asyncio.sleep(random.uniform(0.01, 0.05))
    duration = time.perf_counter() - start_time
    add_external_call(
        url="https://api.example.com/data", method="GET", duration=duration
    )

    DB["counter"] += 1
    return {"status": "medium speed", "counter": DB["counter"]}


@app.get("/slow")
async def slow_endpoint():
    """Slow endpoint"""
    await asyncio.sleep(random.uniform(0.3, 0.7))

    # Simulate multiple external API calls
    for service in ["auth", "payment", "shipping"]:
        start_time = time.perf_counter()
        await asyncio.sleep(random.uniform(0.05, 0.15))
        duration = time.perf_counter() - start_time
        add_external_call(
            url=f"https://api.example.com/{service}", method="POST", duration=duration
        )

    DB["counter"] += 1
    return {"status": "completed slowly", "counter": DB["counter"]}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get an item by ID"""
    await asyncio.sleep(random.uniform(0.01, 0.05))

    if item_id not in DB["items"]:
        if random.random() < 0.3:  # 30% chance of creating a new item
            DB["items"][item_id] = {
                "id": item_id,
                "name": f"Item {item_id}",
                "created_at": time.time(),
            }
        else:
            raise HTTPException(status_code=404, detail="Item not found")

    return DB["items"][item_id]


@app.post("/items")
async def create_item(item: dict):
    """Create a new item"""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    item_id = len(DB["items"]) + 1
    DB["items"][item_id] = {**item, "id": item_id, "created_at": time.time()}

    # Simulate external API call
    start_time = time.perf_counter()
    await asyncio.sleep(random.uniform(0.1, 0.3))
    duration = time.perf_counter() - start_time
    add_external_call(
        url="https://api.example.com/notify", method="POST", duration=duration
    )

    return DB["items"][item_id]


@app.get("/users")
async def get_users(limit: int = Query(10, ge=1, le=100)):
    """Get a list of users"""
    await asyncio.sleep(random.uniform(0.05, 0.15))

    user_ids = list(DB["users"].keys())[:limit]
    return [DB["users"][user_id] for user_id in user_ids]


@app.get("/error")
async def trigger_error():
    """Endpoint that always raises an error"""
    await asyncio.sleep(random.uniform(0.01, 0.1))
    raise HTTPException(status_code=500, detail="Simulated server error")


# Initialize the profiler
Profiler(app)


# Function to continuously send requests
async def continuous_requests(base_url: str, requests_per_second: float = 5.0):
    """Send a continuous stream of requests at a controlled rate"""
    print(
        f"\nSending continuous requests at approximately {requests_per_second} requests per second"
    )

    # Define endpoints with their probabilities
    endpoints = [
        {"method": "GET", "url": "/fast", "weight": 0.4},
        {"method": "GET", "url": "/medium", "weight": 0.3},
        {"method": "GET", "url": "/slow", "weight": 0.1},
        {
            "method": "GET",
            "url": "/items/{item_id}",
            "weight": 0.1,
            "param_range": (1, 100),
        },
        {
            "method": "POST",
            "url": "/items",
            "weight": 0.05,
            "data": lambda: {"name": f"New Item {random.randint(1, 1000)}"},
        },
        {
            "method": "GET",
            "url": "/users",
            "weight": 0.03,
            "params": {"limit": lambda: random.randint(5, 20)},
        },
        {"method": "GET", "url": "/error", "weight": 0.02},
    ]

    # Calculate total weight
    total_weight = sum(endpoint["weight"] for endpoint in endpoints)

    # Calculate delay between requests
    delay = 1.0 / requests_per_second

    # Track statistics
    start_time = time.time()
    request_count = 0

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        while True:
            try:
                # Select a random endpoint based on weights
                rand_val = random.uniform(0, total_weight)
                cumulative_weight = 0
                selected_endpoint = None

                for endpoint in endpoints:
                    cumulative_weight += endpoint["weight"]
                    if rand_val <= cumulative_weight:
                        selected_endpoint = endpoint
                        break

                # Prepare the request
                method = selected_endpoint["method"]
                url_template = selected_endpoint["url"]

                # Replace any path parameters
                if "{" in url_template:
                    param_name = url_template[
                        url_template.find("{") + 1 : url_template.find("}")
                    ]
                    param_range = selected_endpoint.get("param_range", (1, 100))
                    param_value = random.randint(*param_range)
                    url = url_template.replace(f"{{{param_name}}}", str(param_value))
                else:
                    url = url_template

                # Add query parameters if specified
                params = {}
                if "params" in selected_endpoint:
                    for key, value_func in selected_endpoint["params"].items():
                        if callable(value_func):
                            params[key] = value_func()
                        else:
                            params[key] = value_func

                full_url = f"{base_url}{url}"

                # Prepare data for POST requests
                data = None
                if method == "POST" and "data" in selected_endpoint:
                    if callable(selected_endpoint["data"]):
                        data = selected_endpoint["data"]()
                    else:
                        data = selected_endpoint["data"]

                # Make the request
                if method == "GET":
                    await client.get(full_url, params=params)
                elif method == "POST":
                    await client.post(full_url, json=data)

                # Increment request counter
                request_count += 1

                # Print statistics every 10 requests
                if request_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = request_count / elapsed
                    print(
                        f"Sent {request_count} requests ({rate:.2f} req/sec) - {datetime.now().strftime('%H:%M:%S')}"
                    )

                # Wait for the next request
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"Error: {str(e)}")
                await asyncio.sleep(delay)  # Still wait before retrying


def open_browser(url: str, delay: float = 2.0):
    """Open the browser after a short delay"""
    time.sleep(delay)
    print(f"Opening dashboard in browser: {url}")
    webbrowser.open(url)


def run_server():
    """Run the uvicorn server"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


async def main():
    """Main function to run the demo"""
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    print("Starting server...")
    await asyncio.sleep(3)

    # Open the dashboard in a browser
    browser_thread = threading.Thread(
        target=open_browser, args=("http://127.0.0.1:8000/profiler",), daemon=True
    )
    browser_thread.start()

    # Ask user for request rate
    print("\nFastAPI Profiler Real-time Demo")
    print("==============================")
    print("This will continuously send requests to demonstrate the real-time profiler.")
    print("You can watch the dashboard update in real-time as requests are processed.")

    try:
        requests_per_second = float(input("\nRequests per second [10]: ") or "10")
    except ValueError:
        print("Invalid input, using default rate.")
        requests_per_second = 10.0

    print("\nStarting continuous requests. Press Ctrl+C to stop.")
    print("Watch the dashboard for real-time updates!")

    # Start sending continuous requests
    await continuous_requests("http://127.0.0.1:8000", requests_per_second)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
