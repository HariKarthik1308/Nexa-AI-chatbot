import asyncio
import logging
from typing import AsyncGenerator, List, Optional
from app.core.config import settings
from app.llm.base import (
    BaseLLMProvider,
    LLMAuthError,
    LLMError,
    LLMInvalidRequestError,
    LLMMessage,
    LLMRateLimitError,
    LLMResponse,
    LLMTimeoutError,
)

logger = logging.getLogger("nexa_ai.llm.openai")

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._default_model = default_model or settings.OPENAI_MODEL or "gpt-4o-mini"
        self._client = None

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _get_client(self):
        if not self._api_key:
            raise LLMAuthError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY in the backend environment."
            )
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError as e:
                raise LLMError(f"openai package is not installed: {str(e)}")
            except Exception as e:
                raise LLMAuthError(f"Failed to initialize OpenAI client: {str(e)}")
        return self._client

    def _convert_messages(self, messages: List[LLMMessage], system_instruction: Optional[str] = None):
        formatted = []
        if system_instruction:
            formatted.append({"role": "system", "content": system_instruction})

        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})
        return formatted

    async def generate_response(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        client = self._get_client()
        import openai

        model_name = model or self._default_model
        formatted_messages = self._convert_messages(messages, system_instruction)

        params = {
            "model": model_name,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if max_output_tokens:
            params["max_tokens"] = max_output_tokens

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                completion = await client.chat.completions.create(**params)
                choice = completion.choices[0]
                content = choice.message.content or ""

                input_tokens = None
                output_tokens = None
                if completion.usage:
                    input_tokens = completion.usage.prompt_tokens
                    output_tokens = completion.usage.completion_tokens

                return LLMResponse(
                    content=content,
                    model=model_name,
                    provider=self.provider_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    finish_reason=choice.finish_reason,
                )

            except openai.AuthenticationError as exc:
                raise LLMAuthError(f"OpenAI authentication failed: {str(exc)}", 401)
            except openai.RateLimitError as exc:
                if attempt < MAX_RETRIES:
                    sleep_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(f"Rate limited by OpenAI. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                    continue
                raise LLMRateLimitError(f"OpenAI rate limit exceeded: {str(exc)}", 429)
            except openai.BadRequestError as exc:
                raise LLMInvalidRequestError(f"Invalid OpenAI request: {str(exc)}", 400)
            except openai.APITimeoutError:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(INITIAL_BACKOFF)
                    continue
                raise LLMTimeoutError("Request to OpenAI timed out.")
            except openai.APIError as exc:
                if attempt < MAX_RETRIES and getattr(exc, "status_code", 500) >= 500:
                    await asyncio.sleep(INITIAL_BACKOFF)
                    continue
                raise LLMError(f"OpenAI API error: {str(exc)}", getattr(exc, "status_code", 500))
            except Exception as exc:
                if isinstance(exc, LLMError):
                    raise exc
                raise LLMError(f"Unexpected error communicating with OpenAI: {str(exc)}")

        raise LLMTimeoutError("Failed to obtain response from OpenAI after maximum retries.")

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()
        import openai

        model_name = model or self._default_model
        formatted_messages = self._convert_messages(messages, system_instruction)

        params = {
            "model": model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": True,
        }
        if max_output_tokens:
            params["max_tokens"] = max_output_tokens

        try:
            stream = await client.chat.completions.create(**params)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except openai.AuthenticationError as exc:
            raise LLMAuthError(f"OpenAI authentication failed: {str(exc)}", 401)
        except openai.RateLimitError as exc:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {str(exc)}", 429)
        except openai.BadRequestError as exc:
            raise LLMInvalidRequestError(f"Invalid OpenAI request: {str(exc)}", 400)
        except Exception as exc:
            if isinstance(exc, LLMError):
                raise exc
            raise LLMError(f"OpenAI streaming error: {str(exc)}")
