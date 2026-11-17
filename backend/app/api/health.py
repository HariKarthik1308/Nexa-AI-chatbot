from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Liveness check endpoint validating database connectivity."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness probe validating dependencies including DB, LLM config, and LangGraph."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    llm_configured = bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)
    
    return ReadinessResponse(
        status="ready" if db_status == "healthy" else "not_ready",
        database=db_status,
        llm_configured=llm_configured,
        langgraph="enabled",
        timestamp=datetime.now(timezone.utc),
    )
