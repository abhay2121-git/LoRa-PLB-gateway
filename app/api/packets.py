from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.core.database import get_db
from app.schemas import ACKResponse, PacketProcessingResult, SensorPacketCreate
from app.services.ack_services import generate_ack
from app.services.packet_handler import process_packet

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
    db: Session = Depends(get_db),
) -> PacketProcessingResult:
    """
    Receive and process an incoming sensor packet (HEARTBEAT or EMERGENCY).
    """
    return process_packet(
        db=db,
        packet=packet,
    )


@router.post(
    "/ack/{packet_id}",
    response_model=ACKResponse,
    status_code=status.HTTP_200_OK,
)
def get_packet_ack(
    packet_id: str,
    node_id: str = Query(...),
    packet_type: str = Query(...),
) -> ACKResponse:
    """
    Explicitly request an ACK confirmation for a packet.
    """
    return generate_ack(
        packet_id=packet_id,
        node_id=node_id,
        packet_type=packet_type,
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
def list_packet_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List emergency packet logs.
    """
    logs = crud.get_all_packet_logs(db=db, limit=limit, offset=offset)
    return logs