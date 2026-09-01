from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(tags=["dashboard"])


@router.get("/")
def render_dashboard(request: Request):
    """
    Render main dashboard view containing Live Node Monitoring & Emergency History.
    """
    settings = get_settings()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "LoRa PLB Gateway Dashboard",
            "maptiler_api_key": settings.maptiler_api_key,
        },
    )
