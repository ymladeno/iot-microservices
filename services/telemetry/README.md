## build telemetry
docker build -t telemetry ./services/telemetry

## run telemetry
docker run -p 8000:8000 telemetry

## or when we have more docker containers
docker compose up --build

## start as a daemons
docker compose up --build -d

## check docker logs
docker compose logs -f analytics

## 
docker compose ps

## check db
docker compose exec postgres psql -U iot_user -d iot_db

##
docker compose down

##
docker compose up -d

##
docker volume ls

##
docker volume inspect iot-microservices_postgres_data

##
docker compose exec postgres bash

##
docker compose exec postgres psql -U iot_user -d iot_db

##
kubectl get deployments
kubectl get pods
kubectl logs deployment/telemetry

kubectl rollout restart deployment/telemetry
kubectl rollout status deployment/telemetry