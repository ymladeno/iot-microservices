import random
import time
from datetime import datetime, timezone

import requests

SERVER_URL = "http://localhost:8000/measurements"
DEVICE_IDS = [101, 102, 103, 104, 105]
INTERVAL = 3  # seconds

def generate_measurement(device_id):
    return {
        "device_id": device_id,
        "temperature": round(random.uniform(18.0, 35.0), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def send_measurement(measurement):
    try:
        response = requests.post(
            SERVER_URL,
            json=measurement,
            timeout=5
        )
        response.raise_for_status()
        print(f"Sent: {measurement} | Status: {response.status_code}")

    except requests.RequestException as error:
        print(f"Failed to send measurement: {error}")

def main():
    print("Starting IoT device simulator...")

    try:
        while True:
            for device_id in DEVICE_IDS:
                measurement = generate_measurement(device_id)
                send_measurement(measurement)

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
