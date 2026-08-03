from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.core.database import get_db
from app.schemas import (
    HazardBroadcastRequest,
    OutboundMessageResponse,
    StatusMessageCreate,
)
from app.services.status_message_service import StatusMessageService

router = APIRouter(
    prefix="/api/outbound",
    tags=["outbound"],
)


@router.post(
    "/status-message",
    status_code=status.HTTP_200_OK,
)
async def send_status_message(
    req: StatusMessageCreate,
    db: Session = Depends(get_db),
):
    """
    Transmit Status Message to a nearby node (Requirement 18).
    Stores in outbound_messages table (Requirement 4) and enqueues to Outbound Queue (Requirement 8).
    """
    msg_id = await StatusMessageService.create_and_enqueue_status_message(
        db=db,
        destination_node=req.destination_node,
        message_text=req.message,
    )
    return {
        "status": "QUEUED",
        "message_id": msg_id,
        "destination_node": req.destination_node,
        "message": req.message,
    }


@router.post(
    "/hazard-broadcast",
    status_code=status.HTTP_200_OK,
)
async def broadcast_hazard(
    req: HazardBroadcastRequest,
    db: Session = Depends(get_db),
):
    """
    Broadcast Hazard alert to all nodes (Requirement 18).
    """
    msg_id = await StatusMessageService.create_and_enqueue_hazard_broadcast(
        db=db,
        message_text=req.message,
        latitude=req.latitude,
        longitude=req.longitude,
    )
    return {
        "status": "QUEUED",
        "message_id": msg_id,
        "destination": "BROADCAST",
        "message": req.message,
    }


@router.get(
    "/",
    response_model=list[OutboundMessageResponse],
    status_code=status.HTTP_200_OK,
)
def get_outbound_messages(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    List all outbound messages stored in outbound_messages table (Requirement 4).
    """
    return crud.get_all_outbound_messages(db=db, limit=limit, offset=offset)
