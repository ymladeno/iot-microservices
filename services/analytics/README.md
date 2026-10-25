uvicorn services.analytics.app.main:app \
    --host 127.0.0.1 \
    --port 8001

curl -X POST http://localhost:8001/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 101,
    "temperature": 24.5,
    "timestamp": "2026-10-17T08:00:00Z"
  }'

curl http://localhost:8001/devices/101/stats

python -m uvicorn services.analytics.app.main:app --host 127.0.0.1 --port 8001

python -m pip install -r services/analytics/requirements.txt

docker compose up -d --build analytics

docker compose logs -f analytics

## read Kafka messages
docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:29092 \
  --topic measurements \
  --from-beginning \
  --timeout-ms 5000

## inspect analytics-workers LAG
docker compose exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server kafka:29092 \
  --describe \
  --group analytics-workers

## execute sql requests
docker compose exec -T postgres psql -U iot_user -d iot_db
