import logging
from sqlalchemy.orm import Session
from app import crud
from app.core.config import settings

logger = logging.getLogger("gateway.node_manager")


def check_offline_nodes(db: Session) -> int:
    """
    Scans the nodes table and updates status to 'OFFLINE' for any node
    whose last_seen timestamp is older than the configured threshold (default 15 minutes).
    """
    updated_count = crud.mark_offline_nodes(
        db=db,
        timeout_seconds=settings.node_offline_timeout_seconds,
    )
    if updated_count > 0:
        logger.info(f"Node manager: Marked {updated_count} node(s) as OFFLINE due to 15-minute timeout.")
    return updated_count
