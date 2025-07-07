"""
Anthropic LLM Provider Implementation
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
    LLMMessage,
)
from ..exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMError,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    An implementation of the LLMProvider interface for Anthropic's models (Claude).
    """

    def __init__(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ):
        """
        Initializes the Anthropic provider.

        Args:
            provider_name: The name of the provider.
            api_key: The Anthropic API key.
            base_url: The base URL for the Anthropic API.
            model: The default model to use (e.g., "claude-3-opus-20240229").
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
            base_url=base_url or "https://api.anthropic.com/v1",
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs,
        )
        self.model = model or "claude-3-opus-20240229"
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Anthropic API requires this version header
        self.anthropic_version = "2023-06-01"

    async def initialize(self) -> None:
        """Initializes the httpx client for making API requests."""
        if not self.api_key:
            raise LLMAuthenticationError(
                f"API key is required for {self.provider_name}",
                provider=self.provider_name,
            )
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
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
        """Prepares the request payload for the Anthropic API."""
        # Separate system prompt from messages if present
        messages = [msg.to_dict() for msg in request.messages]
        system_prompt = request.context.get("system_prompt")

        payload = {
            "model": request.model or self.model,
            "messages": messages,
            "max_tokens": request.max_tokens or self.max_tokens,
            "temperature": request.temperature or self.temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        return payload

    def _parse_response(self, data: Dict[str, Any], request: LLMRequest) -> LLMResponse:
        """Parses a successful response from the Anthropic API."""
        content = ""
        if data.get("content"):
            content = data["content"][0]["text"]

        usage_data = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=data.get("model", self.model),
            usage=LLMUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
            ),
            request_id=request.request_id,
            finish_reason=data.get("stop_reason"),
        )

    async def process(self, request: LLMRequest) -> LLMResponse:
        """Processes a request using the Anthropic API."""
        if not self._client:
            await self.initialize()

        api_request = self._prepare_api_request(request)
        try:
            response = await self._client.post("/messages", json=api_request)
            response.raise_for_status()
            return self._parse_response(response.json(), request)
        except httpx.HTTPStatusError as e:
            raise LLMAPIError(f"Anthropic API error: {e.response.text}", provider=self.provider_name, original_error=e) from e
        except httpx.RequestError as e:
            raise LLMAPIError(f"Request to Anthropic failed: {e}", provider=self.provider_name, original_error=e) from e

    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """Processes a request as a stream using the Anthropic API."""
        if not self._client:
            await self.initialize()

        api_request = self._prepare_api_request(request)
        api_request["stream"] = True

        try:
            async with self._client.stream("POST", "/messages", json=api_request) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[len("data: ") :].strip()
                        if data:
                            chunk = json.loads(data)
                            if chunk.get("type") == "content_block_delta" and chunk["delta"]["type"] == "text_delta":
                                yield LLMResponse(content=chunk["delta"]["text"])
        except httpx.HTTPStatusError as e:
            raise LLMAPIError(f"Anthropic API streaming error: {e.response.text}", provider=self.provider_name, original_error=e) from e
        except httpx.RequestError as e:
            raise LLMAPIError(f"Streaming request to Anthropic failed: {e}", provider=self.provider_name, original_error=e) from e

    async def get_capabilities(self) -> LLMCapabilities:
        """Returns the static capabilities of the Anthropic provider."""
        return LLMCapabilities(
            supported_capabilities=[
                LLMCapability.TEXT_GENERATION,
                LLMCapability.CHAT_COMPLETION,
                LLMCapability.STREAMING,
            ],
            max_context_length=200000,
            max_output_tokens=4096,
        )

    async def validate_request(self, request: LLMRequest) -> None:
        """Validates a request before sending it to the provider."""
        if not request.messages:
            raise LLMError("Request must contain at least one message.")

    async def health_check(self) -> Dict[str, Any]:
        """Performs a health check on the Anthropic provider."""
        try:
            # A simple ping-like request
            await self._client.post("/messages", json={
                "model": self.model,
                "messages": [{"role": "user", "content": "Health check"}],
                "max_tokens": 1
            })
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
