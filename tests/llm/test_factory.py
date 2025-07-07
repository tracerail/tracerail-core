"""Test cases for the LLM factory module."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch

from tracerail.config import LLMConfig, LLMProvider
from tracerail.llm.exceptions import LLMConfigurationError
from tracerail.llm.factory import create_llm_provider
from tracerail.llm.providers.anthropic import AnthropicProvider
from tracerail.llm.providers.azure_openai import AzureOpenAIProvider
from tracerail.llm.providers.deepseek import DeepSeekProvider
from tracerail.llm.providers.openai import OpenAIProvider


class TestLLMFactory:
    """Test suite for the LLM factory functions."""

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"})
    async def test_create_openai_provider(self):
        """Test creating an OpenAI provider."""
        config = LLMConfig(provider=LLMProvider.OPENAI, api_key="test_key")
        provider = await create_llm_provider(config)
        assert isinstance(provider, OpenAIProvider)

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test_key"})
    async def test_create_anthropic_provider(self):
        """Test creating an Anthropic provider."""
        config = LLMConfig(provider=LLMProvider.ANTHROPIC, api_key="test_key")
        provider = await create_llm_provider(config)
        assert isinstance(provider, AnthropicProvider)

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"AZURE_OPENAI_API_KEY": "test_key"})
    async def test_create_azure_openai_provider(self):
        """Test creating an Azure OpenAI provider."""
        # Azure provider requires base_url and a model (deployment name)
        config = LLMConfig(
            provider=LLMProvider.AZURE_OPENAI,
            api_key="test_key",
            base_url="https://example.openai.azure.com",
            model="my-deployment",
        )
        provider = await create_llm_provider(config)
        assert isinstance(provider, AzureOpenAIProvider)

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test_key"})
    async def test_create_deepseek_provider(self):
        """Test creating a DeepSeek provider."""
        config = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="test_key")
        provider = await create_llm_provider(config)
        assert isinstance(provider, DeepSeekProvider)

    def test_create_unsupported_provider(self):
        """Test that creating a config with an unsupported provider raises a validation error."""
        with pytest.raises(ValidationError):
            LLMConfig(provider="unsupported_provider")

    @pytest.mark.asyncio
    async def test_create_with_missing_api_key(self, monkeypatch):
        """Test creating a provider with a missing API key raises a configuration error."""
        # Ensure the environment variable is not set for this test
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Configure the provider to use OpenAI but explicitly provide no API key.
        # The provider's `initialize` method should fail, and the factory should wrap the error.
        config = LLMConfig(provider=LLMProvider.OPENAI, api_key=None)

        with pytest.raises(LLMConfigurationError, match="API key is required"):
            await create_llm_provider(config)
