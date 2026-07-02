# Manufacturing Reconciliation System

## Purpose

The Manufacturing Reconciliation System monitors barcode data coming from multiple
manufacturing machines such as AOI, SPI, and FCR. It performs real-time reconciliation,
identifies missing products between machines, calculates production metrics, and
displays the results on a live dashboard.

## Architecture

```
CSV Files
   │
   ▼
Node-RED
   │
   ▼
Kafka
   │
   ▼
PyFlink
   │
   ├──► Redis Sets
   ├──► Redis Metrics
   └──► Redis Pub/Sub
   │
   ▼
Aggregation Service
   │
   ▼
Flask API
   │
   ▼
React Dashboard
```

See `docs/02_System_Architecture.md` for details.

## Folder Structure

```
manufacturing-reconciliation-system/
├── flask-api/        REST API service
├── flink-jobs/        PyFlink reconciliation jobs
├── frontend/          React dashboard
├── monitoring/         Watchdog services
├── node-red/           Node-RED flows
├── real-data/           Sample CSV files for testing
├── docs/                Full documentation
├── scripts/              start.sh / stop.sh helpers
├── docker-compose.yml
├── config.env.example
└── README.md
```

Full breakdown in `docs/04_Project_Structure.md`.

## Requirements

- Docker Desktop (Windows/Mac) **or** Docker Engine + Docker Compose (Linux)
- Git (optional — only needed if cloning rather than unzipping)

No need to install Python, Node, Kafka, Redis, or Flink manually — everything
runs inside Docker containers.

## Setup

1. Extract `manufacturing-reconciliation-system.zip` (or `git clone` the repo)
2. Copy the example config and adjust values if needed:
   ```bash
   cp config.env.example config.env
   ```
3. Open a terminal in the project root folder

## Run

```bash
docker compose up --build
```

Or, using the helper script:
```bash
./scripts/start.sh
```

First build may take a few minutes while images download and compile. Subsequent
runs are faster.

## Access

- **Dashboard:** http://localhost:3000
- **API:** http://localhost:5000

## Services

| Service               | Role                                      |
|-----------------------|--------------------------------------------|
| Kafka                 | Message broker for barcode events          |
| Redis                 | State store and pub/sub                    |
| PyFlink                | Stream processing / reconciliation logic   |
| Watchdog               | Detects idle production lines              |
| Aggregation Service     | Listens for Redis events, aggregates data |
| Flask API               | Serves reconciliation data to frontend    |
| React Frontend           | Live dashboard                          |

## Stopping

```bash
docker compose down
```

Or:
```bash
./scripts/stop.sh
```

To also wipe stored data (Redis/Kafka state) and start fully fresh next time:
```bash
docker compose down -v
```

## Documentation

Full documentation is in the `docs/` folder:

- `01_Project_Overview.md`
- `02_System_Architecture.md`
- `03_Data_Flow.md`
- `04_Project_Structure.md`
- `05_Configuration.md`
- `06_Redis_Design.md`
- `07_Flink_Workflow.md`
- `08_API_Documentation.md`
- `09_Frontend.md`
- `10_Run_Project.md`
- `11_Demo.md`

## Demo

See `docs/11_Demo.md` for a step-by-step walkthrough, or watch the included demo
video (link/file shared separately).

## Troubleshooting

- **Port already in use:** make sure nothing else is running on 3000, 5000, or
  Kafka/Redis default ports before starting.
- **Build fails on first run:** try `docker compose down -v` then
  `docker compose up --build` again for a clean rebuild.
- **Dashboard loads but shows no data:** confirm Node-RED is injecting data and
  Kafka topics match what's set in `config.env`.

## Contact

For questions, reach out to [your name / contact info].