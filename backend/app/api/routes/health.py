from fastapi import APIRouter

from app.core.config import settings
from app.database.mongodb import is_mongo_connected
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.environment,
        database_connected=is_mongo_connected(),
    )

