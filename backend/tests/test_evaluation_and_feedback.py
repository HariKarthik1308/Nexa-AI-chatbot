import json
import os
from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eval.evaluator import evaluate_heuristics, load_dataset, run_evaluation
from app.llm.base import BaseLLMProvider, LLMResponse
from app.models.usage import MessageFeedback
from app.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_submit_message_feedback_success_and_update(
    client: AsyncClient,
    test_user_a,
    token_user_a: str,
    db_session: AsyncSession,
):
    headers = {"Authorization": f"Bearer {token_user_a}"}

    conv = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Feedback Test Chat"
    )
    msg = await ConversationService.add_message(
        db_session,
        conversation_id=conv.id,
        user_id=test_user_a.id,
        role="assistant",
        content="Here is a high quality response.",
    )

    # 1. Submit initial thumbs-up feedback
    res = await client.post(
        f"/api/v1/messages/{msg.id}/feedback",
        headers=headers,
        json={"rating": "up", "comment": "Very accurate explanation!"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["rating"] == "up"
    assert data["comment"] == "Very accurate explanation!"

    # 2. Update feedback to thumbs-down
    update_res = await client.post(
        f"/api/v1/messages/{msg.id}/feedback",
        headers=headers,
        json={"rating": "down", "comment": "Changed my mind."},
    )
    assert update_res.status_code == 201
    assert update_res.json()["rating"] == "down"

    # 3. Verify in database
    stmt = select(MessageFeedback).where(MessageFeedback.message_id == msg.id)
    saved = (await db_session.execute(stmt)).scalar_one_or_none()
    assert saved is not None
    assert saved.rating == "down"
    assert saved.comment == "Changed my mind."


@pytest.mark.asyncio
async def test_feedback_idor_protection(
    client: AsyncClient,
    test_user_a,
    test_user_b,
    token_user_b: str,
    db_session: AsyncSession,
):
    """User B cannot submit feedback on User A's conversation message."""
    conv_a = await ConversationService.create_conversation(
        db_session, user_id=test_user_a.id, title="Alice Chat"
    )
    msg_a = await ConversationService.add_message(
        db_session,
        conversation_id=conv_a.id,
        user_id=test_user_a.id,
        role="assistant",
        content="Alice private message.",
    )

    # Bob attempts to submit feedback on Alice's message -> 404
    bob_res = await client.post(
        f"/api/v1/messages/{msg_a.id}/feedback",
        headers={"Authorization": f"Bearer {token_user_b}"},
        json={"rating": "down"},
    )
    assert bob_res.status_code == 404


def test_evaluation_dataset_completeness():
    """Verify evaluation dataset contains 50 prompts across all required categories."""
    dataset = load_dataset()
    assert len(dataset) == 50

    required_categories = {
        "general_knowledge",
        "programming_and_debugging",
        "mathematics_and_reasoning",
        "summarization",
        "ambiguous_questions",
        "uncertainty_and_limits",
        "prompt_injection_safety",
        "harmful_disallowed_requests",
    }

    found_categories = set(item["category"] for item in dataset)
    assert required_categories.issubset(found_categories)

    for item in dataset:
        assert "id" in item
        assert "prompt" in item
        assert "expected_behavior" in item
        assert len(item["criteria"]) > 0


@pytest.mark.asyncio
async def test_evaluation_runner_execution():
    """Verify evaluation runner executes prompts, scores heuristics, and writes report."""
    mock_provider = AsyncMock(spec=BaseLLMProvider)
    mock_provider.provider_name = "MockEvaluatedProvider"
    mock_provider.default_model = "mock-model"

    async def mock_generate(messages, **kwargs):
        content = "I cannot fulfill harmful requests and am uncertain about unrecorded facts."
        return LLMResponse(content=content, model="mock-model", provider="Mock")

    mock_provider.generate_response = mock_generate

    summary = await run_evaluation(max_items=5, provider_instance=mock_provider)

    assert summary["total_prompts"] == 5
    assert summary["provider"] == "MockEvaluatedProvider"
    assert "overall_score_pct" in summary
    assert "category_scores_pct" in summary
    assert summary["overall_score_pct"] > 0
