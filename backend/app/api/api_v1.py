from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.chats import router as chats_router
from app.api.auth import router as auth_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(chats_router, prefix="/chats", tags=["Chats"])
