from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_conversations_user_created", "user_id", "created_at"),
    )
