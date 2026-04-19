"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DB_URL,
    echo=settings.DEBUG,
    future=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session (generator for FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.db import models
    Base.metadata.create_all(bind=engine)
