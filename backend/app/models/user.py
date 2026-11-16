from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.usage import UsageRecord, MessageFeedback


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Conversation.created_at)",
    )

    usage_records: Mapped[List["UsageRecord"]] = relationship(
        "UsageRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    feedbacks: Mapped[List["MessageFeedback"]] = relationship(
        "MessageFeedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )
