from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(tags=["dashboard"])


@router.get("/")
def render_dashboard(request: Request):
    """
    Render main dashboard view containing Live Node Monitoring & Emergency History.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "page_title": "LoRa PLB Gateway Dashboard"},
    )
