"""
LLM Base Interfaces and Models

This module defines the base interfaces, abstract classes, and data models for
interacting with Large Language Models (LLMs) in the TraceRail Core SDK.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncGenerator

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

# --- Enums and Pydantic Models ---


class LLMCapability(Enum):
    """Enumeration of capabilities an LLM provider might have."""
    TEXT_GENERATION = "text_generation"
    CHAT_COMPLETION = "chat_completion"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    EMBEDDINGS = "embeddings"


class LLMUsage(BaseModel):
    """Data class for tracking token usage in an LLM interaction."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: Optional[float] = None

    @model_validator(mode="after")
    def calculate_total_tokens(self) -> "LLMUsage":
        """Calculate total_tokens if not provided."""
        if self.total_tokens == 0 and self.prompt_tokens > 0 and self.completion_tokens > 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        return self


class LLMCapabilities(BaseModel):
    """Describes the capabilities of an LLM provider."""

    supported_capabilities: List[LLMCapability] = Field(default_factory=list)
    max_context_length: Optional[int] = None
    max_output_tokens: Optional[int] = None
    requests_per_minute: Optional[int] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    provider_info: Dict[str, Any] = Field(default_factory=dict)

    def supports_streaming(self) -> bool:
        """Check if the provider supports streaming responses."""
        return LLMCapability.STREAMING in self.supported_capabilities

    def supports_function_calling(self) -> bool:
        """Check if the provider supports function calling."""
        return LLMCapability.FUNCTION_CALLING in self.supported_capabilities


class LLMMessage(BaseModel):
    """Represents a single message in a conversation history."""

    role: str  # e.g., "user", "assistant", "system"
    content: str

    def to_dict(self) -> Dict[str, str]:
        """Serializes the message to a dictionary."""
        return self.model_dump()


# --- Core Request and Response Models ---


class LLMRequest(BaseModel):
    """Encapsulates a request to be sent to an LLM provider."""

    content: Optional[str] = None  # The primary content for simple requests
    messages: List[LLMMessage] = Field(default_factory=list)
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context: Dict[str, Any] = Field(
        default_factory=dict
    )  # For additional context like system prompts

    @model_validator(mode="after")
    def ensure_content_or_messages(self) -> "LLMRequest":
        """Ensure either content or messages are provided."""
        if self.content and not self.messages:
            self.messages.append(LLMMessage(role="user", content=self.content))
        if not self.content and not self.messages:
            raise ValueError("Either 'content' or 'messages' must be provided.")
        return self


class LLMResponse(BaseModel):
    """Encapsulates a response received from an LLM provider."""

    content: str
    model: Optional[str] = None
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None
    response_time_ms: Optional[float] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the response to a dictionary."""
        return self.model_dump(mode="json")


# --- Abstract Base Class for Providers ---


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers in TraceRail.
    """

    def __init__(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ):
        """
        Initializes the base provider.

        Args:
            provider_name: The unique name of the provider.
            api_key: The API key for authentication.
            base_url: The base URL of the provider's API.
            timeout: Default request timeout in seconds.
            max_retries: Default number of retries for failed requests.
            retry_delay: Default delay between retries.
            **kwargs: Additional configuration parameters.
        """
        self.provider_name = provider_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.config = kwargs
        self._client: Optional[Any] = None  # To be initialized by subclasses
        logger.info(f"BaseLLMProvider '{self.provider_name}' instance created.")

    @abstractmethod
    async def initialize(self) -> None:
        """
        Performs any necessary setup for the provider, such as initializing
        an HTTP client. This should be called before making any API requests.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Cleans up any resources used by the provider, such as closing HTTP
        client sessions.
        """
        pass

    @abstractmethod
    async def process(self, request: LLMRequest) -> LLMResponse:
        """
        Processes a single, non-streaming request to the LLM.

        Args:
            request: The LLMRequest object containing the prompt and parameters.

        Returns:
            An LLMResponse object with the full response from the model.
        """
        pass

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """
        Processes a request to the LLM and streams the response.

        Args:
            request: The LLMRequest object.

        Yields:
            LLMResponse objects, each containing a chunk of the response content.
        """
        # This is a generator, so the implementation should use `yield`.
        # We need this to satisfy the linter, as an abstract async generator is tricky.
        if False:
            yield

    @abstractmethod
    async def get_capabilities(self) -> LLMCapabilities:
        """
        Returns the capabilities of the provider, such as supported models,
        max context length, etc.
        """
        pass

    @abstractmethod
    async def validate_request(self, request: LLMRequest) -> None:
        """
        Validates an LLMRequest to ensure it meets the provider's requirements
        before it is sent. Raises an LLMError on failure.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Performs a health check on the provider's API.

        Returns:
            A dictionary with health status and details.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(provider_name='{self.provider_name}')>"
