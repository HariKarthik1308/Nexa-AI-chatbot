from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationService:
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: str,
        title: str = "New Conversation",
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )
        conversation.messages = []
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
    ) -> Optional[Conversation]:
        """Fetch conversation enforcing strict user ownership (prevents IDOR)."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .options(selectinload(Conversation.messages))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Conversation]:
        """List conversations belonging only to the authenticated user."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def rename_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        new_title: str,
    ) -> Optional[Conversation]:
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return None
        conversation.title = new_title
        await db.commit()
        return await ConversationService.get_conversation(db, conversation_id, user_id)

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        await db.delete(conversation)
        await db.commit()
        return True

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        status: str = "complete",
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> Optional[Message]:
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return None

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            status=status,
            model_provider=model_provider,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message
