from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, List, Optional


class LLMError(Exception):
    """Base exception for all LLM provider errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LLMAuthError(LLMError):
    """Raised when authentication credentials (API key) are missing or invalid."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when provider rate limits or quotas are exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when an API request to the provider times out."""
    pass


class LLMInvalidRequestError(LLMError):
    """Raised when the request parameters or contents are invalid."""
    pass


@dataclass
class LLMMessage:
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class LLMStreamChunk:
    delta: str
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract interface defining standard provider operations."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier, e.g., 'Gemini', 'OpenAI', 'Anthropic'."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier configured from environment."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a complete non-streaming response."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens chunk-by-chunk."""
        pass
