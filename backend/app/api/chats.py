from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.core.rate_limit import rate_limit
from app.llm.base import (
    LLMAuthError,
    LLMError,
    LLMInvalidRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ConversationListItem,
    ConversationRead,
    ConversationUpdate,
    MessageCreateRequest,
)
from app.schemas.message import MessageRead
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService

router = APIRouter()


@router.get("", response_model=List[ConversationListItem])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """List current user's conversations."""
    conversations = await ConversationService.list_conversations(
        db, user_id=current_user.id, limit=limit, offset=offset
    )
    return conversations


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation thread."""
    conversation = await ConversationService.create_conversation(
        db, user_id=current_user.id, title=payload.title or "New Conversation"
    )
    return conversation


@router.get("/{chat_id}", response_model=ConversationRead)
async def get_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chat and messages, enforcing user ownership."""
    conversation = await ConversationService.get_conversation(
        db, conversation_id=chat_id, user_id=current_user.id
    )
    if not conversation:
        # Return 404 to avoid IDOR enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


@router.patch("/{chat_id}", response_model=ConversationRead)
async def rename_chat(
    chat_id: str,
    payload: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rename a conversation."""
    conversation = await ConversationService.rename_conversation(
        db, conversation_id=chat_id, user_id=current_user.id, new_title=payload.title
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation."""
    success = await ConversationService.delete_conversation(
        db, conversation_id=chat_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return None


@router.post(
    "/{chat_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, key_prefix="chat_msg"))],
)
async def send_chat_message(
    chat_id: str,
    payload: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to a conversation and get the generated LLM response."""
    try:
        assistant_message = await ChatService.send_message(
            db=db,
            conversation_id=chat_id,
            user_id=current_user.id,
            content=payload.content,
            provider_name=payload.provider,
            model_name=payload.model,
        )
        return assistant_message
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LLMAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
    except LLMInvalidRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=exc.message)
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.message)


@router.post(
    "/{chat_id}/messages/stream",
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, key_prefix="chat_stream"))],
)
async def stream_chat_message(
    chat_id: str,
    payload: MessageCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream LLM response chunk-by-chunk using Server-Sent Events (SSE)."""
    generator = ChatService.stream_message(
        db=db,
        conversation_id=chat_id,
        user_id=current_user.id,
        content=payload.content,
        provider_name=payload.provider,
        model_name=payload.model,
        request=request,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{chat_id}/agent/graph",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, key_prefix="chat_agent"))],
)
async def send_agent_graph_message(
    chat_id: str,
    payload: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute request via LangGraph multi-node state graph (guardrails -> intent -> reasoning -> redaction)."""
    try:
        assistant_message = await ChatService.send_langgraph_message(
            db=db,
            conversation_id=chat_id,
            user_id=current_user.id,
            content=payload.content,
            provider_name=payload.provider,
            model_name=payload.model,
        )
        return assistant_message
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except LLMAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=exc.message)
    except LLMInvalidRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.post(
    "/{chat_id}/agent/graph/stream",
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, key_prefix="chat_agent_stream"))],
)
async def stream_agent_graph_message(
    chat_id: str,
    payload: MessageCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream LLM response chunk-by-chunk through LangGraph workflow via SSE."""
    generator = ChatService.stream_langgraph_message(
        db=db,
        conversation_id=chat_id,
        user_id=current_user.id,
        content=payload.content,
        provider_name=payload.provider,
        model_name=payload.model,
        request=request,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


