from typing import Optional
from app.llm.base import BaseLLMProvider, LLMInvalidRequestError
from app.llm.gemini_provider import GeminiProvider
from app.llm.openai_provider import OpenAIProvider


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory to retrieve configured LLM provider instance."""
    name = (provider_name or "gemini").strip().lower()
    if name in ("gemini", "google"):
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    else:
        raise LLMInvalidRequestError(
            f"Unsupported LLM provider '{provider_name}'. Supported providers are 'Gemini' and 'OpenAI'."
        )
