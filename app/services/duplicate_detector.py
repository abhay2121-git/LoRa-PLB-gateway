import asyncio
import logging
from sqlalchemy.orm import Session

from app import crud

logger = logging.getLogger("gateway.duplicate_detector")


class DuplicateDetector:
    """
    Duplicate Detector (Requirement 12):
    - Duplicate Nodes: Allowed
    - Duplicate Packets: NOT Allowed
    - Uniqueness determined by packet_id
    - Check using PostgreSQL PLUS a lightweight in-memory Python set (NOT an LRU cache)
    - If duplicate arrives: Do not store again, Still generate ACK, Do not generate duplicate emergency
    """

    def __init__(self):
        # Requirement 12: lightweight in-memory Python set
        self._seen_packet_ids: set[str] = set()
        self._lock = asyncio.Lock()

    async def is_duplicate(self, db: Session, packet_id: str) -> bool:
        async with self._lock:
            # Step 1: Check lightweight in-memory set
            if packet_id in self._seen_packet_ids:
                logger.info(f"DuplicateDetector: Packet {packet_id} found in in-memory set.")
                return True

            # Step 2: Check PostgreSQL database
            exists_in_db = crud.packet_exists(db=db, packet_id=packet_id)
            if exists_in_db:
                self._seen_packet_ids.add(packet_id)
                logger.info(f"DuplicateDetector: Packet {packet_id} found in PostgreSQL DB.")
                return True

            return False

    async def register(self, packet_id: str) -> None:
        async with self._lock:
            self._seen_packet_ids.add(packet_id)
            logger.debug(f"DuplicateDetector: Registered packet_id={packet_id} in memory set.")


duplicate_detector = DuplicateDetector()
