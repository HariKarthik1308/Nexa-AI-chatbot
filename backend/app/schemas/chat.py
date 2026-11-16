from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.message import MessageRead


class ConversationBase(BaseModel):
    title: str = Field("New Conversation", min_length=1, max_length=255)


class ConversationCreate(BaseModel):
    title: Optional[str] = Field("New Conversation", max_length=255)


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)


class ConversationRead(ConversationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageRead]] = None

    model_config = {"from_attributes": True}


class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=16000)
    provider: Optional[str] = Field(None, max_length=64)
    model: Optional[str] = Field(None, max_length=128)


class ConversationListItem(ConversationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_message_preview: Optional[str] = None

    model_config = {"from_attributes": True}
