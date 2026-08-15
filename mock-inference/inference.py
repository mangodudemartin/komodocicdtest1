"""
Mock Video AI Inference Container
----------------------------------
Simulates a video AI detection process that publishes detection events to
the MQTT topic `detections/raw`. Detections vary in confidence score so
that the downstream alert filter can distinguish actionable from routine
events.
"""

import json
import os
import random
import time

import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", "1883"))
PUBLISH_TOPIC = os.environ.get("MQTT_PUBLISH_TOPIC", "detections/raw")
PUBLISH_INTERVAL = float(os.environ.get("PUBLISH_INTERVAL_SECONDS", "3"))

# Detection classes that the mock "model" can return
DETECTION_CLASSES = [
    "person",
    "vehicle",
    "bicycle",
    "animal",
    "package",
    "fire",
    "smoke",
]

# Alert threshold used just for logging context here; filtering happens in
# Redpanda Connect, not in this container.
ALERT_THRESHOLD = float(os.environ.get("ALERT_CONFIDENCE_THRESHOLD", "0.75"))


def build_detection() -> dict:
    """Return a single randomly-generated detection payload."""
    label = random.choice(DETECTION_CLASSES)
    confidence = round(random.uniform(0.30, 0.99), 3)
    return {
        "timestamp": time.time(),
        "label": label,
        "confidence": confidence,
        "bounding_box": {
            "x": random.randint(0, 1280),
            "y": random.randint(0, 720),
            "width": random.randint(20, 400),
            "height": random.randint(20, 400),
        },
        "camera_id": os.environ.get("CAMERA_ID", "cam-01"),
    }


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[inference] Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[inference] Failed to connect, return code {rc}")


def main():
    client = mqtt.Client(client_id="mock-inference")
    client.on_connect = on_connect

    while True:
        try:
            client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
            break
        except Exception as exc:
            print(f"[inference] Broker not ready ({exc}), retrying in 5 s …")
            time.sleep(5)

    client.loop_start()

    print(
        f"[inference] Publishing detections to '{PUBLISH_TOPIC}' "
        f"every {PUBLISH_INTERVAL} s"
    )

    while True:
        detection = build_detection()
        payload = json.dumps(detection)
        msg_info = client.publish(PUBLISH_TOPIC, payload, qos=1)
        try:
            msg_info.wait_for_publish(timeout=5)
        except Exception as exc:
            print(f"[inference] Publish failed: {exc}")
            time.sleep(PUBLISH_INTERVAL)
            continue
        status = "HIGH" if detection["confidence"] >= ALERT_THRESHOLD else "low"
        print(
            f"[inference] [{status}] {detection['label']} "
            f"confidence={detection['confidence']} → {PUBLISH_TOPIC}"
        )
        time.sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    main()
