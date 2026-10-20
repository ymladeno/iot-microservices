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