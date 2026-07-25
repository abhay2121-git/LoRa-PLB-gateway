from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models
from app.core.database import get_db
from app.schemas import DashboardStatsResponse

router = APIRouter(
    prefix="/api/stats",
    tags=["stats"],
)


@router.get(
    "/dashboard",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_nodes = db.scalar(select(func.count(models.Node.id))) or 0
    online_nodes = db.scalar(select(func.count(models.Node.id)).where(models.Node.status == "ONLINE")) or 0
    offline_nodes = db.scalar(select(func.count(models.Node.id)).where(models.Node.status == "OFFLINE")) or 0
    active_emergencies = db.scalar(select(func.count(models.EmergencyEvent.id)).where(models.EmergencyEvent.resolved == False)) or 0
    total_emergencies = db.scalar(select(func.count(models.EmergencyEvent.id))) or 0
    total_packets = db.scalar(select(func.count(models.PacketLog.id))) or 0

    return DashboardStatsResponse(
        total_nodes=total_nodes,
        online_nodes=online_nodes,
        offline_nodes=offline_nodes,
        active_emergencies=active_emergencies,
        total_emergencies=total_emergencies,
        total_packets_processed=total_packets,
    )
