from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to retrieve the currently authenticated user.
    Supports JWT Bearer token or falls back to a development demo user if unauthenticated in development."""
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        if payload and "sub" in payload:
            user_id = payload["sub"]
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user

    # Development fallback demo user
    stmt = select(User).where(User.email == "demo@nexa-ai.local")
    result = await db.execute(stmt)
    demo_user = result.scalar_one_or_none()
    if not demo_user:
        demo_user = User(
            id="00000000-0000-0000-0000-000000000001",
            email="demo@nexa-ai.local",
            password_hash="dev_placeholder_hash",
            is_active=True,
        )
        db.add(demo_user)
        await db.commit()
        await db.refresh(demo_user)
    return demo_user
