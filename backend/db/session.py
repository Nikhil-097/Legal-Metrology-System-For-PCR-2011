from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Configure PostgreSQL Engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # Verifies connection liveness before checking out of pool
    pool_size=10,             # Number of persistent connections
    max_overflow=20,          # Maximum temporary overflow connections during traffic spikes
    pool_recycle=3600,        # Recycle connections after 1 hour
    echo=False                # Set to True for SQL query debugging
)

# Session factory for generating scoped database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes and cleans up the session when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()