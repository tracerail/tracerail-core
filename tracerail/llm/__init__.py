"""
TraceRail LLM Module

This package provides the interfaces, models, and factory functions for interacting
with various Large Language Model (LLM) providers.
"""

# Import key data models and base classes for easier access
from .base import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    LLMMessage,
    LLMUsage,
    LLMCapabilities,
    LLMCapability,
)

# Import key exceptions
from .exceptions import (
    LLMError,
    LLMConfigurationError,
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMModelNotFoundError,
    LLMContentFilterError,
    UnsupportedProviderError,
)

# Import factory functions
from .factory import create_llm_provider, create_provider_from_dict, LLMProviderPool

# Define a public alias for the base provider for simplicity
LLMProvider = BaseLLMProvider


__all__ = [
    # Base Classes and aliases
    "BaseLLMProvider",
    "LLMProvider",
    # Core Models
    "LLMRequest",
    "LLMResponse",
    "LLMMessage",
    "LLMUsage",
    "LLMCapabilities",
    "LLMCapability",
    # Factory Functions
    "create_llm_provider",
    "create_provider_from_dict",
    "LLMProviderPool",
    # Exceptions
    "LLMError",
    "LLMConfigurationError",
    "LLMAPIError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMModelNotFoundError",
    "LLMContentFilterError",
    "UnsupportedProviderError",
]
