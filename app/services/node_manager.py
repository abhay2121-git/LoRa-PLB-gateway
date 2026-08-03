import logging
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings

logger = logging.getLogger("gateway.node_manager")


def check_offline_nodes(db: Session) -> int:
    """
    Scans nodes table and marks nodes as 'OFFLINE' if no heartbeat/packet
    received for > settings.heartbeat_timeout_seconds (Requirement 10).
    """
    updated_count = crud.mark_offline_nodes(
        db=db,
        timeout_seconds=settings.heartbeat_timeout_seconds,
    )
    if updated_count > 0:
        logger.info(
            f"NodeManager: Automatically marked {updated_count} node(s) as OFFLINE due to timeout."
        )
    return updated_count
