"""
OpenAI LLM Provider Implementation
"""
from typing import Any, Dict, Optional, AsyncGenerator
import logging
import json
import httpx

from ..base import (
    BaseLLMProvider,
    LLMCapabilities,
    LLMCapability,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from ..exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMError,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    An implementation of the LLMProvider interface for OpenAI's models.
    """

    def __init__(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ):
        """
        Initializes the OpenAI provider.

        Args:
            provider_name: The name of the provider.
            api_key: The OpenAI API key.
            base_url: The base URL for the OpenAI API.
            model: The default model to use for requests (e.g., "gpt-4-turbo").
            temperature: The default sampling temperature.
            max_tokens: The default maximum number of tokens to generate.
            timeout: The request timeout in seconds.
            max_retries: The maximum number of retry attempts.
            retry_delay: The delay between retries in seconds.
            **kwargs: Additional provider-specific configuration.
        """
        super().__init__(
            provider_name=provider_name,
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs,
        )
        self.model = model or "gpt-4-turbo"
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def initialize(self) -> None:
        """Initializes the httpx client for making API requests."""
        if not self.api_key:
            raise LLMAuthenticationError(
                f"API key is required for {self.provider_name}",
                provider=self.provider_name,
            )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=self.timeout
        )
        logger.info(f"{self.provider_name} provider initialized.")

    async def close(self) -> None:
        """Closes the httpx client."""
        if self._client:
            await self._client.aclose()
        logger.info(f"{self.provider_name} provider closed.")

    def _prepare_api_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepares the request payload for the OpenAI API."""
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        return {
            "model": request.model or self.model,
            "messages": messages,
            "temperature": request.temperature or self.temperature,
            "max_tokens": request.max_tokens or self.max_tokens,
        }

    def _parse_response(self, data: Dict[str, Any], request: LLMRequest) -> LLMResponse:
        """Parses a successful response from the OpenAI API."""
        choice = data["choices"][0]
        usage_data = data.get("usage", {})
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage=LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
            ),
            request_id=request.request_id,
            finish_reason=choice.get("finish_reason")
        )

    async def process(self, request: LLMRequest) -> LLMResponse:
        """Processes a request using the OpenAI API."""
        if not self._client:
            await self.initialize()

        api_request = self._prepare_api_request(request)
        try:
            response = await self._client.post("/chat/completions", json=api_request)
            response.raise_for_status()
            return self._parse_response(response.json(), request)
        except httpx.HTTPStatusError as e:
            raise LLMAPIError(f"OpenAI API error: {e.response.text}", provider=self.provider_name, original_error=e) from e
        except httpx.RequestError as e:
            raise LLMAPIError(f"Request to OpenAI failed: {e}", provider=self.provider_name, original_error=e) from e

    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """Processes a request as a stream using the OpenAI API."""
        if not self._client:
            await self.initialize()

        api_request = self._prepare_api_request(request)
        api_request["stream"] = True

        try:
            async with self._client.stream("POST", "/chat/completions", json=api_request) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[len("data: ") :].strip()
                        if data == "[DONE]":
                            break
                        if data:
                            chunk = json.loads(data)
                            if chunk["choices"] and "content" in chunk["choices"][0].get("delta", {}):
                                content = chunk["choices"][0]["delta"]["content"]
                                if content:
                                    yield LLMResponse(content=content)
        except httpx.HTTPStatusError as e:
            raise LLMAPIError(f"OpenAI API streaming error: {e.response.text}", provider=self.provider_name, original_error=e) from e
        except httpx.RequestError as e:
            raise LLMAPIError(f"Streaming request to OpenAI failed: {e}", provider=self.provider_name, original_error=e) from e

    async def get_capabilities(self) -> LLMCapabilities:
        """Returns the static capabilities of the OpenAI provider."""
        return LLMCapabilities(
            supported_capabilities=[
                LLMCapability.TEXT_GENERATION,
                LLMCapability.CHAT_COMPLETION,
                LLMCapability.STREAMING,
                LLMCapability.FUNCTION_CALLING,
            ],
            max_context_length=128000,
            max_output_tokens=4096,
        )

    async def validate_request(self, request: LLMRequest) -> None:
        """Validates a request before sending it to the provider."""
        if not request.messages:
            raise LLMError("Request must contain at least one message.")

    async def health_check(self) -> Dict[str, Any]:
        """Performs a health check on the OpenAI provider."""
        try:
            await self.process(LLMRequest(content="Health check", max_tokens=1))
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
