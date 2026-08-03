from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.core.database import get_db
from app.schemas import SensorLogResponse

router = APIRouter(
    prefix="/api/sensors",
    tags=["sensors"],
)


@router.get(
    "/",
    response_model=list[SensorLogResponse],
    status_code=status.HTTP_200_OK,
)
def get_sensor_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Get sensor logs (Emergency telemetry data only).
    """
    return crud.get_all_sensor_logs(db=db, limit=limit, offset=offset)
