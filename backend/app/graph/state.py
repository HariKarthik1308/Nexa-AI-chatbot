from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class NexaGraphState(TypedDict):
    """State definition for the NexaAI LangGraph Agent Workflow."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    chat_id: str
    provider_name: str
    model_name: Optional[str]
    intent: str
    safety_flagged: bool
    safety_reason: Optional[str]
    system_instruction: str
    response_content: str
    token_usage: Dict[str, int]
    metadata: Dict[str, Any]
