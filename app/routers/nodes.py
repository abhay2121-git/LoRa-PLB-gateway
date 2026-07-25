from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.core.database import get_db
from app.schemas import NodeResponse

router = APIRouter(
    prefix="/api/nodes",
    tags=["nodes"],
)


@router.get(
    "/",
    response_model=list[NodeResponse],
    status_code=status.HTTP_200_OK,
)
def get_all_nodes(db: Session = Depends(get_db)):
    """
    Get live status of all registered nodes (Live Node Monitoring).
    """
    return crud.get_all_nodes(db=db)


@router.get(
    "/{node_id}",
    response_model=NodeResponse,
    status_code=status.HTTP_200_OK,
)
def get_node(node_id: str, db: Session = Depends(get_db)):
    """
    Get single node details by node_id.
    """
    node = crud.get_node_by_node_id(db=db, node_id=node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node {node_id} not found.",
        )
    return node