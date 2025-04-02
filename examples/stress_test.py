"""
FastAPI Profiler Stress Test

This script creates a high-load scenario to demonstrate the profiler's real-time capabilities:
1. Starts a FastAPI server with the profiler enabled
2. Opens the profiler dashboard in your default browser
3. Launches multiple concurrent workers that bombard the API with requests
4. Shows real-time profiling data in the dashboard as the system handles the load
"""

import asyncio
import random
import sys
import threading
import time
import webbrowser

import httpx
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fastapi_profiler import Profiler, add_external_call

# Create FastAPI app
app = FastAPI(title="FastAPI Profiler Stress Test")

# Add CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated database for user data
USERS_DB = {
    i: {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
    for i in range(1, 1001)
}

# Simulated database for product data
PRODUCTS_DB = {
    i: {"id": i, "name": f"Product {i}", "price": round(random.uniform(10, 1000), 2)}
    for i in range(1, 501)
}

# Simulated database for order data
ORDERS_DB = {}

# Counters for various operations
counters = {
    "db_reads": 0,
    "db_writes": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "errors": 0,
}

# Simulated cache
cache = {}


# Dependency to simulate database latency
async def get_db():
    # Simulate connection latency
    await asyncio.sleep(random.uniform(0.005, 0.02))
    return "db_connection"


# Dependency to simulate authentication
async def get_current_user():
    # Simulate auth latency
    await asyncio.sleep(random.uniform(0.01, 0.03))
    user_id = random.randint(1, 1000)
    if user_id in USERS_DB:
        return USERS_DB[user_id]
    raise HTTPException(status_code=401, detail="Unauthorized")


# Simulate external API call
async def call_external_api(service_name):
    start_time = time.perf_counter()
    # Simulate external API latency
    await asyncio.sleep(random.uniform(0.05, 0.2))
    duration = time.perf_counter() - start_time

    # Record the external call in the profiler
    add_external_call(
        url=f"https://api.example.com/{service_name}", method="POST", duration=duration
    )

    return {"status": "success", "service": service_name}


# Simulate database query
async def query_db(db, query_type, entity_id=None):
    # Simulate query latency based on type
    if query_type == "read":
        await asyncio.sleep(random.uniform(0.01, 0.05))
        counters["db_reads"] += 1
    elif query_type == "write":
        await asyncio.sleep(random.uniform(0.02, 0.08))
        counters["db_writes"] += 1
    elif query_type == "complex":
        await asyncio.sleep(random.uniform(0.05, 0.15))
        counters["db_reads"] += 3

    return {"status": "success", "query_type": query_type}


# Simulate cache operations
async def check_cache(key):
    # Small latency for cache check
    await asyncio.sleep(0.002)

    if key in cache and random.random() < 0.7:  # 70% cache hit rate
        counters["cache_hits"] += 1
        return cache[key]

    counters["cache_misses"] += 1
    return None


async def update_cache(key, value):
    await asyncio.sleep(0.003)
    cache[key] = value


# Background task to simulate async processing
async def process_in_background(order_id):
    await asyncio.sleep(random.uniform(0.5, 2.0))
    ORDERS_DB[order_id]["status"] = "processed"


# API Routes


@app.get("/")
async def read_root():
    """Fast endpoint - responds immediately"""
    return {"message": "Welcome to the FastAPI Profiler Stress Test!"}


@app.get("/users", response_model=list)
async def get_users(skip: int = 0, limit: int = 10, db: str = Depends(get_db)):
    """Get a list of users with pagination"""
    await query_db(db, "read")

    # Get user IDs within the range
    user_ids = list(USERS_DB.keys())[skip : skip + limit]
    return [USERS_DB[user_id] for user_id in user_ids]


@app.get("/users/{user_id}")
async def get_user(user_id: int, db: str = Depends(get_db)):
    """Get a single user by ID"""
    # Try cache first
    cache_key = f"user_{user_id}"
    cached_data = await check_cache(cache_key)
    if cached_data:
        return cached_data

    # If not in cache, query DB
    await query_db(db, "read")

    if user_id not in USERS_DB:
        counters["errors"] += 1
        raise HTTPException(status_code=404, detail="User not found")

    # Update cache
    await update_cache(cache_key, USERS_DB[user_id])
    return USERS_DB[user_id]


@app.post("/users")
async def create_user(user: dict, db: str = Depends(get_db)):
    """Create a new user"""
    await query_db(db, "write")

    user_id = max(USERS_DB.keys()) + 1 if USERS_DB else 1
    USERS_DB[user_id] = {**user, "id": user_id}
    return USERS_DB[user_id]


@app.get("/products")
async def get_products(skip: int = 0, limit: int = 20, db: str = Depends(get_db)):
    """Get a list of products with pagination"""
    await query_db(db, "read")

    # Get product IDs within the range
    product_ids = list(PRODUCTS_DB.keys())[skip : skip + limit]
    return [PRODUCTS_DB[product_id] for product_id in product_ids]


@app.get("/products/{product_id}")
async def get_product(product_id: int, db: str = Depends(get_db)):
    """Get a single product by ID"""
    # Try cache first
    cache_key = f"product_{product_id}"
    cached_data = await check_cache(cache_key)
    if cached_data:
        return cached_data

    # If not in cache, query DB
    await query_db(db, "read")

    if product_id not in PRODUCTS_DB:
        counters["errors"] += 1
        raise HTTPException(status_code=404, detail="Product not found")

    # Update cache
    await update_cache(cache_key, PRODUCTS_DB[product_id])
    return PRODUCTS_DB[product_id]


@app.post("/orders")
async def create_order(
    order: dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: str = Depends(get_db),
):
    """Create a new order with background processing"""
    # Validate product exists
    product_id = order.get("product_id")
    if product_id not in PRODUCTS_DB:
        counters["errors"] += 1
        raise HTTPException(status_code=404, detail="Product not found")

    # Create order
    await query_db(db, "write")

    # Call payment service
    await call_external_api("payment")

    order_id = len(ORDERS_DB) + 1
    ORDERS_DB[order_id] = {
        "id": order_id,
        "user_id": current_user["id"],
        "product_id": product_id,
        "status": "pending",
        "created_at": time.time(),
    }

    # Process order in background
    background_tasks.add_task(process_in_background, order_id)

    return {"order_id": order_id, "status": "pending"}


@app.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: str = Depends(get_db),
):
    """Get a single order by ID"""
    await query_db(db, "read")

    if order_id not in ORDERS_DB:
        counters["errors"] += 1
        raise HTTPException(status_code=404, detail="Order not found")

    order = ORDERS_DB[order_id]

    # Check if user owns this order
    if order["user_id"] != current_user["id"]:
        counters["errors"] += 1
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    return order


