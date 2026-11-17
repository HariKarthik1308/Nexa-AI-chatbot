from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    database: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    database: str
    llm_configured: bool
    langgraph: str
    timestamp: datetime
