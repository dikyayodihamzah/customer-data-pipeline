import os
import logging
from typing import Generator

import dlt
import requests
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.customer import Customer

logger = logging.getLogger(__name__)

FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://mock-server:5000")
BATCH_SIZE = 100


@dlt.resource(primary_key="customer_id", write_disposition="merge")
def fetch_customers() -> Generator:
    """
    dlt resource that fetches all customers from the Flask mock server
    with automatic pagination.
    """
    page = 1
    fetched = 0

    while True:
        try:
            response = requests.get(
                f"{FLASK_BASE_URL}/api/customers",
                params={"page": page, "limit": BATCH_SIZE},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch page %d from mock server: %s", page, exc)
            raise

        payload = response.json()
        customers = payload.get("data", [])
        total = payload.get("total", 0)

        if not customers:
            break

        yield customers
        fetched += len(customers)
        logger.info("Fetched page %d — %d/%d customers", page, fetched, total)

        if fetched >= total:
            break

        page += 1


def run_ingestion(db: Session) -> int:
    """
    Run the dlt-powered ingestion pipeline:
      1. Iterate the dlt resource to auto-paginate Flask data.
      2. Upsert each batch into PostgreSQL via SQLAlchemy.

    Returns the total number of records processed.
    """
    total_processed = 0

    for batch in fetch_customers():
        records: list[dict] = batch if isinstance(batch, list) else [batch]

        if not records:
            continue

        stmt = insert(Customer).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id"],
            set_={
                "first_name": stmt.excluded.first_name,
                "last_name": stmt.excluded.last_name,
                "email": stmt.excluded.email,
                "phone": stmt.excluded.phone,
                "address": stmt.excluded.address,
                "date_of_birth": stmt.excluded.date_of_birth,
                "account_balance": stmt.excluded.account_balance,
                "created_at": stmt.excluded.created_at,
            },
        )
        db.execute(stmt)
        total_processed += len(records)
        logger.info("Upserted batch of %d records (total: %d)", len(records), total_processed)

    db.commit()
    return total_processed
