"""
DocSetu AI - Database Connection Setup
Supports SQLite for development and PostgreSQL for production.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Engine configuration based on database type
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    from models.database import User, Document, Analysis, ComplianceReport, Subscription, Payment  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


def check_db_connection() -> bool:
    """
    Check if the database connection is healthy.
    Returns True if connection is successful.
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
