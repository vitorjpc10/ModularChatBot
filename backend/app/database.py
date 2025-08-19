"""
Database connection and session management for the Modular Chatbot application.
Uses SQLAlchemy for ORM and connection pooling.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create database engine
if settings.ENVIRONMENT == "test":
    # Support both SQLite (default) and external DBs (e.g., Postgres) for tests
    test_url = settings.TEST_DATABASE_URL
    if test_url.startswith("sqlite"):
        # SQLite-specific engine options
        engine = create_engine(
            test_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DEBUG
        )
    else:
        # Generic engine options for Postgres/MySQL, etc.
        engine = create_engine(
            test_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG
        )
else:
    # Use configured database for development/production
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.DEBUG
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Metadata for table management
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def create_tables() -> None:
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables() -> None:
    """Drop all database tables (use with caution)."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def check_database_health() -> bool:
    """
    Check database connection health.
    Returns True if connection is healthy, False otherwise.
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.debug("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
