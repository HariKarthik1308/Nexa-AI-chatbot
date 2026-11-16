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

logger = logging.getLogger("nexa_ai.llm.gemini")

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._default_model = default_model or settings.GEMINI_MODEL or "gemini-1.5-flash"
        self._client = None

    @property
    def provider_name(self) -> str:
        return "Gemini"

    @property
    def default_model(self) -> str:
        return self._default_model

    def _get_client(self):
        if not self._api_key:
            raise LLMAuthError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in the backend environment."
            )
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except ImportError as e:
                raise LLMError(f"google-genai SDK is not installed: {str(e)}")
            except Exception as e:
                raise LLMAuthError(f"Failed to initialize Gemini client: {str(e)}")
        return self._client

    def _convert_messages(self, messages: List[LLMMessage]):
        from google.genai import types

        contents = []
        for msg in messages:
            if msg.role == "system":
                # System instructions should be supplied via config, but if encountered in history map to user
                role = "user"
            elif msg.role == "assistant":
                role = "model"
            else:
                role = "user"

            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )
        return contents

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
        from google.genai import types
        from google.genai.errors import APIError

        model_name = model or self._default_model
        contents = self._convert_messages(messages)

        config_params = {"temperature": temperature}
        if system_instruction:
            config_params["system_instruction"] = system_instruction
        if max_output_tokens:
            config_params["max_output_tokens"] = max_output_tokens

        config = types.GenerateContentConfig(**config_params)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )

                input_tokens = None
                output_tokens = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)

                return LLMResponse(
                    content=response.text or "",
                    model=model_name,
                    provider=self.provider_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            except APIError as exc:
                status_code = getattr(exc, "code", None)
                message = str(exc)

                if status_code in (401, 403):
                    raise LLMAuthError(f"Gemini authentication failed: {message}", status_code)
                elif status_code == 429:
                    if attempt < MAX_RETRIES:
                        sleep_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                        logger.warning(f"Rate limited by Gemini. Retrying in {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
                        continue
                    raise LLMRateLimitError("Gemini rate limit exceeded.", status_code)
                elif status_code == 400:
                    raise LLMInvalidRequestError(f"Invalid Gemini request: {message}", status_code)
                elif status_code in (500, 503, 504) and attempt < MAX_RETRIES:
                    sleep_time = INITIAL_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(f"Gemini server error {status_code}. Retrying in {sleep_time}s...")
                    await asyncio.sleep(sleep_time)
                    continue
                else:
                    raise LLMError(f"Gemini API error: {message}", status_code)

            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(INITIAL_BACKOFF)
                    continue
                raise LLMTimeoutError("Request to Gemini API timed out.")
            except Exception as exc:
                if isinstance(exc, LLMError):
                    raise exc
                raise LLMError(f"Unexpected error communicating with Gemini: {str(exc)}")

        raise LLMTimeoutError("Failed to obtain a response after maximum retries.")

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
        from google.genai import types
        from google.genai.errors import APIError

        model_name = model or self._default_model
        contents = self._convert_messages(messages)

        config_params = {"temperature": temperature}
        if system_instruction:
            config_params["system_instruction"] = system_instruction
        if max_output_tokens:
            config_params["max_output_tokens"] = max_output_tokens

        config = types.GenerateContentConfig(**config_params)

        try:
            stream = await client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config,
            )

            async for chunk in stream:
                if chunk.text:
                    yield chunk.text

        except APIError as exc:
            status_code = getattr(exc, "code", None)
            if status_code in (401, 403):
                raise LLMAuthError(f"Gemini authentication error: {str(exc)}", status_code)
            elif status_code == 429:
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {str(exc)}", status_code)
            elif status_code == 400:
                raise LLMInvalidRequestError(f"Invalid request to Gemini: {str(exc)}", status_code)
            else:
                raise LLMError(f"Gemini stream error: {str(exc)}", status_code)
        except Exception as exc:
            if isinstance(exc, LLMError):
                raise exc
            raise LLMError(f"Unexpected stream error: {str(exc)}")
