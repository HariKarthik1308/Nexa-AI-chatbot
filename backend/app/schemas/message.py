from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=32000)


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: str
    conversation_id: str
    status: str
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageFeedbackCreate(BaseModel):
    rating: str = Field(..., pattern="^(up|down)$")
    comment: Optional[str] = Field(None, max_length=1000)
