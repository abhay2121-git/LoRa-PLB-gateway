from datetime import datetime, UTC
from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)
