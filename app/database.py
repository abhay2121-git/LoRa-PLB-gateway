# Database configuration using PostgreSQL + SQLAlchemy

from collections.abc import Generator
import sys

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes.
    Creates a database session and closes it automatically.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def create_tables() -> None:
    """
    Creates all tables defined in SQLAlchemy models.
    """
    Base.metadata.create_all(bind=engine)