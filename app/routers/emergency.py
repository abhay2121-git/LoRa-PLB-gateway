from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app import crud, models
from app.core.database import get_db
from app.schemas import EmergencyEventResponse, EmergencyResolveRequest

router = APIRouter(
    prefix="/api/emergencies",
    tags=["emergency"],
)


@router.get(
    "/",
    response_model=list[EmergencyEventResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_emergencies(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Get all emergency history records (SOS, FALL, HAZARD).
    Populates latest vitals from sensor_logs.
    """
    stmt = (
        select(models.EmergencyEvent)
        .order_by(models.EmergencyEvent.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    events = list(db.scalars(stmt).all())
    
    result = []
    for event in events:
        resp = EmergencyEventResponse.model_validate(event)
        # Fetch latest sensor log for vitals
        sensor_stmt = (
            select(models.SensorLog)
            .where(models.SensorLog.emergency_id == event.emergency_id)
            .order_by(models.SensorLog.timestamp.desc())
            .limit(1)
        )
        s_log = db.scalar(sensor_stmt)
        if s_log:
            resp.battery = s_log.battery
            resp.heart_rate = s_log.heart_rate
            resp.spo2 = s_log.spo2
            resp.temperature = s_log.temperature
        elif event.node:
            resp.battery = event.node.battery
            
        result.append(resp)

    return result


@router.get(
    "/active",
    response_model=list[EmergencyEventResponse],
    status_code=status.HTTP_200_OK,
)
def get_active_emergencies(db: Session = Depends(get_db)):
    """
    Get currently active (unresolved) emergencies.
    """
    events = crud.get_active_emergency_events(db=db)
    result = []
    for event in events:
        resp = EmergencyEventResponse.model_validate(event)
        sensor_stmt = (
            select(models.SensorLog)
            .where(models.SensorLog.emergency_id == event.emergency_id)
            .order_by(models.SensorLog.timestamp.desc())
            .limit(1)
        )
        s_log = db.scalar(sensor_stmt)
        if s_log:
            resp.battery = s_log.battery
            resp.heart_rate = s_log.heart_rate
            resp.spo2 = s_log.spo2
            resp.temperature = s_log.temperature
        result.append(resp)
    return result


@router.post(
    "/{emergency_id}/resolve",
    response_model=EmergencyEventResponse,
    status_code=status.HTTP_200_OK,
)
def resolve_emergency(
    emergency_id: str,
    req: EmergencyResolveRequest,
    db: Session = Depends(get_db),
):
    """
    Resolve an active emergency event with operator remarks.
    """
    event = crud.resolve_emergency_event(db=db, emergency_id=emergency_id, remarks=req.remarks)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency event {emergency_id} not found.",
        )
    return event