import json
import logging
import os

import psycopg
from confluent_kafka import Consumer, KafkaException
from pydantic import ValidationError

from app.models import Measurement


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

consumer = Consumer({
    "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
    "group.id": "analytics-workers",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})

consumer.subscribe(["measurements"])


def store_measurement(measurement: Measurement, msg) -> bool:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO measurements
                    (device_id, temperature, timestamp,
                     kafka_topic, kafka_partition, kafka_offset)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT
                    (kafka_topic, kafka_partition, kafka_offset)
                DO NOTHING
                RETURNING id
                """,
                (
                    measurement.device_id,
                    measurement.temperature,
                    measurement.timestamp,
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                ),
            )

            inserted = cur.fetchone()

            if inserted is None:
                return False

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

    return True


def main():
    logger.info("Analytics Kafka consumer started")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue

            if msg.error():
                logger.error("Kafka error: %s", msg.error())
                continue

            try:
                logger.debug("Received raw message: %r", msg.value())

                data = json.loads(msg.value())
                measurement = Measurement.model_validate(data)

                inserted = store_measurement(measurement, msg)

                # Commit Kafka offset only after PostgreSQL commits.
                consumer.commit(message=msg, asynchronous=False)

                if inserted:
                    logger.info(
                        "Stored device %s (partition=%s, offset=%s)",
                        measurement.device_id,
                        msg.partition(),
                        msg.offset(),
                    )
                else:
                    logger.info(
                        "Duplicate Kafka message (partition=%s, offset=%s)",
                        msg.partition(),
                        msg.offset(),
                    )

            except (ValueError, ValidationError) as error:
                logger.warning(
                    "Invalid message at offset %s: %r - %s",
                    msg.offset(),
                    msg.value(),
                    error,
                )

                # Skip invalid messages by committing their offsets.
                consumer.commit(message=msg, asynchronous=False)

            except Exception:
                logger.exception("Measurement processing failed")

                # Stop rather than skipping a failed measurement.
                # Kubernetes can restart the consumer.
                # Kafka can redeliver the uncommitted message.
                raise

    finally:
        consumer.close()
        logger.info("Analytics Kafka consumer stopped")


if __name__ == "__main__":
    main()
