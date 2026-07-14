# Manufacturing Reconciliation System

## Purpose

The Manufacturing Reconciliation System monitors barcode data coming from multiple
manufacturing machines — AOI, SPI, and FCR. It performs real-time reconciliation,
identifies missing barcodes between machines, calculates production metrics including
Good/Bad split and FCR rework coverage, and displays everything on a live dashboard
that updates automatically via Server-Sent Events with no browser polling.

---

## Architecture

```
CSV Files (AOI / SPI / FCR machines)
   │
   ▼
Node-RED (file watchers)
   │  publishes JSON with barcode, result (GOOD/BAD), sourceType
   ▼
Kafka Topics
   aoi1-topic, aoi2-topic
   spi1-topic, spi2-topic
   fcr2-topic
   │
   ▼
PyFlink Reconciliation Job
   │
   ├──► Redis ZSETs (barcodes per machine per window)
   │    line:{LINE}:{MACHINE}:{window_id}
   │    line:{LINE}:{MACHINE}:GOOD:{window_id}   ← SPI only
   │    line:{LINE}:{MACHINE}:BAD:{window_id}    ← SPI only
   │
   ├──► Window Manager (24h tumbling windows)
   │    window:{LINE} → window_id, start_ms, end_ms
   │    Each window is isolated — data never bleeds across days
   │
   ├──► Redis Metrics Hash
   │    metrics:{LINE}              (live — always current window)
   │    metrics:{LINE}:{window_id}  (historical snapshot per window)
   │
   └──► Redis Pub/Sub  (channel: line_events)
           LINE_ACTIVE published on first barcode
           LINE_IDLE published by Watchdog after 30s silence
   │
   ├──► Watchdog Service
   │    Polls processing:* keys every 5s
   │    Publishes LINE_IDLE on ACTIVE → IDLE transition only
   │
   ├──► Aggregation Service
   │    Subscribes to line_events via pubsub.listen()
   │    Writes status:{LINE} → { state: ACTIVE/IDLE, since: timestamp }
   │    Zero CPU when idle — blocks at OS level until event arrives
   │
   ▼
Flask API (port 5000)
   │  REST endpoints + /events SSE stream
   │  Pushes full snapshot on every Redis Pub/Sub event
   ▼
React Dashboard (port 3000)
   EventSource("/events") — one persistent connection, no polling
```

---

## Key Features

- **Real-time reconciliation** — barcodes compared across AOI, SPI, FCR as they arrive
- **Dynamic machine support** — add machines or production lines in `config.env` only, no code changes required
- **24-hour tumbling windows** — each production day is isolated; barcodes from one window never affect the next
- **SPI Good / Bad split** — barcodes marked GOOD or BAD by SPI inspection; each stored in separate Redis ZSETs
- **FCR rework reconciliation** — FCR is a dependent rework station; system tracks which SPI Bad barcodes reached FCR and which are missing
- **Idle detection** — Watchdog marks lines IDLE after 30 seconds of silence, fires LINE_ACTIVE on reactivation
- **Event-driven architecture** — Redis Pub/Sub drives all state updates throughout the pipeline; no polling loops anywhere in the backend
- **Server-Sent Events** — dashboard updates in real time via SSE; no `setInterval` or repeated HTTP requests
- **Global loss metrics** — per-machine coverage calculated against the full unique barcode pool across all machines
- **Pairwise comparison** — dynamic AOI↔SPI, AOI↔FCR, SPI↔FCR match and loss percentages generated automatically via `itertools.combinations`
- **Alert system** — Critical (≥50% loss) and Warning (≥20% loss) alerts shown on dashboard for both pairwise and global losses
- **Machine health scores** — per-machine health bar based on global coverage percentage

---

## Folder Structure

```
manufacturing-reconciliation-system/
│
├── flink-jobs/                    PyFlink processing layer
│   ├── pyflink_reconciliation.py  Main Flink job — Kafka → Redis
│   ├── update_metrics.py          Reconciliation engine (dynamic, pairwise, rework)
│   ├── window_manager.py          24h tumbling window management
│   ├── redis_events.py            Processing state + Pub/Sub helpers
│   ├── aggregation_service.py     Redis Pub/Sub subscriber
│   ├── watchdog.py                Idle line detection service
│   ├── load_config.py             Reads config.env, builds topics + lines dicts
│   └── config.env                 Single source of truth for all configuration
│
├── flask-api/                     REST API + SSE service
│   └── app.py                     6 REST endpoints + /events SSE stream
│
├── frontend/                      React dashboard (Vite + React)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AlertPanel.jsx
│   │   │   ├── ComparisonCard.jsx
│   │   │   ├── DashboardContent.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── MachineHealth.jsx
│   │   │   ├── ProductionLines.jsx
│   │   │   ├── ReworkPanel.jsx
│   │   │   └── SummaryCards.jsx
│   │   ├── pages/
│   │   │   └── Dashboard.jsx
│   │   └── services/
│   │       └── api.js
│   ├── Dockerfile
│   └── nginx.conf
│
├── flink-lib/                     Kafka connector JARs for Flink
│   ├── flink-connector-kafka-3.0.2-1.18.jar
│   └── kafka-clients-3.5.1.jar
│
├── flink/                         Flink configuration
│   └── flink-conf.dev.yaml
│
├── nodered-data/                  Node-RED flow persistence
├── real-data/                     Sample CSV files for testing
│   ├── AOI/
│   ├── SPI/
│   └── FCR/
│
├── docs/                          Full documentation
├── Dockerfile.flink               Custom Flink image with Python + redis + dotenv
├── docker-compose.yml
└── README.md
```