@app.get("/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Complex endpoint that aggregates data from multiple sources"""
    # Call multiple external services
    await asyncio.gather(call_external_api("analytics"), call_external_api("reporting"))

    # Return aggregated stats
    return {
        "user": current_user,
        "counters": counters,
        "cache_hit_ratio": counters["cache_hits"]
        / (counters["cache_hits"] + counters["cache_misses"])
        if (counters["cache_hits"] + counters["cache_misses"]) > 0
        else 0,
        "total_orders": len(ORDERS_DB),
        "total_products": len(PRODUCTS_DB),
        "total_users": len(USERS_DB),
    }


@app.get("/error")
async def trigger_error():
    """Endpoint that always raises an error"""
    counters["errors"] += 1
    raise HTTPException(status_code=500, detail="Simulated server error")


# Initialize the profiler
Profiler(app)


# Function to make concurrent requests to the API
async def make_concurrent_requests(
    base_url: str, num_workers: int = 10, requests_per_worker: int = 50
):
    """Make concurrent requests to the API using multiple workers"""
    print(
        f"\nStarting stress test with {num_workers} workers, {requests_per_worker} requests per worker"
    )
    print(f"Total requests: {num_workers * requests_per_worker}")

    # Define all possible API endpoints with their weights
    endpoints = [
        {"method": "GET", "url": "/", "weight": 5},
        {"method": "GET", "url": "/users?limit=20", "weight": 10},
        {
            "method": "GET",
            "url": "/users/{user_id}",
            "weight": 15,
            "param_range": (1, 1000),
        },
        {
            "method": "POST",
            "url": "/users",
            "weight": 5,
            "data": lambda: {
                "name": f"New User {random.randint(1, 1000)}",
                "email": f"new{random.randint(1, 9999)}@example.com",
            },
        },
        {"method": "GET", "url": "/products?limit=30", "weight": 10},
        {
            "method": "GET",
            "url": "/products/{product_id}",
            "weight": 15,
            "param_range": (1, 500),
        },
        {
            "method": "POST",
            "url": "/orders",
            "weight": 10,
            "data": lambda: {"product_id": random.randint(1, 500)},
        },
        {
            "method": "GET",
            "url": "/orders/{order_id}",
            "weight": 5,
            "param_range": (1, 100),
        },
        {"method": "GET", "url": "/dashboard", "weight": 3},
        {"method": "GET", "url": "/error", "weight": 2},
    ]

    # Calculate total weight for weighted random selection
    total_weight = sum(endpoint["weight"] for endpoint in endpoints)

    # Track request counts
    request_count = 0

    async def worker(worker_id: int):
        """Worker function to make API requests"""
        nonlocal request_count
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            for i in range(requests_per_worker):
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
                        url = url_template.replace(
                            f"{{{param_name}}}", str(param_value)
                        )
                    else:
                        url = url_template

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
                        await client.get(full_url)
                    elif method == "POST":
                        await client.post(full_url, json=data)

                    # Increment request counter
                    request_count += 1

                    # No sleep between requests to maximize load

                except Exception as e:
                    # Print errors but continue
                    print(f"Error on {method} {url}: {str(e)}")

                # Print progress
                if (i + 1) % 10 == 0:
                    print(
                        f"Worker {worker_id}: Completed {i + 1}/{requests_per_worker} requests"
                    )

    # Create and run workers
    workers = [worker(i) for i in range(num_workers)]

    # Start a progress monitor
    async def monitor_progress():
        last_count = 0
        while True:
            await asyncio.sleep(1)
            current = request_count
            rate = current - last_count
            print(f"Requests completed: {current} (Rate: {rate}/sec)")
            last_count = current

    # Run workers and monitor together
    monitor_task = asyncio.create_task(monitor_progress())
    await asyncio.gather(*workers)
    monitor_task.cancel()

    print(f"\nStress test completed! Total requests: {request_count}")


def open_browser(url: str, delay: float = 2.0):
    """Open the browser after a short delay"""
    time.sleep(delay)
    print(f"Opening dashboard in browser: {url}")
    webbrowser.open(url)


def run_server():
    """Run the uvicorn server"""
    uvicorn.run(app, host="127.0.0.1", port=8000)


async def main():
    """Main function to run the stress test"""
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

    # Ask user for stress test parameters
    print("\nFastAPI Profiler Stress Test")
    print("===========================")
    print(
        "This will bombard the API with concurrent requests to demonstrate the profiler."
    )
    print("You can watch the dashboard update in real-time as requests are processed.")

    # Default to high load
    num_workers = 20
    requests_per_worker = 200

    try:
        custom = input(
            "\nUse high load settings (20 workers, 200 requests each)? [Y/n]: "
        ).lower()
        if custom == "n":
            num_workers = int(input("Number of concurrent workers [20]: ") or "20")
            requests_per_worker = int(input("Requests per worker [200]: ") or "200")
    except ValueError:
        print("Invalid input, using defaults.")

    print(
        f"\nStarting stress test with {num_workers} workers and {requests_per_worker} requests per worker"
    )
    print(f"Total planned requests: {num_workers * requests_per_worker}")
    print("\nWatch the dashboard for real-time updates!")

    # Run the stress test
    await make_concurrent_requests(
        "http://127.0.0.1:8000",
        num_workers=num_workers,
        requests_per_worker=requests_per_worker,
    )

    print("\nStress test completed! The profiler dashboard shows the performance data.")
    print("Press Ctrl+C to exit.")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
