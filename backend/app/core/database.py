import asyncpg
from asyncpg import Pool
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "host": os.getenv("DB_HOST")
}

pool: Pool = None

async def init_db():
    """Create a connection pool at startup."""
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=10)
    return pool

async def close_db():
    """Close the pool on shutdown."""
    if pool:
        await pool.close()

async def get_db():
    """Dependency to get a database connection from the pool."""
    async with pool.acquire() as conn:
        yield conn