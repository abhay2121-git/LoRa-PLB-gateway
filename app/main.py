# Entry Point of FastAPI

from contextlib import asynccontextmanager
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI

import app.models  # noqa: F401

from app.api.packets import router as packets_router
from app.config import settings
from app.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """

    create_tables()

    print("\n--- GATEWAY STARTED ---")
    print(f"Application: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Gateway ID: {settings.gateway_id}")

    yield

    print("\n--- GATEWAY STOPPED ---")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


app.include_router(packets_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "gateway_id": settings.gateway_id,
        "status": "ONLINE",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "gateway": settings.gateway_id,
    }

