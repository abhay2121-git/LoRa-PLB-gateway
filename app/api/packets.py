from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import session

from app.database import get_db
from app.schemas import SensorPacketCreate

from app.services.packet_handler import (
    PacketProcessingResult, 
    process_packet
)


router = APIRouter(
    prefix="/api/packets",
    tags=["packets"],
)

@router.post(
    "/",
    response_model=PacketProcessingResult,
    status_code=status.HTTP_200_OK,
)
def receive_packet(
    packet: SensorPacketCreate,
    db: session = Depends(get_db),
) -> PacketProcessingResult:
    """
    Receive and process an incoming sensor packet.
    """

    return process_packet(
        db=db,
        packet=packet,
    )