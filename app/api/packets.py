from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.core.database import get_db
from app.schemas import ACKResponse, PacketLogResponse, PacketProcessingResult, SensorPacketCreate
from app.services.ack_service import AckService
from app.services.packet_processor import PacketProcessor

router = APIRouter(
    prefix="/api/packets",
    tags=["packets"],
)


@router.post(
    "/",
    response_model=PacketProcessingResult,
    status_code=status.HTTP_200_OK,
)
async def receive_packet(
    packet: SensorPacketCreate,
    db: Session = Depends(get_db),
) -> PacketProcessingResult:
    """
    Receive and process an incoming sensor packet (HEARTBEAT or EMERGENCY).
    """
    return await PacketProcessor.process_packet(
        db=db,
        packet=packet,
    )


@router.post(
    "/ack/{packet_id}",
    response_model=ACKResponse,
    status_code=status.HTTP_200_OK,
)
async def get_packet_ack(
    packet_id: str,
    node_id: str = Query(...),
    packet_type: str = Query(...),
) -> ACKResponse:
    """
    Explicitly request an ACK confirmation for a packet.
    """
    return await AckService.generate_and_enqueue_ack(
        packet_id=packet_id,
        node_id=node_id,
        packet_type=packet_type,
    )


@router.get(
    "/",
    response_model=list[PacketLogResponse],
    status_code=status.HTTP_200_OK,
)
def list_packet_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    List emergency packet logs.
    """
    return crud.get_all_packet_logs(db=db, limit=limit, offset=offset)