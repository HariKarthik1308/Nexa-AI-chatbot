import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


@pytest.mark.asyncio
async def test_user_registration_success_and_cookie(
    client: AsyncClient, db_session: AsyncSession
):
    payload = {
        "email": "newuser@example.com",
        "password": "SecurePassword123!",
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201

    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password_hash" not in data  # Never expose hash in response

    # Verify HttpOnly session cookie was set
    assert "access_token" in res.cookies

    # Verify user exists in database with Argon2id hash
    stmt = select(User).where(User.email == "newuser@example.com")
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert user is not None
    assert user.password_hash.startswith("$argon2id$")


@pytest.mark.asyncio
async def test_registration_validation_and_duplicate_handling(client: AsyncClient):
    # Weak password (< 8 chars)
    res_weak = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert res_weak.status_code == 422

    # Initial valid registration
    res1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "SecurePassword123!"},
    )
    assert res1.status_code == 201

    # Duplicate registration attempt
    res2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "AnotherPassword456!"},
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_user_login_and_logout(
    client: AsyncClient, test_user_a: User
):
    # 1. Invalid password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_a.email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 2. Correct password
    good_login = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_a.email, "password": "SuperSecretPassword123!"},
    )
    assert good_login.status_code == 200
    token_data = good_login.json()
    assert "access_token" in token_data
    assert "access_token" in good_login.cookies

    token = token_data["access_token"]

    # 3. GET /me using Bearer header
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_user_a.email

    # 4. GET /me using HttpOnly Cookie
    cookie_client_res = await client.get(
        "/api/v1/auth/me",
        cookies={"access_token": token},
    )
    assert cookie_client_res.status_code == 200
    assert cookie_client_res.json()["email"] == test_user_a.email

    # 5. Logout clears cookie
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Not authenticated" in res.json()["detail"]


@pytest.mark.asyncio
async def test_multi_account_cross_access_strict_isolation(
    client: AsyncClient,
):
    """Rigorous acceptance test: Two accounts cannot access, inspect, modify, or delete each other's chats."""
    # 1. Register User Alpha
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "alpha@example.com", "password": "AlphaPassword123!"},
    )
    token_a = res_a.cookies["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User Beta
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "beta@example.com", "password": "BetaPassword123!"},
    )
    token_b = res_b.cookies["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Alpha creates Chat A
    chat_a_res = await client.post(
        "/api/v1/chats",
        headers=headers_a,
        json={"title": "Alpha Confidential Project"},
    )
    chat_a_id = chat_a_res.json()["id"]

    # 4. Beta creates Chat B
    chat_b_res = await client.post(
        "/api/v1/chats",
        headers=headers_b,
        json={"title": "Beta Public Project"},
    )
    chat_b_id = chat_b_res.json()["id"]

    # 5. Alpha list shows ONLY Chat A
    list_a = await client.get("/api/v1/chats", headers=headers_a)
    chat_ids_a = [c["id"] for c in list_a.json()]
    assert chat_a_id in chat_ids_a
    assert chat_b_id not in chat_ids_a

    # 6. Beta list shows ONLY Chat B
    list_b = await client.get("/api/v1/chats", headers=headers_b)
    chat_ids_b = [c["id"] for c in list_b.json()]
    assert chat_b_id in chat_ids_b
    assert chat_a_id not in chat_ids_b

    # 7. Beta attempts to read Chat A -> 404
    cross_read = await client.get(f"/api/v1/chats/{chat_a_id}", headers=headers_b)
    assert cross_read.status_code == 404

    # 8. Beta attempts to rename Chat A -> 404
    cross_rename = await client.patch(
        f"/api/v1/chats/{chat_a_id}",
        headers=headers_b,
        json={"title": "Tampered Title"},
    )
    assert cross_rename.status_code == 404

    # 9. Beta attempts to delete Chat A -> 404
    cross_delete = await client.delete(f"/api/v1/chats/{chat_a_id}", headers=headers_b)
    assert cross_delete.status_code == 404

    # 10. Alpha can still read Chat A intact
    verify_a = await client.get(f"/api/v1/chats/{chat_a_id}", headers=headers_a)
    assert verify_a.status_code == 200
    assert verify_a.json()["title"] == "Alpha Confidential Project"
