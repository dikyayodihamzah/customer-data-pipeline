import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models.customer import Customer, CustomerResponse, PaginatedResponse
from services.ingestion import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
    yield


app = FastAPI(
    title="Customer Pipeline Service",
    description="FastAPI data ingestion pipeline — fetches customers from mock server and stores in PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "pipeline-service"}


@app.post("/api/ingest")
def ingest(db: Session = Depends(get_db)):
    """
    Fetch all customer data from the Flask mock server (handling pagination)
    and upsert into PostgreSQL.
    """
    try:
        records_processed = run_ingestion(db)
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Ingestion failed: {exc}")

    return {"status": "success", "records_processed": records_processed}


@app.get("/api/customers", response_model=PaginatedResponse)
def list_customers(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="page and limit must be positive integers")

    total = db.scalar(select(func.count()).select_from(Customer))
    offset = (page - 1) * limit
    customers = db.scalars(
        select(Customer).order_by(Customer.customer_id).offset(offset).limit(limit)
    ).all()

    return PaginatedResponse(
        data=[CustomerResponse.model_validate(c) for c in customers],
        total=total or 0,
        page=page,
        limit=limit,
    )


@app.get("/api/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return CustomerResponse.model_validate(customer)
