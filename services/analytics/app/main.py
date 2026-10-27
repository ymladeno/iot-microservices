import json
import os
from datetime import datetime

import psycopg
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.models import Measurement

app = FastAPI()

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)

CACHE_TTL = 60

def stats_cache_key(device_id: int) -> str:
    return f"device:{device_id}:stats"

@app.get("/devices/{device_id}/stats")
def get_statistics(device_id: int):
    with psycopg.connect(DATABASE_URL) as conn:

        # Keep the version and statistics consistent.
        # Both queries see the same PostgreSQL snapshot.
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
                )

                cur.execute(
                    """
                    SELECT version
                    FROM device_versions
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )

                row = cur.fetchone()

                if row is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Device not found",
                    )

                version = row[0]
                key = f"device:{device_id}:stats:v{version}"

                # Try Redis using the database version
                try:
                    cached = redis_client.get(key)

                    if cached is not None:
                        print(f"CACHE HIT: {key}")
                        return json.loads(cached)

                except (redis.RedisError, ValueError) as error:
                    print(f"Redis read failed: {error}")

                print(f"CACHE MISS: {key}")

                cur.execute(
                    """
                    SELECT
                        COUNT(*),
                        AVG(temperature),
                        MIN(temperature),
                        MAX(temperature)
                    FROM measurements
                    WHERE device_id = %s
                    """,
                    (device_id,),
                )

                count, average, minimum, maximum = cur.fetchone()

    if count == 0:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    result = {
        "device_id": device_id,
        "count": count,
        "average": average,
        "minimum": minimum,
        "maximum": maximum,
    }

    try:
        redis_client.set(
            key,
            json.dumps(result),
            ex=CACHE_TTL,
        )
    except redis.RedisError as error:
        print(f"Redis write failed: {error}")

    return result
