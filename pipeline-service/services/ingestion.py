import os
import dlt
import requests
from datetime import datetime, date
from sqlalchemy.orm import Session
from models.customer import Customer

# ─── Read env variables ──────────────────────────────────────
FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://mock-server:5000")
DATABASE_URL   = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/customer_db")


# ─── Fetch ALL customers from Flask (handles pagination) ─────
def fetch_all_customers_from_flask():
    """
    Calls Flask /api/customers endpoint page by page
    until all customers are fetched.
    Returns a flat list of all customer dicts.
    """
    all_customers = []
    page          = 1
    limit         = 10

    print(f"[Ingestion] Starting fetch from {FLASK_BASE_URL}")

    while True:
        url = f"{FLASK_BASE_URL}/api/customers?page={page}&limit={limit}"
        print(f"[Ingestion] Fetching page {page} -> {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch from Flask: {str(e)}")

        data              = response.json()
        customers_on_page = data.get("data", [])
        all_customers.extend(customers_on_page)

        print(f"[Ingestion] Got {len(customers_on_page)} customers on page {page}")

        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break

        page += 1

    print(f"[Ingestion] Total customers fetched: {len(all_customers)}")
    return all_customers


# ─── Convert raw customer dict to proper Python types ────────
def prepare_customer_for_dlt(customer: dict) -> dict:
    """
    Convert string dates to proper Python date/datetime objects
    so dlt correctly types them in PostgreSQL.
    """
    c = customer.copy()

    # Convert date_of_birth string to Python date object
    if c.get("date_of_birth") and isinstance(c["date_of_birth"], str):
        try:
            c["date_of_birth"] = datetime.strptime(
                c["date_of_birth"], "%Y-%m-%d"
            ).date()
        except ValueError:
            c["date_of_birth"] = None

    # Convert created_at string to Python datetime object
    if c.get("created_at") and isinstance(c["created_at"], str):
        try:
            c["created_at"] = datetime.fromisoformat(
                c["created_at"].replace("Z", "+00:00")
            )
        except ValueError:
            c["created_at"] = None

    # Convert account_balance to float
    if c.get("account_balance") is not None:
        c["account_balance"] = float(c["account_balance"])

    return c


# ─── dlt resource ─────────────────────────────────────────────
@dlt.resource(name="customers", write_disposition="merge", primary_key="customer_id")
def customers_resource(customers_data: list):
    """
    dlt resource that yields customer records.
    write_disposition="merge" means dlt will upsert automatically:
      - INSERT if customer_id does not exist
      - UPDATE if customer_id already exists
    """
    for customer in customers_data:
        yield prepare_customer_for_dlt(customer)


# ─── Load using dlt ───────────────────────────────────────────
def load_customers_with_dlt(customers: list):
    """
    Uses dlt pipeline to load customer data into PostgreSQL.
    dlt handles upsert logic automatically via merge disposition.
    """
    print(f"[dlt] Setting up pipeline...")

    pipeline = dlt.pipeline(
        pipeline_name="customer_pipeline",
        destination=dlt.destinations.postgres(DATABASE_URL),
        dataset_name="public"
    )

    print(f"[dlt] Running pipeline with {len(customers)} customers...")
    load_info = pipeline.run(customers_resource(customers))
    print(f"[dlt] Load complete: {load_info}")


# ─── Upsert using SQLAlchemy ──────────────────────────────────
def upsert_customers(db: Session, customers: list):
    """
    SQLAlchemy upsert to keep customers table in sync.
    INSERT if new, UPDATE if exists.
    Returns count of records processed.
    """
    count = 0

    for c in customers:
        existing = db.query(Customer).filter(
            Customer.customer_id == c["customer_id"]
        ).first()

        # Parse date safely
        date_of_birth = None
        if c.get("date_of_birth"):
            try:
                if isinstance(c["date_of_birth"], str):
                    date_of_birth = datetime.strptime(
                        c["date_of_birth"], "%Y-%m-%d"
                    ).date()
                else:
                    date_of_birth = c["date_of_birth"]
            except ValueError:
                date_of_birth = None

        # Parse timestamp safely
        created_at = None
        if c.get("created_at"):
            try:
                if isinstance(c["created_at"], str):
                    created_at = datetime.fromisoformat(
                        c["created_at"].replace("Z", "+00:00")
                    )
                else:
                    created_at = c["created_at"]
            except ValueError:
                created_at = None

        if existing:
            existing.first_name      = c.get("first_name")
            existing.last_name       = c.get("last_name")
            existing.email           = c.get("email")
            existing.phone           = c.get("phone")
            existing.address         = c.get("address")
            existing.date_of_birth   = date_of_birth
            existing.account_balance = c.get("account_balance")
            existing.created_at      = created_at
            print(f"[Ingestion] Updated: {c['customer_id']}")
        else:
            new_customer = Customer(
                customer_id     = c.get("customer_id"),
                first_name      = c.get("first_name"),
                last_name       = c.get("last_name"),
                email           = c.get("email"),
                phone           = c.get("phone"),
                address         = c.get("address"),
                date_of_birth   = date_of_birth,
                account_balance = c.get("account_balance"),
                created_at      = created_at
            )
            db.add(new_customer)
            print(f"[Ingestion] Inserted: {c['customer_id']}")

        count += 1

    db.commit()
    print(f"[Ingestion] Upsert complete. Records processed: {count}")
    return count