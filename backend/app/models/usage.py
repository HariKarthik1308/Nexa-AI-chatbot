from typing import Optional, TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message


class UsageRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "usage_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="usage_records")

    __table_args__ = (
        Index("ix_usage_user_created", "user_id", "created_at"),
    )


class MessageFeedback(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_feedback"

    message_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[str] = mapped_column(String(16), nullable=False)  # up, down
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    message: Mapped["Message"] = relationship("Message", back_populates="feedbacks")
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")
