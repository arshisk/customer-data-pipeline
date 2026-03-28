from sqlalchemy import Column, String, Text, Date, DECIMAL, TIMESTAMP
from database import Base


class Customer(Base):
    """
    SQLAlchemy model for the customers table in PostgreSQL.
    This defines the exact structure of the database table.
    """
    __tablename__ = "customers"

    # Primary Key
    customer_id     = Column(String(50),  primary_key=True, index=True)

    # Name fields
    first_name      = Column(String(100), nullable=False)
    last_name       = Column(String(100), nullable=False)

    # Contact fields
    email           = Column(String(255), nullable=False)
    phone           = Column(String(20),  nullable=True)
    address         = Column(Text,        nullable=True)

    # Personal info
    date_of_birth   = Column(Date,        nullable=True)

    # Financial info
    account_balance = Column(DECIMAL(15, 2), nullable=True)

    # Timestamps
    created_at      = Column(TIMESTAMP,   nullable=True)

    def to_dict(self):
        """Convert model instance to a plain dictionary for JSON responses."""
        return {
            "customer_id":     self.customer_id,
            "first_name":      self.first_name,
            "last_name":       self.last_name,
            "email":           self.email,
            "phone":           self.phone,
            "address":         self.address,
            "date_of_birth":   str(self.date_of_birth)   if self.date_of_birth   else None,
            "account_balance": float(self.account_balance) if self.account_balance else None,
            "created_at":      str(self.created_at)      if self.created_at      else None,
        }