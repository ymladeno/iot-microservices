CREATE TABLE IF NOT EXISTS measurements (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    kafka_topic TEXT,
    kafka_partition INTEGER,
    kafka_offset BIGINT,

    CONSTRAINT uq_kafka_message
        UNIQUE (kafka_topic, kafka_partition, kafka_offset)
);

CREATE INDEX IF NOT EXISTS idx_measurements_device_id
    ON measurements(device_id);

CREATE TABLE IF NOT EXISTS device_versions (
    device_id INTEGER PRIMARY KEY,
    version BIGINT NOT NULL DEFAULT 0
);