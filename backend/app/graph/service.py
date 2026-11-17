"""NexaAI LangGraph Service — High-level interface for agent execution."""
from typing import Any, AsyncGenerator, Dict, List, Optional
from langchain_core.messages import AIMessage, HumanMessage
from app.graph.graph import compile_nexa_graph
from app.graph.nodes import INJECTION_PATTERNS
from app.llm.base import LLMMessage
from app.llm.factory import get_llm_provider
import re


class NexaGraphService:
    """Service orchestrating LangGraph executions with streaming & non-streaming support."""

    def __init__(self):
        self._compiled_graph = None

    @property
    def graph(self):
        if self._compiled_graph is None:
            self._compiled_graph = compile_nexa_graph()
        return self._compiled_graph

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        chat_id: str,
        provider_name: str = "gemini",
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes the full LangGraph pipeline non-streaming."""
        # Convert dict messages to LangChain messages
        lc_messages = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            else:
                lc_messages.append(AIMessage(content=content))

        initial_state = {
            "messages": lc_messages,
            "user_id": user_id,
            "chat_id": chat_id,
            "provider_name": provider_name,
            "model_name": model_name,
            "intent": "general_qa",
            "safety_flagged": False,
            "safety_reason": None,
            "system_instruction": "",
            "response_content": "",
            "token_usage": {"input_tokens": 0, "output_tokens": 0},
            "metadata": {},
        }

        final_state = await self.graph.ainvoke(initial_state)
        return {
            "content": final_state.get("response_content", ""),
            "intent": final_state.get("intent", "general_qa"),
            "safety_flagged": final_state.get("safety_flagged", False),
            "safety_reason": final_state.get("safety_reason"),
            "token_usage": final_state.get("token_usage", {}),
            "metadata": final_state.get("metadata", {}),
        }

    async def stream(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        chat_id: str,
        provider_name: str = "gemini",
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streams responses through LangGraph guardrail screening and progressive token emission."""
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # Step 1: Input Guardrail Check
        prompt_lower = last_user_msg.lower()
        is_flagged = False
        matched_rule = None
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                is_flagged = True
                matched_rule = pattern
                break

        if is_flagged:
            yield {
                "event": "guardrail_alert",
                "data": {"rule": matched_rule, "action": "blocked"},
            }
            refusal_text = (
                "I cannot fulfill this request. NexaAI is configured to decline requests "
                "involving malicious exploitation, credential extraction, or security bypasses."
            )
            yield {
                "event": "content_delta",
                "data": {"delta": refusal_text},
            }
            yield {
                "event": "message_complete",
                "data": {
                    "full_content": refusal_text,
                    "intent": "harmful_blocked",
                    "guardrail_status": "blocked",
                },
            }
            return

        # Step 2: Intent Analysis
        intent = "general_qa"
        if any(k in prompt_lower for k in ["code", "function", "debug", "python", "typescript", "react", "bug"]):
            intent = "code_generation"
        elif any(k in prompt_lower for k in ["calculate", "derivative", "integral", "equation", "solve", "math"]):
            intent = "math_reasoning"
        elif any(k in prompt_lower for k in ["summarize", "tldr", "synopsis", "bullet points"]):
            intent = "summarization"

        yield {
            "event": "agent_state",
            "data": {
                "node": "intent_analyzer",
                "intent": intent,
                "guardrail_status": "passed",
            },
        }

        # Step 3: Stream generation from provider
        provider = get_llm_provider(provider_name)
        llm_messages = [
            LLMMessage(role=m.get("role", "user"), content=m.get("content", ""))
            for m in messages
        ]

        full_content = []
        async for chunk in provider.generate_stream(
            messages=llm_messages,
            model=model_name,
        ):
            full_content.append(chunk)
            yield {
                "event": "content_delta",
                "data": {"delta": chunk},
            }

        joined = "".join(full_content)
        yield {
            "event": "message_complete",
            "data": {
                "full_content": joined,
                "intent": intent,
                "guardrail_status": "passed",
            },
        }


graph_service = NexaGraphService()
