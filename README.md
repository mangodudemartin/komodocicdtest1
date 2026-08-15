# komodocicdtest1 – Edge AI Detection Stack (Komodo CI/CD POC)

# Edit to force webhook to Komodo 3

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

The promotion flow is:

1. Developers push changes to `stage`
2. GitHub Actions runs the stage validation workflow
3. After the workflow succeeds, GitHub Actions creates a pull request from `stage` into `main`
4. A developer reviews and merges that pull request before anything lands on `main`
