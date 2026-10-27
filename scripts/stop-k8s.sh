#!/usr/bin/env bash
set -euo pipefail

echo "=== Stopping port-forwards ==="

for service in telemetry analytics; do
    pid_file="/tmp/iot-microservices-${service}-forward.pid"

    if [[ -f "$pid_file" ]]; then
        pid=$(cat "$pid_file")

        if kill -0 "$pid" 2>/dev/null &&
           ps -p "$pid" -o args= |
               grep -q "kubectl port-forward service/${service}"; then
            kill "$pid"
        fi

        rm -f "$pid_file"
    fi
done

echo "=== Stopping Minikube ==="
minikube stop

echo "=== Done ==="