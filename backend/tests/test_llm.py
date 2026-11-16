from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.llm.base import (
    LLMAuthError,
    LLMInvalidRequestError,
    LLMMessage,
    LLMResponse,
)
from app.llm.factory import get_llm_provider
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider
from app.models.usage import UsageRecord
from app.services.conversation_service import ConversationService


def test_factory_returns_configured_providers():
    gemini = get_llm_provider("gemini")
    assert isinstance(gemini, GeminiProvider)
    assert gemini.provider_name == "Gemini"

    openai = get_llm_provider("openai")
    assert isinstance(openai, OpenAIProvider)
    assert openai.provider_name == "OpenAI"

    with pytest.raises(LLMInvalidRequestError):
        get_llm_provider("unsupported_provider_xyz")


def test_missing_api_key_raises_auth_error():
    provider = GeminiProvider(api_key="")
    with pytest.raises(LLMAuthError) as excinfo:
        provider._get_client()
    assert "Gemini API key is not configured" in str(excinfo.value)


@pytest.mark.asyncio
async def test_gemini_generate_response_mocked():
    provider = GeminiProvider(api_key="mock_test_key", default_model="gemini-1.5-flash")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is a real model response from Gemini."
    mock_response.usage_metadata.prompt_token_count = 15
    mock_response.usage_metadata.candidates_token_count = 25

    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    provider._client = mock_client

    messages = [LLMMessage(role="user", content="Hello Gemini!")]
    response = await provider.generate_response(messages)

    assert response.content == "This is a real model response from Gemini."
    assert response.model == "gemini-1.5-flash"
    assert response.provider == "Gemini"
    assert response.input_tokens == 15
    assert response.output_tokens == 25


@pytest.mark.asyncio
async def test_gemini_generate_stream_mocked():
    provider = GeminiProvider(api_key="mock_test_key", default_model="gemini-1.5-flash")

    mock_client = MagicMock()
    chunk1 = MagicMock(text="Hello ")
    chunk2 = MagicMock(text="world!")

    async def mock_stream_iter():
        yield chunk1
        yield chunk2

    mock_client.aio.models.generate_content_stream = AsyncMock(return_value=mock_stream_iter())
    provider._client = mock_client

    messages = [LLMMessage(role="user", content="Say hello")]
    chunks = []
    async for chunk in provider.generate_stream(messages):
        chunks.append(chunk)

    assert chunks == ["Hello ", "world!"]


@pytest.mark.asyncio
async def test_chat_message_endpoint_integration(
    client: AsyncClient,
    test_user_a,
    token_user_a: str,
    db_session: AsyncSession,
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    # 1. Create conversation
    conv = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="LLM Test Chat"
    )

    # 2. Mock GeminiProvider to return response
    mock_llm_response = LLMResponse(
        content="Streaming tokens from Gemini backend adapter.",
        model="gemini-1.5-flash",
        provider="Gemini",
        input_tokens=12,
        output_tokens=18,
    )

    with patch.object(
        GeminiProvider, "generate_response", AsyncMock(return_value=mock_llm_response)
    ):
        res = await client.post(
            f"/api/v1/chats/{conv.id}/messages",
            headers=headers,
            json={
                "content": "Can you explain token streaming?",
                "provider": "gemini",
                "model": "gemini-1.5-flash",
            },
        )

        assert res.status_code == 201
        data = res.json()
        assert data["content"] == "Streaming tokens from Gemini backend adapter."
        assert data["role"] == "assistant"
        assert data["model_provider"] == "Gemini"
        assert data["model_name"] == "gemini-1.5-flash"
        assert data["input_tokens"] == 12
        assert data["output_tokens"] == 18

        # Security check: Ensure API key is NEVER leaked in the API response
        raw_res_str = str(data)
        assert "api_key" not in raw_res_str
        assert "GEMINI_API_KEY" not in raw_res_str

    # 3. Verify usage record was saved in database
    stmt = select(UsageRecord).where(UsageRecord.user_id == test_user_a.id)
    usage = (await db_session.execute(stmt)).scalar_one_or_none()
    assert usage is not None
    assert usage.input_tokens == 12
    assert usage.output_tokens == 18
    assert usage.provider == "Gemini"
