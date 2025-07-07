"""
TraceRail LLM Provider Factory

This module provides factory functions for creating LLM provider instances.
It handles provider instantiation, configuration, and initialization.
"""
import logging
from typing import Any, Dict, List, Optional, Type

from ..config import LLMConfig, LLMProvider as LLMProviderEnum
from .exceptions import LLMConfigurationError
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMProviderRegistry:
    """Registry for LLM provider implementations."""

    def __init__(self):
        self._providers: Dict[str, Type[BaseLLMProvider]] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, name: str, provider_class: Type[BaseLLMProvider], aliases: Optional[List[str]] = None):
        """
        Register a provider implementation.

        Args:
            name: Provider name.
            provider_class: The class of the provider.
            aliases: A list of alternative names for the provider.
        """
        if name in self._providers:
            logger.warning(f"Provider '{name}' is already registered and will be overridden.")
        self._providers[name] = provider_class

        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
        logger.debug(f"Registered LLM provider: {name}")

    def get_provider_class(self, name: str) -> Type[BaseLLMProvider]:
        """
        Get a provider class by its registered name or alias.

        Args:
            name: The name or alias of the provider.

        Returns:
            The provider class if found.

        Raises:
            LLMConfigurationError: If the provider is not registered.
        """
        resolved_name = self._aliases.get(name, name)
        provider_class = self._providers.get(resolved_name)

        if not provider_class:
            available = list(self._providers.keys())
            raise LLMConfigurationError(
                f"Unknown LLM provider: '{name}'. Available providers: {available}",
                provider=name,
            )
        return provider_class


_provider_registry = LLMProviderRegistry()


def register_provider(name: str, provider_class: Type[BaseLLMProvider], aliases: Optional[List[str]] = None):
    """Registers a provider with the global registry."""
    _provider_registry.register(name, provider_class, aliases)


def _register_builtin_providers():
    """Dynamically registers the built-in LLM providers."""
    try:
        from .providers.deepseek import DeepSeekProvider
        register_provider(LLMProviderEnum.DEEPSEEK.value, DeepSeekProvider, aliases=["deepseek-chat"])
    except ImportError:
        logger.debug("DeepSeek provider not available. Please install necessary dependencies.")
    try:
        from .providers.openai import OpenAIProvider
        register_provider(LLMProviderEnum.OPENAI.value, OpenAIProvider, aliases=["gpt", "chatgpt"])
    except ImportError:
        logger.debug("OpenAI provider not available. Please install necessary dependencies.")
    try:
        from .providers.anthropic import AnthropicProvider
        register_provider(LLMProviderEnum.ANTHROPIC.value, AnthropicProvider, aliases=["claude"])
    except ImportError:
        logger.debug("Anthropic provider not available. Please install necessary dependencies.")
    try:
        from .providers.azure_openai import AzureOpenAIProvider
        register_provider(LLMProviderEnum.AZURE_OPENAI.value, AzureOpenAIProvider, aliases=["azure"])
    except ImportError:
        logger.debug("Azure OpenAI provider not available. Please install necessary dependencies.")

_register_builtin_providers()


async def create_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """
    Creates and initializes an LLM provider instance from configuration.

    Args:
        config: The LLM configuration object.

    Returns:
        An initialized LLM provider instance.

    Raises:
        LLMConfigurationError: If the provider cannot be created or initialized.
    """
    provider_name = config.provider.value
    logger.info(f"Creating LLM provider of type: {provider_name}")

    try:
        provider_class = _provider_registry.get_provider_class(provider_name)

        init_kwargs = {
            "api_key": config.api_key.get_secret_value() if config.api_key else None,
            "base_url": config.base_url,
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
            "retry_delay": config.retry_delay,
            **config.provider_config,
        }

        # Filter out None values to avoid overriding defaults in provider's __init__
        filtered_kwargs = {k: v for k, v in init_kwargs.items() if v is not None}

        provider = provider_class(provider_name=provider_name, **filtered_kwargs)

        await provider.initialize()
        logger.info(f"LLM provider '{provider_name}' initialized successfully.")
        return provider

    except Exception as e:
        logger.error(f"Failed to create LLM provider '{provider_name}': {e}", exc_info=True)
        # Wrap the exception in our custom error type for consistency, but don't re-wrap.
        if isinstance(e, LLMConfigurationError):
             raise e
        raise LLMConfigurationError(
            f"Failed to create '{provider_name}' provider: {e}",
            provider=provider_name,
            original_error=e,
        ) from e


async def create_provider_from_dict(config_dict: Dict[str, Any]) -> BaseLLMProvider:
    """
    Creates an LLM provider from a dictionary configuration.

    Args:
        config_dict: A dictionary containing the LLM configuration.

    Returns:
        An initialized LLM provider instance.
    """
    try:
        llm_config = LLMConfig(**config_dict)
        return await create_llm_provider(llm_config)
    except Exception as e:
        raise LLMConfigurationError(f"Invalid configuration dictionary provided: {e}") from e


class LLMProviderPool:
    """A pool for managing multiple LLM providers for failover or load balancing."""

    def __init__(self, providers: Optional[List[BaseLLMProvider]] = None):
        self._providers = providers or []
        self._current_index = 0

    def add_provider(self, provider: BaseLLMProvider):
        """Adds a provider to the pool."""
        self._providers.append(provider)

    def get_next_provider(self) -> Optional[BaseLLMProvider]:
        """Gets the next provider in a round-robin fashion."""
        if not self._providers:
            return None
        provider = self._providers[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._providers)
        return provider

    async def close_all(self):
        """Closes all providers in the pool."""
        for provider in self._providers:
            try:
                await provider.close()
            except Exception as e:
                logger.error(f"Error closing provider {provider}: {e}", exc_info=True)

async def create_provider_pool(configs: List[LLMConfig]) -> LLMProviderPool:
    """
    Creates a pool of LLM providers from a list of configurations.

    Args:
        configs: A list of LLMConfig objects.

    Returns:
        An LLMProviderPool instance with initialized providers.
    """
    pool = LLMProviderPool()
    for config in configs:
        try:
            provider = await create_llm_provider(config)
            pool.add_provider(provider)
        except Exception as e:
            logger.error(f"Failed to create and add provider to pool from config: {config.provider.value}", exc_info=True)
    return pool
