import os
import sys
from typing import AsyncGenerator
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure backend root is on sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.main import app
from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user_a(db_session: AsyncSession) -> User:
    user = User(
        id="11111111-1111-1111-1111-111111111111",
        email="alice@example.com",
        password_hash=hash_password("SuperSecretPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_b(db_session: AsyncSession) -> User:
    user = User(
        id="22222222-2222-2222-2222-222222222222",
        email="bob@example.com",
        password_hash=hash_password("SuperSecretPassword456!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
def token_user_a(test_user_a: User) -> str:
    return create_access_token(subject=test_user_a.id)


@pytest_asyncio.fixture(scope="function")
def token_user_b(test_user_b: User) -> str:
    return create_access_token(subject=test_user_b.id)
