# komodocicdtest1 – Edge AI Detection Stack (Komodo CI/CD POC)

A minimal proof-of-concept that demonstrates using **GitHub Actions** +
**Komodo** (via WebHooks) to automatically update a fleet of edge computers
running this Docker Compose stack.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Docker Compose Stack                                         │
│                                                               │
│  ┌──────────────┐   detections/raw   ┌──────────────────┐   │
│  │  mock-       │ ──────────────────▶│  alert-filter    │   │
│  │  inference   │                    │  (Redpanda        │   │
│  │  (Python)    │                    │   Connect)        │   │
│  └──────┬───────┘                    └────────┬─────────┘   │
│         │                                     │ alerts       │
│         ▼                                     ▼              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Eclipse Mosquitto MQTT Broker           │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

| Service | Image | Role |
|---|---|---|
| `mosquitto` | `eclipse-mosquitto:2.0` | MQTT broker – central data bus |
| `mock-inference` | *(built locally)* | Simulates a video AI detector; publishes JSON detections to `detections/raw` |
| `alert-filter` | `docker.redpanda.com/redpandadata/connect:latest` | Reads `detections/raw`, filters events with `confidence ≥ 0.75`, republishes actionable alerts to `alerts` |

## Quick Start

```bash
docker compose up --build
```

Subscribe to alerts in a separate terminal:

```bash
mosquitto_sub -h localhost -t alerts -v
```

Subscribe to all raw detections:

```bash
mosquitto_sub -h localhost -t detections/raw -v
```

## Configuration

| File | Purpose |
|---|---|
| `mosquitto/config/mosquitto.conf` | Mosquitto broker settings |
| `mock-inference/inference.py` | Detection simulator source |
| `mock-inference/Dockerfile` | Container build for the simulator |
| `redpanda-connect/pipeline.yaml` | Benthos/Redpanda Connect pipeline (filter logic) |
| `docker-compose.yml` | Compose stack wiring all services together |

### Environment variables (mock-inference)

| Variable | Default | Description |
|---|---|---|
| `MQTT_BROKER_HOST` | `mosquitto` | Broker hostname |
| `MQTT_BROKER_PORT` | `1883` | Broker port |
| `MQTT_PUBLISH_TOPIC` | `detections/raw` | Topic to publish detections on |
| `PUBLISH_INTERVAL_SECONDS` | `3` | Seconds between detections |
| `ALERT_CONFIDENCE_THRESHOLD` | `0.75` | Informational threshold (filtering done in Redpanda Connect) |
| `CAMERA_ID` | `cam-01` | Camera identifier included in each payload |

## CI/CD with Komodo

GitHub Actions triggers a Komodo WebHook on every push to `main`.  Komodo
then pulls the latest image / compose file on each registered edge device,
ensuring the entire fleet is updated automatically.