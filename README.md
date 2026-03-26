# Backend Developer Assessment — Customer Data Pipeline

A data pipeline built with 3 Docker services:

| Service | Stack | Port |
|---|---|---|
| **mock-server** | Flask | 5000 |
| **pipeline-service** | FastAPI + dlt + SQLAlchemy | 8000 |
| **postgres** | PostgreSQL 15 | 5432 |

**Flow**: `Flask (JSON) → FastAPI (dlt ingest) → PostgreSQL → API Response`

---

## Prerequisites

- Docker Desktop (running)
- Docker Compose v2+

---

## Quick Start

```bash
# Clone and start all services
git clone https://github.com/dikyayodihamzah/backend-assessment.git
cd backend-assessment
docker-compose up -d --build
```

Wait ~10 seconds for services to be ready, then:

```bash
# Ingest customers from Flask into PostgreSQL
curl -X POST "http://localhost:8000/api/ingest"
# {"status":"success","records_processed":25}

# Query customers from the pipeline service (paginated)
curl "http://localhost:8000/api/customers?page=1&limit=5"

# Get a single customer
curl "http://localhost:8000/api/customers/CUST-001"

# Directly query the mock server
curl "http://localhost:5000/api/customers?page=1&limit=5"
```

---

## API Reference

### Mock Server (port 5000)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/customers` | Paginated customer list (`page`, `limit`) |
| `GET` | `/api/customers/{id}` | Single customer or `404` |

### Pipeline Service (port 8000)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/ingest` | Fetch all data from Flask and upsert to PostgreSQL |
| `GET` | `/api/customers` | Paginated customers from database (`page`, `limit`) |
| `GET` | `/api/customers/{id}` | Single customer from database or `404` |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Project Structure

```text
backend-assessment/
├── docker-compose.yml
├── README.md
├── mock-server/
│   ├── app.py                  # Flask REST API
│   ├── data/customers.json     # 25 customer records
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py                 # FastAPI app + endpoints
    ├── database.py             # SQLAlchemy engine + session
    ├── models/
    │   └── customer.py         # SQLAlchemy ORM model + Pydantic schemas
    ├── services/
    │   └── ingestion.py        # dlt resource + upsert pipeline
    ├── Dockerfile
    └── requirements.txt
```

---

## Architecture Notes

- **dlt** is used as the pipeline abstraction layer — the `@dlt.resource` decorator defines the data source with `primary_key` and `write_disposition`, while auto-pagination pulls all pages from the Flask API.
- **SQLAlchemy** handles table creation (on startup) and query operations. Upserts use PostgreSQL's `INSERT ... ON CONFLICT DO UPDATE` via `sqlalchemy.dialects.postgresql.insert`.
- **Docker health checks** on PostgreSQL ensure dependent services only start when the database is ready.
- The pipeline is **idempotent** — running `POST /api/ingest` multiple times safely upserts without creating duplicates.

---

## Stopping Services

```bash
docker-compose down          # stop containers
docker-compose down -v       # stop containers and remove volumes
```
