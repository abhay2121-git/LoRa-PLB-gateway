import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401
from app.api.packets import router as packets_router
from app.core.config import settings
from app.core.database import SessionLocal, create_tables
from app.core.logger import logger, setup_logging
from app.routers.dashboard import router as dashboard_router
from app.routers.emergency import router as emergency_router
from app.routers.nodes import router as nodes_router
from app.routers.sensor import router as sensor_router
from app.routers.stats import router as stats_router
from app.routers.websocket import router as websocket_router
from app.services.node_manager import check_offline_nodes


async def periodic_node_timeout_checker():
    """
    Background task checking for nodes that haven't sent a heartbeat/packet in 15 minutes.
    Runs every 60 seconds.
    """
    while True:
        try:
            await asyncio.sleep(60)
            db = SessionLocal()
            try:
                check_offline_nodes(db)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"Error in periodic node timeout checker: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """
    setup_logging()
    logger.info("Initializing database tables...")
    create_tables()

    logger.info(f"Gateway Application Started: {settings.app_name} v{settings.app_version}")
    logger.info(f"Gateway ID: {settings.gateway_id}")

    # Start background node offline checker task
    checker_task = asyncio.create_task(periodic_node_timeout_checker())

    yield

    checker_task.cancel()
    try:
        await checker_task
    except asyncio.CancelledError:
        pass
    logger.info("Gateway Application Shutdown Complete.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Enable CORS for frontend client interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for CSS / JS assets
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register API & Page Routers
app.include_router(dashboard_router)
app.include_router(packets_router)
app.include_router(nodes_router)
app.include_router(emergency_router)
app.include_router(sensor_router)
app.include_router(stats_router)
app.include_router(websocket_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "gateway": settings.gateway_id,
        "application": settings.app_name,
    }