from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.usage import MessageFeedback
from app.models.user import User
from app.schemas.message import MessageFeedbackCreate

router = APIRouter()


@router.post("/{message_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_message_feedback(
    message_id: str,
    payload: MessageFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit quality feedback (thumbs up / thumbs down with optional comment) on an assistant message."""
    # Enforce conversation ownership to prevent unauthorized feedback manipulation
    stmt = (
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Message.id == message_id,
            Conversation.user_id == current_user.id,
        )
    )
    message = (await db.execute(stmt)).scalar_one_or_none()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied.",
        )

    # Check for existing feedback
    fb_stmt = select(MessageFeedback).where(
        MessageFeedback.message_id == message_id,
        MessageFeedback.user_id == current_user.id,
    )
    feedback = (await db.execute(fb_stmt)).scalar_one_or_none()

    if feedback:
        feedback.rating = payload.rating
        feedback.comment = payload.comment
    else:
        feedback = MessageFeedback(
            message_id=message_id,
            user_id=current_user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
        db.add(feedback)

    await db.commit()
    await db.refresh(feedback)

    return {
        "status": "success",
        "messageId": message_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
    }
