"""
Test cases for the LLM factory module, using pydantic-settings.
"""

import pytest
from pydantic import ValidationError

# Import the config models and the factory function we are testing
from tracerail.config import TraceRailConfig
from tracerail.llm.factory import create_llm_provider
from tracerail.llm.exceptions import LLMConfigurationError

# Import the provider classes to check the type of the created provider
from tracerail.llm.providers.anthropic import AnthropicProvider
from tracerail.llm.providers.azure_openai import AzureOpenAIProvider
from tracerail.llm.providers.deepseek import DeepSeekProvider
from tracerail.llm.providers.openai import OpenAIProvider


class TestLLMFactory:
    """
    Test suite for the LLM factory functions.

    These tests validate that the factory can create the correct provider
    based on a configuration that is loaded from environment variables.
    """

    @pytest.mark.asyncio
    async def test_create_openai_provider(self, monkeypatch):
        """
        Tests creating an OpenAI provider by setting environment variables.
        """
        # Arrange: Set env vars for the config to load
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")

        # Act: Instantiate config from env and create provider
        config = TraceRailConfig()
        provider = await create_llm_provider(config.llm)

        # Assert
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test_key"

    @pytest.mark.asyncio
    async def test_create_anthropic_provider(self, monkeypatch):
        """
        Tests creating an Anthropic provider by setting environment variables.
        """
        # Arrange
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

        # Act
        config = TraceRailConfig()
        provider = await create_llm_provider(config.llm)

        # Assert
        assert isinstance(provider, AnthropicProvider)

    @pytest.mark.asyncio
    async def test_create_azure_openai_provider(self, monkeypatch):
        """
        Tests creating an Azure OpenAI provider by setting environment variables.
        """
        # Arrange
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "azure_openai")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test_key")
        # Azure provider also requires base_url and model, which are not aliased
        # and must be loaded using the nested env var syntax.
        monkeypatch.setenv("TRACERAIL_LLM__BASE_URL", "https://example.openai.azure.com")
        monkeypatch.setenv("TRACERAIL_LLM__MODEL", "my-deployment")

        # Act
        # Instantiate the main config object to test nested loading
        config = TraceRailConfig()
        provider = await create_llm_provider(config.llm)

        # Assert
        assert isinstance(provider, AzureOpenAIProvider)
        assert provider.deployment_name == "my-deployment"

    @pytest.mark.asyncio
    async def test_create_deepseek_provider(self, monkeypatch):
        """
        Tests creating a DeepSeek provider by setting environment variables.
        """
        # Arrange
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "deepseek")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")

        # Act
        config = TraceRailConfig()
        provider = await create_llm_provider(config.llm)

        # Assert
        assert isinstance(provider, DeepSeekProvider)

    def test_create_unsupported_provider_from_env(self, monkeypatch):
        """
        Tests that creating a config with an unsupported provider from the
        environment raises a Pydantic ValidationError.
        """
        # Arrange
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "unsupported_provider")

        # Act & Assert
        with pytest.raises(ValidationError):
            TraceRailConfig()

    @pytest.mark.asyncio
    async def test_create_with_missing_api_key(self, monkeypatch):
        """
        Tests creating a provider when the required API key is not in the environment.
        """
        # Arrange: Ensure the provider is set but the corresponding key is not.
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "openai")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Act
        config = TraceRailConfig()

        # Assert: The provider's `initialize` method should fail, and the
        # factory should wrap this in a specific configuration error.
        with pytest.raises(LLMConfigurationError, match="API key is required"):
            await create_llm_provider(config.llm)
