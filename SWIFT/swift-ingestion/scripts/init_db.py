"""Database migration script for initial schema."""

from sqlalchemy import create_engine
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
    
    logger.info("Database initialized successfully")


if __name__ == "__main__":
    init_database()
