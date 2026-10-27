#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Building telemetry image ==="
docker compose build telemetry
docker tag iot-microservices-telemetry:latest iot-telemetry:latest

echo "=== Building analytics consumer image ==="
docker compose build analytics-consumer
docker tag iot-microservices-analytics-consumer:latest iot-analytics-consumer:latest

echo "=== Building analytics API image ==="
docker compose build analytics
docker tag iot-microservices-analytics:latest iot-analytics:latest

echo "=== Images built successfully ==="