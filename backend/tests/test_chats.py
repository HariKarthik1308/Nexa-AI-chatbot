import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_create_and_list_conversations(
    client: AsyncClient, token_user_a: str
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    # Create new conversation
    response = await client.post(
        "/api/v1/chats",
        headers=headers,
        json={"title": "Test Architecture Chat"},
    )
    assert response.status_code == 201
    created_chat = response.json()
    assert created_chat["title"] == "Test Architecture Chat"
    assert "id" in created_chat

    # List conversations
    list_response = await client.get("/api/v1/chats", headers=headers)
    assert list_response.status_code == 200
    chats = list_response.json()
    assert len(chats) >= 1
    assert chats[0]["id"] == created_chat["id"]


@pytest.mark.asyncio
async def test_get_and_rename_conversation(
    client: AsyncClient, token_user_a: str, test_user_a, db_session: AsyncSession
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    # Create via service
    conv = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Initial Title"
    )

    # Add messages
    await ConversationService.add_message(
        db_session,
        conversation_id=conv.id,
        user_id=test_user_a.id,
        role="user",
        content="What is FastAPI?",
    )
    await ConversationService.add_message(
        db_session,
        conversation_id=conv.id,
        user_id=test_user_a.id,
        role="assistant",
        content="FastAPI is a modern, fast web framework for building APIs with Python.",
        model_name="gemini-1.5-flash",
    )

    # Get conversation via API
    get_res = await client.get(f"/api/v1/chats/{conv.id}", headers=headers)
    assert get_res.status_code == 200
    conv_data = get_res.json()
    assert conv_data["id"] == conv.id
    assert len(conv_data["messages"]) == 2
    assert conv_data["messages"][0]["content"] == "What is FastAPI?"

    # Rename conversation
    patch_res = await client.patch(
        f"/api/v1/chats/{conv.id}",
        headers=headers,
        json={"title": "Updated Title"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_conversation_cascades_messages(
    client: AsyncClient, token_user_a: str, test_user_a, db_session: AsyncSession
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    conv = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="To Be Deleted"
    )
    msg = await ConversationService.add_message(
        db_session,
        conversation_id=conv.id,
        user_id=test_user_a.id,
        role="user",
        content="Transient message",
    )

    # Delete conversation
    del_res = await client.delete(f"/api/v1/chats/{conv.id}", headers=headers)
    assert del_res.status_code == 204

    # Verify conversation is gone
    check_conv = await client.get(f"/api/v1/chats/{conv.id}", headers=headers)
    assert check_conv.status_code == 404

    # Verify message was cascade-deleted from database
    stmt = select(Message).where(Message.id == msg.id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None
