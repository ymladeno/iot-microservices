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

## build the image
docker compose build analytics

##  load the image
minikube image load iot-analytics:latest

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


kubectl exec -it deployment/kafka -- \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:29092 \
  --topic measurements \
  --from-beginning

kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl rollout status statefulset/postgres --timeout=120s

## check deployment syntax
kubectl apply --dry-run=server -f k8s/postgres-statefulset.yaml

## logs
kubectl logs deployment/analytics-consumer --previous --tail=60