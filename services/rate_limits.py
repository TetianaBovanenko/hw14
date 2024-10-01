import os
import logging
from fastapi import HTTPException
from redis import Redis, RedisError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0
    )
except RedisError as e:
    logger.error(f"Error connecting to Redis: {e}")
    raise

# Configurable rate limit and time frame from environment variables
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 5))  # Maximum number of requests
TIME_FRAME = int(os.getenv("TIME_FRAME", 60))  # Time frame in seconds


def limit_rate(user_id: str):
    """
    Limits the number of requests a user can make within a time frame using Redis.

    If the user exceeds the allowed number of requests, an HTTP 429 error is raised.

    :param user_id: Unique identifier of the user.
    :raises HTTPException: If the user exceeds the request limit, returns a 429 error.
    """
    try:
        key = f"rate_limit:{user_id}"
        current_count = redis_client.get(key)

        if current_count is None:
            # Key doesn't exist, set it with an expiration time
            redis_client.set(key, 1, ex=TIME_FRAME)
            logger.info(f"Rate limit initialized for user {user_id}.")
        elif int(current_count) < RATE_LIMIT:
            # Increment the count if the rate limit has not been exceeded
            redis_client.incr(key)
            logger.info(f"Request count {int(current_count) + 1} for user {user_id}.")
        else:
            # Rate limit exceeded
            logger.warning(f"User {user_id} exceeded the rate limit.")
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

    except RedisError as e:
        # Log Redis connection errors and raise a 500 HTTP exception
        logger.error(f"Redis error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")
