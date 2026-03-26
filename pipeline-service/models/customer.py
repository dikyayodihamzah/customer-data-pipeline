from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Date, DateTime, Numeric, String, Text

from database import Base


class Customer(Base):
    """SQLAlchemy ORM model for the customers table."""

    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    account_balance = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime, nullable=True)


class CustomerResponse(BaseModel):
    """Pydantic schema for API responses."""

    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    account_balance: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    data: list[CustomerResponse]
    total: int
    page: int
    limit: int
