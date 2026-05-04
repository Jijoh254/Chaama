"""
Database configuration for SQLAlchemy.
Creates engine, session factory, and declarative base.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=10,        # Number of connections to keep open
    max_overflow=20      # Allow up to 20 additional connections
)

# Session factory - use this to get DB sessions in your code
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function that yields a database session.
    Use with FastAPI's Depends() in route handlers.
    
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
