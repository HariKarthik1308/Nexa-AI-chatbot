import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.services.conversation_service import ConversationService


def test_argon2id_password_hashing():
    raw_password = "P@ssword1234_ExtremelySecure!"
    hashed = hash_password(raw_password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_token_generation_and_validation():
    user_id = "test-uuid-12345"
    token = create_access_token(subject=user_id, extra_claims={"role": "tester"})

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "tester"

    # Invalid token returns None
    assert decode_access_token("invalid.token.signature") is None


@pytest.mark.asyncio
async def test_idor_protection_read(
    client: AsyncClient,
    test_user_a,
    token_user_a: str,
    test_user_b,
    token_user_b: str,
    db_session: AsyncSession,
):
    """User B must NOT be able to read User A's conversation."""
    conv_a = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Alice Confidential Chat"
    )

    # Alice can read her chat
    alice_res = await client.get(
        f"/api/v1/chats/{conv_a.id}",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert alice_res.status_code == 200

    # Bob attempting to read Alice's chat MUST receive 404 (IDOR prevention)
    bob_res = await client.get(
        f"/api/v1/chats/{conv_a.id}",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert bob_res.status_code == 404
    assert bob_res.json()["detail"] == "Conversation not found"


@pytest.mark.asyncio
async def test_idor_protection_modify_and_delete(
    client: AsyncClient,
    test_user_a,
    test_user_b,
    token_user_b: str,
    db_session: AsyncSession,
):
    """User B must NOT be able to rename or delete User A's conversation."""
    conv_a = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Alice Chat"
    )

    # Bob attempts to rename Alice's chat -> 404
    bob_rename = await client.patch(
        f"/api/v1/chats/{conv_a.id}",
        headers={"Authorization": f"Bearer {token_user_b}"},
        json={"title": "Hacked Title"},
    )
    assert bob_rename.status_code == 404

    # Bob attempts to delete Alice's chat -> 404
    bob_delete = await client.delete(
        f"/api/v1/chats/{conv_a.id}",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert bob_delete.status_code == 404

    # Verify conversation title was untouched
    re_check = await ConversationService.get_conversation(
        db_session, conversation_id=conv_a.id, user_id=test_user_a.id
    )
    assert re_check is not None
    assert re_check.title == "Alice Chat"
