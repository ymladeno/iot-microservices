#!/usr/bin/env bash
set -euo pipefail

start_port_forward() {
    local service="$1"
    local port="$2"

    local pid_file="/tmp/iot-microservices-${service}-forward.pid"
    local log_file="/tmp/iot-microservices-${service}-forward.log"

    if [[ -f "$pid_file" ]]; then
        local old_pid
        old_pid=$(cat "$pid_file")

        if kill -0 "$old_pid" 2>/dev/null &&
           ps -p "$old_pid" -o args= |
               grep -q "kubectl port-forward service/${service}"; then
            kill "$old_pid"
            sleep 1
        fi

        rm -f "$pid_file"
    fi

    echo "Starting port-forward: ${service} -> localhost:${port}"
    nohup kubectl port-forward \
        "service/${service}" "${port}:${port}" \
        >"$log_file" 2>&1 </dev/null &

    local pid=$!
    echo "$pid" > "$pid_file"

    for attempt in {1..20}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            cat "$log_file"
            rm -f "$pid_file"
            return 1
        fi

        if grep -q "Forwarding from 127.0.0.1:${port}" "$log_file"; then
            return 0
        fi

        sleep 0.5
    done

    echo "Port-forward for ${service} did not become ready"
    cat "$log_file"
    kill "$pid" 2>/dev/null || true
    rm -f "$pid_file"
    return 1
}

start_kafka() {
    echo "=== Deploying Kafka storage ==="
    kubectl apply -f k8s/kafka-pvc.yaml

    echo "=== Deploying Kafka ==="
    kubectl apply -f k8s/kafka-service.yaml
    kubectl apply -f k8s/kafka-deployment.yaml

    echo "=== Waiting for Kafka ==="
    kubectl rollout status deployment/kafka --timeout=180s

    echo "=== Initializing Kafka topic ==="

    # A completed Job does not run again when applied.
    # Recreate it so initialization is checked on every startup.
    kubectl delete job kafka-init \
      --ignore-not-found=true \
      --wait=true

    kubectl apply -f k8s/kafka-init-job.yaml

    kubectl wait \
      --for=condition=complete \
      job/kafka-init \
      --timeout=180s || {
        kubectl logs job/kafka-init
        exit 1
      }
}

start_postgres() {
    echo "=== Deploying PostgreSQL ==="

    kubectl create configmap postgres-init \
      --from-file=init.sql=./infrastructure/postgres/init.sql \
      --dry-run=client -o yaml | kubectl apply -f -

    kubectl apply -f k8s/postgres-service.yaml
    kubectl apply -f k8s/postgres-statefulset.yaml

    echo "=== Waiting for PostgreSQL ==="

    kubectl rollout status statefulset/postgres --timeout=180s
}

start_redis() {
    echo "=== Deploying Redis ==="

    kubectl apply -f k8s/redis-service.yaml
    kubectl apply -f k8s/redis-deployment.yaml

    echo "=== Waiting for Redis ==="

    kubectl rollout status deployment/redis --timeout=120s
}

start_telemetry() {
    echo "=== Loading image into Minikube ==="
    minikube image load iot-telemetry:latest

    echo "=== Deploying telemetry ==="
    kubectl apply -f k8s/telemetry-service.yaml
    kubectl apply -f k8s/telemetry-deployment.yaml

    kubectl rollout restart deployment/telemetry

    kubectl rollout status deployment/telemetry --timeout=120s
}

start_analytics() {

    minikube image load iot-analytics-consumer:latest

    echo "=== Deploying analytics consumer ==="

    kubectl apply -f k8s/analytics-consumer-deployment.yaml

    kubectl rollout restart deployment/analytics-consumer
    kubectl rollout status deployment/analytics-consumer --timeout=120s

    minikube image load iot-analytics:latest

    echo "=== Deploying analytics API ==="
    kubectl apply -f k8s/analytics-service.yaml
    kubectl apply -f k8s/analytics-deployment.yaml

    kubectl rollout restart deployment/analytics
    kubectl rollout status deployment/analytics --timeout=120s
}

cd "$(dirname "$0")/.."

echo "=== Starting Minikube ==="
minikube start --driver=docker

echo "=== Configuring kubectl context ==="
minikube update-context
kubectl config use-context minikube

start_kafka
start_postgres
start_redis
start_telemetry
start_analytics

echo "=== Configuring local access ==="

start_port_forward telemetry 8000
start_port_forward analytics 8001

echo
echo "=== Kubernetes environment ready ==="
echo "Telemetry: http://localhost:8000"
echo "Analytics: http://localhost:8001"
echo "Kafka: kafka:29092 (inside Kubernetes)"
echo "Topic: measurements"
echo
echo "Run your simulator in another terminal."