---

## Requirements

- Docker Desktop (Windows / Mac) **or** Docker Engine + Docker Compose (Linux)
- Git (optional — only needed if cloning rather than unzipping)

No need to install Python, Node.js, Kafka, Redis, or Flink manually.
Everything runs inside Docker containers.

---

## Configuration

All machine and topic configuration lives in a single file: `flink-jobs/config.env`

```dotenv
# Kafka Topics
AOI_TOPICS=aoi1-topic,aoi2-topic
SPI_TOPICS=spi1-topic,spi2-topic
FCR_TOPICS=fcr2-topic

# Production Lines  (format: TYPE|MachineName)
LINE1=AOI|AOI3D1,SPI|SPI1
LINE2=AOI|AOI2,SPI|SPI2,FCR|FCR2
```

**To add a new machine:** append it to a line definition — e.g. `LINE2=AOI|AOI2,SPI|SPI2,FCR|FCR2,ICT|ICT1`

**To add a new production line:** add a new `LINE3=...` entry.

No Python, Redis, or frontend code changes are required — the system reads this file
dynamically at startup and all components adapt automatically.

---

## Kafka Message Format

Each barcode message published from Node-RED to Kafka:

```json
{
  "line": "LINE2",
  "machine": "SPI2",
  "sourceType": "SPI",
  "barcode": "PIR22606020007T",
  "result": "GOOD",
  "timestamp_ms": 1783839750444
}
```

- `sourceType` — `AOI`, `SPI`, or `FCR`. Used by PyFlink to route storage logic.
- `result` — `GOOD` or `BAD`. Required for SPI only. FCR and AOI do not need this field.

---

## Redis Data Model

| Key Pattern | Type | Purpose |
|---|---|---|
| `line:{LINE}:{MACHINE}:{window_id}` | ZSET | All barcodes for a machine in a window (member=barcode, score=timestamp ms) |
| `line:{LINE}:{MACHINE}:GOOD:{window_id}` | ZSET | SPI Good barcodes only |
| `line:{LINE}:{MACHINE}:BAD:{window_id}` | ZSET | SPI Bad barcodes only — expected at FCR |
| `metrics:{LINE}` | Hash | Live metrics — always mirrors current window |
| `metrics:{LINE}:{window_id}` | Hash | Historical metrics snapshot per window |
| `processing:{LINE}` | Hash | state, started_at, last_activity, message_count |
| `status:{LINE}` | Hash | ACTIVE or IDLE + since timestamp |
| `window:{LINE}` | Hash | window_id, start_ms, end_ms |

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Redis connectivity + service version |
| `/api/lines` | GET | List of configured production lines |
| `/api/reconciliation` | GET | All metrics for all lines |
| `/api/reconciliation/<line>` | GET | Metrics for a single line |
| `/api/summary` | GET | Totals and overall match % per line |
| `/api/status` | GET | ACTIVE / IDLE state per line with timestamp |
| `/events` | GET | SSE stream — pushes snapshot on every Redis Pub/Sub event |

---

## Services

| Service | Container | Port | Role |
|---|---|---|---|
| Zookeeper | `zookeeper` | 2181 | Kafka coordination |
| Kafka | `kafka` | 9092 | Message broker (5 topics) |
| Kafka Init | `kafka-init` | — | Creates topics on startup, then exits |
| Redis | `redis` | 6379 | Barcode storage, metrics, Pub/Sub, window state |
| Flink JobManager | `flink-jobmanager` | 8081 | Flink cluster manager |
| Flink TaskManager | `flink-taskmanager` | — | Executes the PyFlink reconciliation job |
| Flink Job Submitter | `flink-job-submitter` | — | Submits job on startup, then exits |
| Watchdog | `flink-watchdog` | — | Idle detection — publishes LINE_IDLE after 30s silence |
| Aggregation Service | `flink-aggregation` | — | Pub/Sub subscriber — writes status keys |
| Flask API | `flask-api` | 5000 | REST endpoints + SSE stream |
| Node-RED | `nodered` | 1880 | CSV file watchers — publishes barcodes to Kafka |
| Frontend | `frontend` | 3000 | React dashboard served via nginx |

---

## Setup

1. Extract the zip or clone the repository:
   ```bash
   git clone <repo-url>
   cd manufacturing-reconciliation-system
   ```

