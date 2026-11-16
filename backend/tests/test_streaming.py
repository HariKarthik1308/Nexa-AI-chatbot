import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.base import LLMError
from app.llm.gemini_provider import GeminiProvider
from app.models.message import Message
from app.services.conversation_service import ConversationService


def parse_sse_events(raw_body: str):
    """Utility to parse SSE text stream into structured events."""
    events = []
    current_event = None
    current_data = None

    for line in raw_body.strip().split("\n"):
        line = line.strip()
        if not line:
            if current_event and current_data:
                events.append({"event": current_event, "data": json.loads(current_data)})
                current_event = None
                current_data = None
            continue
        if line.startswith("event:"):
            current_event = line.replace("event:", "").strip()
        elif line.startswith("data:"):
            current_data = line.replace("data:", "").strip()

    if current_event and current_data:
        events.append({"event": current_event, "data": json.loads(current_data)})

    return events


@pytest.mark.asyncio
async def test_stream_chat_message_success(
    client: AsyncClient,
    test_user_a,
    token_user_a: str,
    db_session: AsyncSession,
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    conv = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="SSE Stream Chat"
    )

    async def mock_stream_chunks(*args, **kwargs):
        yield "Hello "
        yield "from "
        yield "Gemini!"

    with patch.object(GeminiProvider, "generate_stream", mock_stream_chunks):
        res = await client.post(
            f"/api/v1/chats/{conv.id}/messages/stream",
            headers=headers,
            json={"content": "Stream to me", "provider": "gemini"},
        )

        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]

        events = parse_sse_events(res.text)
        event_types = [e["event"] for e in events]

        assert "message_start" in event_types
        assert "content_delta" in event_types
        assert "message_complete" in event_types
        assert "usage" in event_types

        # Verify delta contents
        deltas = [e["data"]["delta"] for e in events if e["event"] == "content_delta"]
        assert "".join(deltas) == "Hello from Gemini!"

        # Verify database message was saved
        complete_event = next(e for e in events if e["event"] == "message_complete")
        msg_id = complete_event["data"]["messageId"]

        stmt = select(Message).where(Message.id == msg_id)
        saved_msg = (await db_session.execute(stmt)).scalar_one_or_none()
        assert saved_msg is not None
        assert saved_msg.status == "complete"
        assert saved_msg.content == "Hello from Gemini!"


@pytest.mark.asyncio
async def test_stream_chat_message_provider_error(
    client: AsyncClient,
    test_user_a,
    token_user_a: str,
    db_session: AsyncSession,
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    conv = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Error Stream Chat"
    )

    async def mock_stream_error(*args, **kwargs):
        yield "Beginning text..."
        raise LLMError("Simulated upstream provider outage", 503)

    with patch.object(GeminiProvider, "generate_stream", mock_stream_error):
        res = await client.post(
            f"/api/v1/chats/{conv.id}/messages/stream",
            headers=headers,
            json={"content": "Trigger error", "provider": "gemini"},
        )

        assert res.status_code == 200
        events = parse_sse_events(res.text)
        error_event = next((e for e in events if e["event"] == "error"), None)

        assert error_event is not None
        assert error_event["data"]["code"] == "PROVIDER_ERROR"
        assert "Simulated upstream provider outage" in error_event["data"]["message"]


@pytest.mark.asyncio
async def test_stream_chat_message_idor_protection(
    client: AsyncClient,
    test_user_a,
    test_user_b,
    token_user_b: str,
    db_session: AsyncSession,
):
    """User B attempting to stream into User A's chat is rejected."""
    conv_a = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Alice Secret Chat"
    )

    res = await client.post(
        f"/api/v1/chats/{conv_a.id}/messages/stream",
        headers={"Authorization": f"Bearer {token_user_b}"},
        json={"content": "Unauthorized message", "provider": "gemini"},
    )

    assert res.status_code == 200
    events = parse_sse_events(res.text)
    error_event = next(e for e in events if e["event"] == "error")
    assert error_event["data"]["code"] == "NOT_FOUND"
