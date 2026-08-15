# komodocicdtest1 – Edge AI Detection Stack (Komodo CI/CD POC)

# Edit to force webhook to Komodo 1

A minimal proof-of-concept that demonstrates using **GitHub Actions** +
**Komodo** (via WebHooks) to automatically update a fleet of edge computers
running this Docker Compose stack.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Docker Compose Stack                                         │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  alert-filter (Redpanda Connect)                      │    │
│  │  reads detections/raw → filters → publishes alerts   │    │
│  └────────────────────────┬─────────────────────────────┘    │
│                            │ alerts                           │
│                            ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Eclipse Mosquitto MQTT Broker           │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

| Service | Image | Role |
|---|---|---|
| `mosquitto` | `eclipse-mosquitto:2.0` | MQTT broker – central data bus |
| `alert-filter` | `docker.redpanda.com/redpandadata/connect:latest` | Reads `detections/raw`, filters events with `confidence ≥ 0.75`, republishes actionable alerts to `alerts` |

## Quick Start

```bash
docker compose up
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
| `redpanda-connect/pipeline.yaml` | Benthos/Redpanda Connect pipeline (filter logic) |
| `docker-compose.yml` | Compose stack wiring all services together |

## CI/CD with Komodo

GitHub Actions triggers a Komodo WebHook on every push to `main`.  Komodo
then pulls the latest image / compose file on each registered edge device,
ensuring the entire fleet is updated automatically.
