import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ─── Read Database URL from environment variable ─────────────
# This is set in docker-compose.yml
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/customer_db"
)

# ─── Create Engine ───────────────────────────────────────────
# Engine is the core connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# ─── Create Session Factory ──────────────────────────────────
# Each request gets its own session (like a transaction)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ─── Base Class for Models ───────────────────────────────────
# All SQLAlchemy models will inherit from this
Base = declarative_base()


# ─── Dependency for FastAPI routes ───────────────────────────
def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes session after request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()