"""
FastAPI Profiler AsyncEngine Demo

This example demonstrates how to use FastAPI Profiler with SQLAlchemy's AsyncEngine.
It shows how to properly instrument an AsyncEngine to avoid the error:
AttributeError: 'AsyncEngine' object has no attribute '_profiler_metadata'

The key is to instrument the AsyncEngine, which will properly handle the __slots__ limitation
by storing metadata on the underlying sync_engine.
"""

import asyncio
import os
import sys
import threading
import time
import webbrowser
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from fastapi_profiler import Profiler
from fastapi_profiler.instrumentations import SQLAlchemyInstrumentation

# Create SQLAlchemy models
Base = declarative_base()


class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)


# Create FastAPI app
app = FastAPI(title="FastAPI Profiler AsyncEngine Demo")

# Create SQLAlchemy async engine
# Using SQLite for demo purposes, but this works with any async driver
DATABASE_URL = "sqlite+aiosqlite:///./async_test.db"
engine = create_async_engine(DATABASE_URL)

# Create async session factory
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Dependency to get async DB session
async def get_db():
    async with async_session_maker() as session:
        yield session


# Pydantic models
class Item(BaseModel):
    name: str
    description: str = None

    class Config:
        orm_mode = True


class ItemCreate(BaseModel):
    name: str
    description: str = None


# API routes
@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI Profiler AsyncEngine Demo"}


@app.get("/items/", response_model=List[Item])
async def read_items(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    # Execute a query
    result = await db.execute(select(ItemModel).offset(skip).limit(limit))
    items = result.scalars().all()
    return items


@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    # Execute a query
    result = await db.execute(select(ItemModel).filter(ItemModel.id == item_id))
    item = result.scalars().first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/items/", response_model=Item)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    # Create a new item
    db_item = ItemModel(name=item.name, description=item.description)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@app.get("/raw-query/")
async def raw_query(db: AsyncSession = Depends(get_db)):
    # Execute a raw SQL query
    result = await db.execute(text("SELECT COUNT(*) FROM items"))
    count = result.scalar()

    # Execute another query
    result = await db.execute(text("SELECT name FROM items ORDER BY id DESC LIMIT 5"))
    recent_items = result.scalars().all()

    return {"total_items": count, "recent_items": recent_items}


# Initialize the profiler
print("Initializing profiler...")
profiler = Profiler(app)

# IMPORTANT: Manually instrument the AsyncEngine
# This is the key step to avoid the AttributeError
print(f"Instrumenting AsyncEngine: {engine}")
SQLAlchemyInstrumentation.instrument(engine)


# Function to create tables and generate sample data
async def setup_database():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Generate sample data
    async with async_session_maker() as session:
        # Check if we already have data
        result = await session.execute(text("SELECT COUNT(*) FROM items"))
        count = result.scalar()

        if count > 0:
            print(f"Database already contains {count} items")
            return

        print("Generating sample data...")
        for i in range(20):
            item = ItemModel(
                name=f"Async Item {i}", description=f"Description for async item {i}"
            )
            session.add(item)

        await session.commit()
        print("Sample data generated")


# Function to make requests to the API
async def make_requests(base_url: str, num_requests: int = 30):
    """Make a series of requests to the API endpoints"""
    import httpx

    print(f"\nMaking {num_requests} requests to demonstrate the profiler...")

    async with httpx.AsyncClient() as client:
        for i in range(num_requests):
            # Choose a random endpoint
            import random

            endpoint_type = random.choice(["list", "detail", "create", "raw"])

            try:
                if endpoint_type == "list":
                    # Get list of items
                    await client.get(f"{base_url}/items/")
                    print(f"Request {i + 1}/{num_requests}: GET /items/")

                elif endpoint_type == "detail":
                    # Get a specific item
                    item_id = random.randint(1, 20)
                    await client.get(f"{base_url}/items/{item_id}")
                    print(f"Request {i + 1}/{num_requests}: GET /items/{item_id}")

                elif endpoint_type == "create":
                    # Create a new item
                    await client.post(
                        f"{base_url}/items/",
                        json={
                            "name": f"New Async Item {random.randint(1000, 9999)}",
                            "description": f"Created during demo run {i}",
                        },
                    )
                    print(f"Request {i + 1}/{num_requests}: POST /items/")

                elif endpoint_type == "raw":
                    # Execute raw query
                    await client.get(f"{base_url}/raw-query/")
                    print(f"Request {i + 1}/{num_requests}: GET /raw-query/")

                # Small delay between requests
                await asyncio.sleep(random.uniform(0.1, 0.3))

            except Exception as e:
                print(f"Error making request: {e}")


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
    # Setup database and generate sample data
    await setup_database()

    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    print("Starting server...")
    await asyncio.sleep(2)

    # Open the dashboard in a browser
    browser_thread = threading.Thread(
        target=open_browser, args=("http://127.0.0.1:8000/profiler",), daemon=True
    )
    browser_thread.start()

    # Wait a bit more for the browser to open
    await asyncio.sleep(1)

    # Make some requests
    await make_requests("http://127.0.0.1:8000", num_requests=30)

    print(
        "\nDemo completed! The profiler dashboard shows the database query performance."
    )
    print("Press Ctrl+C to exit.")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    print("FastAPI Profiler AsyncEngine Demo")
    print("=================================")
    print("This demo shows how to properly instrument SQLAlchemy's AsyncEngine.")
    print("The dashboard will open in your browser.")

    try:
        if os.path.exists("./async_test.db"):
            os.remove("./async_test.db")

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
