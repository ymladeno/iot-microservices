import json
import os

import psycopg
from confluent_kafka import Consumer, KafkaException
from pydantic import ValidationError

from app.main import Measurement

DATABASE_URL = os.environ["DATABASE_URL"]

consumer = Consumer({
    "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
    "group.id": "analytics-workers",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})

consumer.subscribe(["measurements"])


def store_measurement(measurement: Measurement):
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

            cur.execute(
                """
                INSERT INTO device_versions (device_id, version)
                VALUES (%s, 1)
                ON CONFLICT (device_id)
                DO UPDATE SET
                    version = device_versions.version + 1
                """,
                (measurement.device_id,),
            )


print("Analytics Kafka consumer started", flush=True)

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue

        if msg.error():
            print(f"Kafka error: {msg.error()}", flush=True)
            continue

        try:
            print(f"Received raw message: {msg.value()!r}", flush=True)
            data = json.loads(msg.value())
            measurement = Measurement.model_validate(data)

            store_measurement(measurement)

            # Commit Kafka offset only after PostgreSQL commits.
            consumer.commit(message=msg, asynchronous=False)

            print(
                f"Stored device {measurement.device_id}",
                flush=True,
            )

        except (ValueError, ValidationError) as error:
            print(
                f"Invalid message at offset {msg.offset()}: "
                f"{msg.value()!r} - {error}",
                flush=True,
            )
            consumer.commit(message=msg, asynchronous=False)
            continue

        except (psycopg.Error, KafkaException) as error:
            print(f"Processing failed: {error}", flush=True)

            # Stop rather than skipping a failed measurement.
            # On restart, Kafka can redeliver it.
            raise

finally:
    consumer.close()
