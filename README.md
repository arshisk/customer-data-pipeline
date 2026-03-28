# Customer Data Pipeline 🚀

A production-style data pipeline built with Flask, FastAPI, PostgreSQL, and Docker.

---

## Overview

This project implements a 3-service data pipeline:

```
Flask Mock Server → FastAPI Pipeline → PostgreSQL Database
  (Data Source)       (Processor)        (Storage)
```

- **Flask** serves 20 fake customers from a JSON file
- **FastAPI** fetches that data, stores it in PostgreSQL, and exposes query endpoints
- **PostgreSQL** stores the data permanently
- **Docker Compose** runs all 3 services together

---

## Architecture

```
┌─────────────────┐     GET /api/customers      ┌──────────────────────┐
│                 │ ◄─────────────────────────── │                      │
│   Flask Mock    │                              │   FastAPI Pipeline   │
│   Server        │ ──────────────────────────►  │   Service            │
│   Port: 5000    │     JSON customer data       │   Port: 8000         │
│                 │                              │                      │
└─────────────────┘                              └──────────┬───────────┘
                                                            │
                                                            │ SQLAlchemy
                                                            │ Upsert
                                                            ▼
                                                 ┌──────────────────────┐
                                                 │                      │
                                                 │     PostgreSQL       │
                                                 │     Port: 5432       │
                                                 │     customer_db      │
                                                 │                      │
                                                 └──────────────────────┘
```

---

## Tech Stack

| Service           | Technology              | Port |
|-------------------|-------------------------|------|
| Mock Data Server  | Python 3.13 + Flask     | 5000 |
| Pipeline API      | Python 3.13 + FastAPI   | 8000 |
| Database          | PostgreSQL 15           | 5432 |
| Containerization  | Docker + Docker Compose | —    |

---

## Project Structure

```
customer-data-pipeline/
├── docker-compose.yml              # Runs all 3 services together
├── README.md                       # This file
├── .gitignore                      # Files to exclude from Git
│
├── mock-server/                    # Flask mock data server
│   ├── app.py                      # Flask routes and pagination logic
│   ├── Dockerfile                  # Container build instructions
│   ├── requirements.txt            # Python dependencies
│   └── data/
│       └── customers.json          # 20 fake customers (data source)
│
└── pipeline-service/               # FastAPI ingestion + query service
    ├── main.py                     # All FastAPI endpoints
    ├── database.py                 # PostgreSQL connection setup
    ├── Dockerfile                  # Container build instructions
    ├── requirements.txt            # Python dependencies
    ├── models/
    │   ├── __init__.py
    │   └── customer.py             # SQLAlchemy customer table model
    └── services/
        ├── __init__.py
        └── ingestion.py            # Fetch from Flask + upsert to DB
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (must be running)
- [Git](https://git-scm.com/)

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/customer-data-pipeline.git
cd customer-data-pipeline
```

### 2. Start all services
```bash
docker-compose up --build
```

### 3. Wait for all 3 services to be ready
You should see:
```
mock_server       | [INFO] Listening at: http://0.0.0.0:5000
pipeline_service  | INFO:     Application startup complete.
```

### 4. Run the ingest to load data
```bash
curl -X POST http://localhost:8000/api/ingest
```

---

## API Reference

### Mock Server (Port 5000)

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| GET    | /api/health                 | Health check                       |
| GET    | /api/customers              | Paginated customer list            |
| GET    | /api/customers/{id}         | Single customer by ID              |

### Pipeline Service (Port 8000)

| Method | Endpoint                    | Description                        |
|--------|-----------------------------|------------------------------------|
| GET    | /api/health                 | Health check                       |
| POST   | /api/ingest                 | Fetch from Flask + save to DB      |
| GET    | /api/customers              | Paginated customers from DB        |
| GET    | /api/customers/{id}         | Single customer from DB            |

---

## Testing All Endpoints

### Health Checks
```bash
curl http://localhost:5000/api/health
curl http://localhost:8000/api/health
```

### Flask Mock Server
```bash
# Get all customers (page 1, 10 per page)
curl http://localhost:5000/api/customers

# Get page 2 with 5 per page
curl "http://localhost:5000/api/customers?page=2&limit=5"

# Get single customer
curl http://localhost:5000/api/customers/CUST001

# Test 404
curl http://localhost:5000/api/customers/CUST999
```

### FastAPI Pipeline Service
```bash
# Ingest all data from Flask into PostgreSQL
curl -X POST http://localhost:8000/api/ingest

# Get all customers from database
curl http://localhost:8000/api/customers

# Get page 2 with 5 per page
curl "http://localhost:8000/api/customers?page=2&limit=5"

# Get single customer from database
curl http://localhost:8000/api/customers/CUST001

# Test 404
curl http://localhost:8000/api/customers/CUST999
```

---

## Environment Variables

| Variable       | Service          | Value                                               |
|----------------|------------------|-----------------------------------------------------|
| DATABASE_URL   | pipeline-service | postgresql://postgres:password@postgres:5432/customer_db |
| FLASK_BASE_URL | pipeline-service | http://mock-server:5000                             |
| POSTGRES_USER  | postgres         | postgres                                            |
| POSTGRES_PASSWORD | postgres      | password                                            |
| POSTGRES_DB    | postgres         | customer_db                                         |

---

## Common Issues & Fixes

**1. Port already in use**
```bash
# Stop all containers and try again
docker-compose down
docker-compose up --build
```

**2. Pipeline service can't connect to PostgreSQL**
```bash
# Check if postgres container is healthy
docker ps
# Wait a few seconds and retry — postgres needs time to initialize
```

**3. Ingest returns error**
```bash
# Make sure mock-server is running first
curl http://localhost:5000/api/health
# Then retry ingest
curl -X POST http://localhost:8000/api/ingest
```

**4. Want to reset everything (clear database)**
```bash
docker-compose down -v
docker-compose up --build
```

---

## API Response Format

All list endpoints return this format:
```json
{
  "data": [...],
  "total": 20,
  "page": 1,
  "limit": 10,
  "total_pages": 2
}
```

---

## Author

Built as part of a Developer Technical Assessment.