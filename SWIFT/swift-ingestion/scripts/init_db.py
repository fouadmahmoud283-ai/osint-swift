"""Database migration script for initial schema."""

from sqlalchemy import create_engine, text
from src.db.models import Base
from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


def init_database():
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Ensure enum values are up to date (Postgres only)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        enum_exists = conn.execute(
            text("SELECT 1 FROM pg_type WHERE typname = :name"),
            {"name": "sourcetype"},
        ).scalar()
        if enum_exists:
            existing_values = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT e.enumlabel
                        FROM pg_enum e
                        JOIN pg_type t ON t.oid = e.enumtypid
                        WHERE t.typname = :name
                        """
                    ),
                    {"name": "sourcetype"},
                ).fetchall()
            }
            if "OSINT_SEARCH" not in existing_values:
                conn.execute(text("ALTER TYPE sourcetype ADD VALUE 'OSINT_SEARCH'"))
                logger.info("Added OSINT_SEARCH to sourcetype enum")
    
    logger.info("Database initialized successfully")


if __name__ == "__main__":
    init_database()
