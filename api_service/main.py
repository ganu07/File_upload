from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import asyncpg
import aioredis
from typing import Optional
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration for PostgreSQL and Redis
DB_CONFIG = {
    "user": "user",
    "password": "password",
    "database": "file_db",
    "host": "postgres",  
    "port": 5432,
}
REDIS_CONFIG = {
    "host": "redis",  
    "port": 6379,
}


# App initialization
app = FastAPI()

# Rate limiter configuration
RATE_LIMIT = 5  # Maximum requests
TIME_WINDOW = 60  # Time window in seconds


# Initialize database pool and Redis client during app startup
@app.on_event("startup")
async def startup_event():
    logger.info("App startup: Initializing database pool and Redis client.")
    app.state.db_pool = await asyncpg.create_pool(**DB_CONFIG)
    app.state.redis_client = await aioredis.from_url(f"redis://{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
    logger.info("App startup: Initialization complete.")


# Close resources during app shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("App shutdown: Closing database pool and Redis client.")
    await app.state.db_pool.close()
    await app.state.redis_client.close()
    logger.info("App shutdown: Resources closed.")


# Dependency to get database pool
async def get_db_pool():
    return app.state.db_pool


# Dependency to get Redis client
async def get_redis_client():
    return app.state.redis_client


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    logger.info(f"Received request: {request.method} {request.url}")
    redis_client = await get_redis_client()

    try:
        await rate_limiter(request, redis_client)
        response = await call_next(request)
        logger.info(f"Request {request.method} {request.url} processed successfully.")
    except HTTPException as e:
        logger.warning(f"Rate limit exceeded: {request.client.host} - {e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        logger.error(f"Error processing request {request.method} {request.url}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

    return response

async def rate_limiter(request: Request, redis_client: aioredis.Redis):
    client_ip = request.client.host
    redis_key = f"rate_limit:{client_ip}"

    # Increment request count
    current_count = await redis_client.incr(redis_key)

    # Set expiration if this is the first request
    if current_count == 1:
        await redis_client.expire(redis_key, TIME_WINDOW)

    # Enforce rate limit
    if current_count > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check requested.")
    return {"status": "healthy"}


# Data fetching endpoint with pagination and search
@app.get("/data")
async def get_data(
    pageno: int = 1,
    pagesize: int = 10,
    name: Optional[str] = ""
):
    logger.info(f"Fetching data with params: pageno={pageno}, pagesize={pagesize}, name={name}")
    offset = (pageno - 1) * pagesize
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT * FROM file_data WHERE line_data LIKE $1 LIMIT $2 OFFSET $3",
                f"%{name}%", pagesize, offset
            )
        data = [{"id": row["id"], "line_data": row["line_data"]} for row in rows]
        logger.info(f"Fetched {len(data)} rows from the database.")
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting application.")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