2. Verify `flink-jobs/config.env` matches your machine configuration (default values work for testing).

3. Open a terminal in the project root.

---

## Run

```bash
docker compose up --build
```

First build may take several minutes while images download. Subsequent runs are faster.

To run in the background:
```bash
docker compose up --build -d
```

---

## Access

| Service | URL |
|---|---|
| **Dashboard** | http://localhost:3000 |
| **Flask API** | http://localhost:5000 |
| **Node-RED** | http://localhost:1880 |
| **Flink UI** | http://localhost:8081 |

---

## Sending Test Data

1. Open Node-RED at http://localhost:1880
2. Trigger the inject nodes for AOI, SPI, and FCR flows simultaneously
3. Watch the dashboard at http://localhost:3000 update in real time
4. After 30 seconds of no data, the line badges will flip to **Idle** automatically

To start fresh with clean data:
```bash
docker exec -it redis redis-cli FLUSHDB
```
Then re-trigger the Node-RED inject nodes.

---

## Stopping

```bash
docker compose down
```

To also wipe all stored Redis and Kafka state for a completely clean restart:
```bash
docker compose down -v
```

---

## How the 24h Window Works

Each production line maintains a rolling 24-hour window stored in Redis:

```
Window 1: 09:00 Day 1 → 09:00 Day 2  (barcodes stored in :1 keys)
Window 2: 09:00 Day 2 → 09:00 Day 3  (barcodes stored in :2 keys)
```

When the first barcode of a new day arrives after the window has expired:
1. `window_manager.py` detects the expiry
2. Previous window's Redis keys are deleted
3. A new window ID is created
4. All subsequent barcodes go into the new window's keys

The live `metrics:{LINE}` key always mirrors the current window so all API
endpoints and the dashboard work without any changes.

---

## FCR Rework Flow

FCR is not a parallel inspection machine — it is a **dependent rework station**:

```
SPI inspects all barcodes
    ↓
GOOD barcodes → pass, no further action needed
BAD barcodes  → physically sent to FCR for rework
                FCR generates its own CSV by scanning those barcodes

Rework loss = BAD barcodes that never reached FCR
            = SPI BAD set  -  FCR received set
```

The dashboard shows:
- SPI Good / Bad split bar with counts and percentages
- FCR rework coverage (how many bad barcodes FCR received vs expected)
- Rework loss percentage
- Popup lists for: all Bad barcodes, and specifically which Bad barcodes are missing at FCR

---

## Troubleshooting

**Port already in use**
Make sure nothing else is running on ports 3000, 5000, 6379, 8081, 1880, or 9092.

**Build fails on first run**
```bash
docker compose down -v
docker compose up --build
```

**Dashboard loads but shows no data**
- Confirm Node-RED inject nodes have been triggered
- Check Kafka topics in `config.env` match what Node-RED is publishing to
- Run `docker logs flink-taskmanager` to see if barcodes are being processed

**Metrics show stale or accumulated data**
```bash
docker exec -it redis redis-cli FLUSHDB
```
Then re-inject data from Node-RED.

**Flink job not running**
```bash
docker logs flink-job-submitter   # check if JobID was printed
docker logs flink-taskmanager     # check for processing output or errors
```

**SPI Good / Bad split not appearing on dashboard**
Confirm the Node-RED SPI function node includes both fields in the published JSON:
```javascript
result: msg.payload.PCBResult,   // maps PCBResult → result
sourceType: "SPI",               // must be exactly "SPI"
```

**FCR rework panel not appearing**
The rework panel only renders when `spi_total_barcodes > 0`.
SPI data with the `result` field must arrive and be processed before the panel appears.

**SSE connection not working / dashboard not updating**
Check `docker logs flask-api` for errors. The `/events` endpoint requires
`proxy_buffering off` in nginx — confirm `frontend/nginx.conf` has this setting.

**Line stays ACTIVE after data stops**
The Watchdog fires LINE_IDLE after 30 seconds of silence. Check it is running:
```bash
docker logs -f flink-watchdog
```

---

## Documentation

Full documentation is in the `docs/` folder:

| File | Contents |
|---|---|
| `01_Project_Overview.md` | Business problem and goals |
| `02_System_Architecture.md` | Full architecture with diagrams |
| `03_Data_Flow.md` | End-to-end barcode flow |
| `04_Project_Structure.md` | Folder and file breakdown |
| `05_Configuration.md` | config.env reference |
| `06_Redis_Design.md` | Redis key schema and data model |
| `07_Flink_Workflow.md` | PyFlink job internals |
| `08_API_Documentation.md` | All Flask endpoints with examples |
| `09_Frontend.md` | React component architecture |
| `10_Run_Project.md` | Detailed startup and testing guide |
| `11_Demo.md` | Step-by-step demo walkthrough |

---

## Demo

See `docs/11_Demo.md` for a step-by-step walkthrough of the complete pipeline,
or watch the included demo video (shared separately).

---

## Contact

For questions, reach out to [your name / contact info].