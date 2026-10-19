import os
from datetime import datetime

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

DATABASE_URL = os.environ["DATABASE_URL"]


class Measurement(BaseModel):
    device_id: int
    temperature: float
    timestamp: datetime


@app.post("/measurements")
def add_measurement(measurement: Measurement):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO measurements
                    (device_id, temperature, timestamp)
                VALUES (%s, %s, %s)
                """,
                (
                    measurement.device_id,
                    measurement.temperature,
                    measurement.timestamp,
                ),
            )

    print(f"Stored measurement: {measurement}")

    return {"status": "stored"}


@app.get("/devices/{device_id}/stats")
def get_statistics(device_id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
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

    return {
        "device_id": device_id,
        "count": count,
        "average": average,
        "minimum": minimum,
        "maximum": maximum,
    }
