# Customer Data Pipeline

A containerized data pipeline that ingests customer records from a mock data source into PostgreSQL, exposing a queryable REST API on top.

| Service | Stack | Port |
|---|---|---|
| **mock-server** | Flask | 5001 |
| **pipeline-service** | FastAPI + dlt + SQLAlchemy | 8000 |
| **postgres** | PostgreSQL 15 | 5432 |

**Flow**: `Mock Server (JSON) → Pipeline Service (dlt ingest) → PostgreSQL → REST API`

---

## Prerequisites

- Docker Desktop (running)
- Docker Compose v2+

---

## Quick Start

```bash
git clone https://github.com/dikyayodihamzah/customer-data-pipeline.git
cd customer-data-pipeline
docker compose up -d --build
```

Wait ~10 seconds for services to be ready, then trigger the first ingestion:

```bash
curl -X POST "http://localhost:8000/api/ingest"
# {"status":"success","records_processed":25}
```

---

## API Reference

### Mock Server (port 5001)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/customers` | Paginated customer list (`page`, `limit`) |
| `GET` | `/api/customers/{id}` | Single customer or `404` |

### Pipeline Service (port 8000)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/ingest` | Fetch all records from mock server and upsert into PostgreSQL |
| `GET` | `/api/customers` | Paginated customers from database (`page`, `limit`) |
| `GET` | `/api/customers/{id}` | Single customer from database or `404` |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Usage Examples

```bash
# Ingest all customer data
curl -X POST "http://localhost:8000/api/ingest"

# Query customers with pagination
curl "http://localhost:8000/api/customers?page=1&limit=10"

# Get a single customer
curl "http://localhost:8000/api/customers/CUST-001"

# Query the mock server directly
curl "http://localhost:5001/api/customers?page=1&limit=5"
```

---

## Project Structure

```text
customer-data-pipeline/
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

- **dlt** is used as the pipeline abstraction layer — the `@dlt.resource` decorator defines the data source with `primary_key` and handles auto-pagination across all pages from the mock server.
- **SQLAlchemy** manages table creation on startup and all query operations. Upserts use PostgreSQL's `INSERT ... ON CONFLICT DO UPDATE` via `sqlalchemy.dialects.postgresql.insert`.
- **Docker health checks** on PostgreSQL ensure dependent services only start once the database is ready.
- The pipeline is **idempotent** — running `POST /api/ingest` multiple times safely upserts without creating duplicates.

---

## Stopping Services

```bash
docker compose down      # stop containers
docker compose down -v   # stop containers and remove volumes
```
