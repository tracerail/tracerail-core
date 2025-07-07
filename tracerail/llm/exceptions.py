"""
LLM-specific Exceptions for TraceRail Core.

This module defines the custom exception hierarchy for errors related to
Large Language Model (LLM) interactions.
"""

from typing import Any, Dict, Optional

# Assuming a base exception structure exists in the parent package.
# The `..` indicates a relative import from the parent directory.
from ..exceptions import TraceRailException, ConfigurationError


class LLMError(TraceRailException):
    """Base class for all LLM-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
        **kwargs: Any,
    ):
        """
        Initializes the LLM error.

        Args:
            message: The human-readable error message.
            provider: The name of the LLM provider that caused the error.
            original_error: The original exception, if any, for debugging.
            **kwargs: Additional details to include with the exception.
        """
        details = {"provider": provider, **kwargs}
        if original_error:
            # Include the string representation of the original error for context
            details["original_error"] = f"{type(original_error).__name__}: {original_error}"
        super().__init__(message, details)
        self.provider = provider
        self.original_error = original_error


class LLMConfigurationError(ConfigurationError, LLMError):
    """Raised for errors in an LLM provider's configuration."""
    pass


class LLMAPIError(LLMError):
    """Raised for general or unexpected API errors from the LLM provider."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when an API key or other authentication mechanism fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider's rate limit has been exceeded."""

    def __init__(
        self,
        message: str,
        provider: str,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Initializes the rate limit error.

        Args:
            message: The error message.
            provider: The name of the LLM provider.
            retry_after: The suggested number of seconds to wait before retrying.
            **kwargs: Additional details.
        """
        super().__init__(message, provider=provider, retry_after=retry_after, **kwargs)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Raised when a request to the LLM provider times out."""
    pass


class LLMModelNotFoundError(LLMError):
    """Raised when the requested model is not available at the provider."""
    pass


class LLMContentFilterError(LLMError):
    """Raised when content is blocked or filtered by the provider's safety systems."""
    pass


class UnsupportedProviderError(LLMError):
    """Raised when an unsupported LLM provider is requested."""
    pass
