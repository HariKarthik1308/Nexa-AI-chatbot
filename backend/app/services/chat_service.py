import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.prompts import NEXA_SYSTEM_INSTRUCTION
from app.llm.base import LLMError, LLMMessage
from app.llm.factory import get_llm_provider
from app.models.message import Message
from app.models.usage import UsageRecord
from app.services.conversation_service import ConversationService

logger = logging.getLogger("nexa_ai.services.chat")


def format_sse(event: str, data: dict) -> str:
    """Format SSE payload adhering to standard event stream format."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class ChatService:
    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        content: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Message:
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found or access denied.")

        user_msg = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
            status="complete",
        )

        provider = get_llm_provider(provider_name)
        active_model = model_name or provider.default_model

        history_msgs = conversation.messages[-20:]
        llm_messages = [
            LLMMessage(role=m.role, content=m.content)
            for m in history_msgs
            if m.status == "complete"
        ]

        try:
            llm_response = await provider.generate_response(
                messages=llm_messages,
                model=active_model,
                system_instruction=NEXA_SYSTEM_INSTRUCTION,
            )

            assistant_msg = await ConversationService.add_message(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=llm_response.content,
                status="complete",
                model_provider=provider.provider_name,
                model_name=llm_response.model,
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )

            usage = UsageRecord(
                user_id=user_id,
                provider=provider.provider_name,
                model=llm_response.model,
                input_tokens=llm_response.input_tokens or 0,
                output_tokens=llm_response.output_tokens or 0,
            )
            db.add(usage)
            await db.commit()

            return assistant_msg

        except LLMError as exc:
            logger.error(f"LLM generation failed: {exc.message}")
            await ConversationService.add_message(
                db=db,
                conversation_id=conversation_id,
                user_id=user_id,
                role="assistant",
                content=f"Error: {exc.message}",
                status="failed",
                model_provider=provider.provider_name,
                model_name=active_model,
            )
            raise exc

    @staticmethod
    async def stream_message(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        content: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens chunk-by-chunk using Server-Sent Events (SSE)."""
        provider = get_llm_provider(provider_name)
        active_model = model_name or provider.default_model
        assistant_message_id = None
        accumulated_text = ""
        is_aborted = False

        # Phase A: Initial setup & user message insertion in database
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            yield format_sse("error", {"code": "NOT_FOUND", "message": "Conversation not found."})
            return

        # Save user prompt
        await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
            status="complete",
        )

        # Create placeholder assistant message
        assistant_msg = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content="",
            status="streaming",
            model_provider=provider.provider_name,
            model_name=active_model,
        )
        assistant_message_id = assistant_msg.id

        # Context history
        history_msgs = conversation.messages[-20:]
        llm_messages = [
            LLMMessage(role=m.role, content=m.content)
            for m in history_msgs
            if m.status == "complete"
        ]

        # Announce stream start
        yield format_sse(
            "message_start",
            {
                "messageId": assistant_message_id,
                "conversationId": conversation_id,
                "role": "assistant",
                "model": active_model,
                "provider": provider.provider_name,
            },
        )

        # Phase B: Stream tokens from provider
        try:
            token_stream = provider.generate_stream(
                messages=llm_messages,
                model=active_model,
                system_instruction=NEXA_SYSTEM_INSTRUCTION,
            )

            async for chunk in token_stream:
                # Check for client cancellation/disconnection
                if request and await request.is_disconnected():
                    logger.info(f"Client disconnected in-flight for message {assistant_message_id}")
                    is_aborted = True
                    break

                accumulated_text += chunk
                yield format_sse("content_delta", {"delta": chunk})

        except LLMError as exc:
            logger.error(f"Stream error for message {assistant_message_id}: {exc.message}")
            if assistant_message_id:
                msg = await db.get(Message, assistant_message_id)
                if msg:
                    msg.status = "failed"
                    msg.content = accumulated_text or f"Error: {exc.message}"
                    await db.commit()

            yield format_sse("error", {"code": "PROVIDER_ERROR", "message": exc.message})
            return
        except Exception as exc:
            logger.error(f"Unexpected stream error: {str(exc)}", exc_info=True)
            if assistant_message_id:
                msg = await db.get(Message, assistant_message_id)
                if msg:
                    msg.status = "failed"
                    msg.content = accumulated_text or "Error: Unexpected stream failure."
                    await db.commit()

            yield format_sse("error", {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred during streaming."})
            return

        # Phase C: Finalize message state in database
        final_status = "partial" if is_aborted else "complete"
        estimated_output_tokens = len(accumulated_text.split())

        if assistant_message_id:
            msg = await db.get(Message, assistant_message_id)
            if msg:
                msg.status = final_status
                msg.content = accumulated_text
                msg.output_tokens = estimated_output_tokens
                await db.commit()

        # Record token usage
        usage = UsageRecord(
            user_id=user_id,
            provider=provider.provider_name,
            model=active_model,
            input_tokens=len(content.split()),
            output_tokens=estimated_output_tokens,
        )
        db.add(usage)
        await db.commit()

        if not is_aborted:
            yield format_sse(
                "message_complete",
                {
                    "messageId": assistant_message_id,
                    "status": "complete",
                    "content": accumulated_text,
                },
            )
            yield format_sse(
                "usage",
                {
                    "estimatedOutputTokens": estimated_output_tokens,
                },
            )

    @staticmethod
    async def send_langgraph_message(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        content: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Message:
        """Process message through multi-node LangGraph agent workflow."""
        from app.graph.service import graph_service

        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found or access denied.")

        await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
            status="complete",
        )

        history_msgs = conversation.messages[-20:]
        formatted_history = [
            {"role": m.role, "content": m.content}
            for m in history_msgs
            if m.status == "complete"
        ]

        result = await graph_service.run(
            messages=formatted_history,
            user_id=user_id,
            chat_id=conversation_id,
            provider_name=provider_name or "gemini",
            model_name=model_name,
        )

        tokens = result.get("token_usage", {})
        assistant_message = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content=result["content"],
            model_name=model_name or "langgraph-agent",
            model_provider="LangGraph",
            input_tokens=tokens.get("input_tokens", 0),
            output_tokens=tokens.get("output_tokens", 0),
            status="complete",
        )

        return assistant_message

    @staticmethod
    async def stream_langgraph_message(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        content: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream message processed through LangGraph agent workflow via SSE."""
        from app.graph.service import graph_service

        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            yield format_sse("error", {"code": "NOT_FOUND", "message": "Conversation not found or access denied."})
            return

        user_msg = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
            status="complete",
        )

        assistant_msg = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="assistant",
            content="",
            model_name=model_name or "langgraph-agent",
            model_provider="LangGraph",
            status="streaming",
        )

        yield format_sse(
            "message_start",
            {
                "messageId": assistant_msg.id,
                "conversationId": conversation_id,
                "role": "assistant",
                "model": assistant_msg.model,
                "provider": "LangGraph",
            },
        )

        history_msgs = conversation.messages[-20:]
        formatted_history = [
            {"role": m.role, "content": m.content}
            for m in history_msgs
            if m.status == "complete"
        ]

        accumulated_text = ""
        is_aborted = False

        try:
            async for event in graph_service.stream(
                messages=formatted_history,
                user_id=user_id,
                chat_id=conversation_id,
                provider_name=provider_name or "gemini",
                model_name=model_name,
            ):
                if request and await request.is_disconnected():
                    is_aborted = True
                    break

                ev_type = event.get("event")
                ev_data = event.get("data", {})
                if ev_type == "content_delta":
                    accumulated_text += ev_data.get("delta", "")
                yield format_sse(ev_type, ev_data)

        except Exception as exc:
            logger.error("LangGraph streaming failed: %s", exc, exc_info=True)
            msg = await db.get(Message, assistant_msg.id)
            if msg:
                msg.status = "failed"
                msg.content = accumulated_text or "Error in LangGraph workflow."
                await db.commit()
            yield format_sse("error", {"code": "LANGGRAPH_ERROR", "message": str(exc)})
            return

        final_status = "partial" if is_aborted else "complete"
        msg = await db.get(Message, assistant_msg.id)
        if msg:
            msg.status = final_status
            msg.content = accumulated_text
            msg.output_tokens = len(accumulated_text.split())
            await db.commit()

        if not is_aborted:
            yield format_sse("usage", {"estimatedOutputTokens": len(accumulated_text.split())})
