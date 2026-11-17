import re
from typing import Any, Dict
from langchain_core.messages import AIMessage, HumanMessage
from app.core.prompts import NEXA_SYSTEM_INSTRUCTION
from app.llm.base import LLMMessage
from app.llm.factory import get_llm_provider
from app.graph.state import NexaGraphState


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"jailbreak",
    r"\bdan\s+mode\b",
    r"developer\s+mode\s+enabled",
    r"extract\s+(api\s+key|password|secret)",
    r"bypass\s+(security|auth|permissions)",
    r"\b(malware|keylogger|ddos|sql\s+injection)\b",
]

SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z\-_]{20,}",
    r"sk-[a-zA-Z0-9]{20,}",
    r"bearer\s+[a-zA-Z0-9_\-\.]+",
]


async def input_guardrail_node(state: NexaGraphState) -> Dict[str, Any]:
    """Inspects prompt for prompt injections, credential extraction, or abusive queries."""
    messages = state.get("messages", [])
    user_prompt = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human":
            user_prompt = str(m.content)
            break

    prompt_lower = user_prompt.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return {
                "safety_flagged": True,
                "safety_reason": f"Prompt matched safety guardrail rule: {pattern}",
                "intent": "harmful_blocked",
            }

    return {
        "safety_flagged": False,
        "safety_reason": None,
    }


async def intent_analyzer_node(state: NexaGraphState) -> Dict[str, Any]:
    """Classifies user intent to dynamically tailor system instructions and depth."""
    messages = state.get("messages", [])
    user_prompt = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human":
            user_prompt = str(m.content)
            break

    prompt_lower = user_prompt.lower()
    base_instruction = NEXA_SYSTEM_INSTRUCTION

    if any(k in prompt_lower for k in ["code", "function", "debug", "python", "typescript", "react", "bug", "algorithm", "class"]):
        intent = "code_generation"
        system_instruction = (
            f"{base_instruction}\n\n"
            "[Context: Programming Task]\n"
            "- Provide idiomatic, clean, modular code with clear syntax highlighting.\n"
            "- Include robust error handling and edge cases.\n"
            "- Keep explanations concise and focused on architectural decisions."
        )
    elif any(k in prompt_lower for k in ["calculate", "derivative", "integral", "equation", "solve", "math", "proof"]):
        intent = "math_reasoning"
        system_instruction = (
            f"{base_instruction}\n\n"
            "[Context: Mathematical Reasoning]\n"
            "- Show rigorous step-by-step derivations before concluding.\n"
            "- Double check arithmetic and boundary conditions."
        )
    elif any(k in prompt_lower for k in ["summarize", "tldr", "synopsis", "key takeaways", "bullet points"]):
        intent = "summarization"
        system_instruction = (
            f"{base_instruction}\n\n"
            "[Context: Summarization]\n"
            "- Provide structured, high-signal executive bullet points.\n"
            "- Highlight critical takeaways and omit unnecessary filler."
        )
    else:
        intent = "general_qa"
        system_instruction = base_instruction

    return {
        "intent": intent,
        "system_instruction": system_instruction,
    }


async def refusal_handler_node(state: NexaGraphState) -> Dict[str, Any]:
    """Produces a safe, polite refusal when input fails guardrail checks."""
    refusal_text = (
        "I cannot fulfill this request. NexaAI is configured to decline requests "
        "involving malicious exploitation, credential extraction, or security bypasses."
    )
    return {
        "response_content": refusal_text,
        "messages": [AIMessage(content=refusal_text)],
        "token_usage": {"input_tokens": 10, "output_tokens": 25},
    }


async def agent_reasoner_node(state: NexaGraphState) -> Dict[str, Any]:
    """Executes model reasoning using the configured provider and dynamic instructions."""
    provider_name = state.get("provider_name", "gemini")
    model_name = state.get("model_name")
    system_instruction = state.get("system_instruction", NEXA_SYSTEM_INSTRUCTION)
    messages = state.get("messages", [])

    # Convert langchain messages to LLMMessage
    llm_messages = []
    for m in messages:
        role = "user" if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human" else "assistant"
        llm_messages.append(LLMMessage(role=role, content=str(m.content)))

    provider = get_llm_provider(provider_name)
    response = await provider.generate_response(
        messages=llm_messages,
        model=model_name,
        system_instruction=system_instruction,
    )

    return {
        "response_content": response.content,
        "messages": [AIMessage(content=response.content)],
        "token_usage": {
            "input_tokens": response.input_tokens or 0,
            "output_tokens": response.output_tokens or 0,
        },
    }


async def output_guardrail_node(state: NexaGraphState) -> Dict[str, Any]:
    """Inspects response output for credential/secret leakage before returning."""
    raw_content = state.get("response_content", "")
    sanitized = raw_content

    for pattern in SECRET_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED_SECRET]", sanitized, flags=re.IGNORECASE)

    return {
        "response_content": sanitized,
        "metadata": {
            **state.get("metadata", {}),
            "guardrail_inspected": True,
            "intent": state.get("intent", "general_qa"),
            "safety_flagged": state.get("safety_flagged", False),
        },
    }
