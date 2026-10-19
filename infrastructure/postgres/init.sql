CREATE TABLE IF NOT EXISTS measurements (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_measurements_device_id
    ON measurements(device_id);
