from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.usage import MessageFeedback


class Message(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="complete", nullable=False)  # complete, streaming, partial, error
    model_provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    feedbacks: Mapped[List["MessageFeedback"]] = relationship(
        "MessageFeedback",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_messages_conv_created", "conversation_id", "created_at"),
    )
