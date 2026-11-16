import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.prompts import NEXA_SYSTEM_INSTRUCTION
from app.llm.base import LLMError, LLMMessage
from app.llm.factory import get_llm_provider
from app.models.message import Message
from app.models.usage import UsageRecord
from app.services.conversation_service import ConversationService

logger = logging.getLogger("nexa_ai.services.chat")


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
        # 1. Enforce conversation ownership
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found or access denied.")

        # 2. Persist user message
        user_msg = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=content,
            status="complete",
        )

        # 3. Retrieve LLM provider
        provider = get_llm_provider(provider_name)
        active_model = model_name or provider.default_model

        # 4. Assemble bounded history context (latest 20 messages)
        history_msgs = conversation.messages[-20:]
        llm_messages = [
            LLMMessage(role=m.role, content=m.content)
            for m in history_msgs
            if m.status == "complete"
        ]

        # 5. Call LLM provider
        try:
            llm_response = await provider.generate_response(
                messages=llm_messages,
                model=active_model,
                system_instruction=NEXA_SYSTEM_INSTRUCTION,
            )

            # 6. Persist assistant response
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

            # 7. Record usage metadata
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
            # Persist failed assistant message for audit and user feedback
            failed_msg = await ConversationService.add_message(
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
