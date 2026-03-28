from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models.customer import Customer
from services.ingestion import (
    fetch_all_customers_from_flask,
    upsert_customers,
    load_customers_with_dlt
)

# ─── Create all DB tables on startup ─────────────────────────
Base.metadata.create_all(bind=engine)

# ─── App Setup ───────────────────────────────────────────────
app = FastAPI(
    title="Customer Data Pipeline API",
    description="Fetches customer data from Flask mock server and stores in PostgreSQL using dlt",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────
@app.get("/api/health")
def health_check():
    """Check if the pipeline service is running."""
    return {
        "status":    "healthy",
        "service":   "pipeline-service",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ─── POST /api/ingest ─────────────────────────────────────────
@app.post("/api/ingest")
def ingest_data(db: Session = Depends(get_db)):
    """
    Main ingestion endpoint.
    1. Fetches ALL customers from Flask (handles pagination automatically)
    2. Loads into PostgreSQL using dlt (handles upsert automatically)
    3. Also syncs to SQLAlchemy model for querying
    4. Returns count of records processed
    """
    try:
        # Step 1: Fetch all customers from Flask mock server
        print("[Ingest] Fetching customers from Flask...")
        customers = fetch_all_customers_from_flask()

        if not customers:
            raise HTTPException(
                status_code=404,
                detail="No customers found from Flask mock server"
            )

        # Step 2: Load using dlt (upsert handled automatically)
        print(f"[Ingest] Loading {len(customers)} customers via dlt...")
        try:
            load_customers_with_dlt(customers)
        except Exception as dlt_error:
            print(f"[Ingest] dlt warning: {dlt_error} — falling back to SQLAlchemy")

        # Step 3: Sync to SQLAlchemy customers table for querying
        print(f"[Ingest] Syncing to customers table...")
        records_processed = upsert_customers(db, customers)

        # Step 4: Return success
        return {
            "status":            "success",
            "records_processed": records_processed
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


# ─── GET /api/customers ───────────────────────────────────────
@app.get("/api/customers")
def get_customers(
    page:  int = 1,
    limit: int = 10,
    db:    Session = Depends(get_db)
):
    """
    Return paginated list of customers from PostgreSQL.
    Query params:
      - page  (int, default 1)
      - limit (int, default 10)
    """
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400,
            detail="page and limit must be greater than 0"
        )

    total       = db.query(Customer).count()
    offset      = (page - 1) * limit
    customers   = db.query(Customer).offset(offset).limit(limit).all()
    total_pages = (total + limit - 1) // limit

    return {
        "data":        [c.to_dict() for c in customers],
        "total":       total,
        "page":        page,
        "limit":       limit,
        "total_pages": total_pages
    }


# ─── GET /api/customers/{customer_id} ────────────────────────
@app.get("/api/customers/{customer_id}")
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Return a single customer by customer_id from PostgreSQL.
    Returns 404 if not found.
    """
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail={
                "error":       "Customer not found",
                "customer_id": customer_id
            }
        )

    return customer.to_dict()