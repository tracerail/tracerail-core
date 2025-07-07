import pytest
from pydantic import SecretStr

from tracerail.config import LLMProvider, TraceRailConfig


class TestTraceRailConfig:
    """
    Unit tests for the Pydantic configuration models, using pydantic-settings.
    These tests verify that settings are correctly loaded from environment variables.
    """

    def test_default_config_instantiation(self):
        """
        Tests that the configuration can be instantiated with default values
        when no environment variables are set.
        """
        # Act
        config = TraceRailConfig()

        # Assert
        assert config is not None
        assert config.llm.provider == LLMProvider.DEEPSEEK
        assert config.temporal.host == "localhost"

    def test_nested_llm_provider_loading(self, monkeypatch):
        """
        Verifies that a nested LLM property is correctly loaded using the
        prefix and nested delimiter (e.g., TRACERAIL_LLM__PROVIDER).
        """
        # Arrange: Set the environment variable with the correct prefix and delimiter.
        monkeypatch.setenv("TRACERAIL_LLM__PROVIDER", "openai")

        # Act: Create the config instance. pydantic-settings should find the var.
        config = TraceRailConfig()

        # Assert: Check if the provider was overridden from its default.
        assert config.llm.provider == LLMProvider.OPENAI

    def test_api_key_loading_from_alias(self, monkeypatch):
        """
        Verifies that the LLM API key is correctly loaded from an aliased
        environment variable (one without the TRACERAIL_ prefix).
        """
        # Arrange
        dummy_key = "sk-dummy-key-for-testing"
        monkeypatch.setenv("DEEPSEEK_API_KEY", dummy_key)

        # Act
        config = TraceRailConfig()

        # Assert
        assert config.llm.api_key is not None
        assert isinstance(config.llm.api_key, SecretStr)
        assert config.llm.api_key.get_secret_value() == dummy_key

    def test_nested_temporal_config_loading(self, monkeypatch):
        """
        Tests another nested property to confirm the loading mechanism is robust.
        """
        # Arrange
        test_host = "test.temporal.host.io"
        # This uses the nested syntax because `host` in TemporalConfig does not
        # have its own `validation_alias` without a prefix.
        monkeypatch.setenv("TRACERAIL_TEMPORAL__HOST", test_host)

        # Act
        config = TraceRailConfig()

        # Assert
        assert config.temporal.host == test_host
        # Also check that a default value remains unchanged
        assert config.temporal.port == 7233

    def test_api_key_alias_priority(self, monkeypatch):
        """
        Verifies that Pydantic respects the order of AliasChoices, picking the
        first environment variable it finds in the list.
        """
        # Arrange: Set multiple possible keys.
        # In LLMConfig, DEEPSEEK_API_KEY is first in the list for api_key.
        openai_key = "sk-this-should-be-ignored"
        deepseek_key = "sk-this-should-be-chosen"
        monkeypatch.setenv("OPENAI_API_KEY", openai_key)
        monkeypatch.setenv("DEEPSEEK_API_KEY", deepseek_key)

        # Act
        config = TraceRailConfig()

        # Assert
        assert config.llm.api_key.get_secret_value() == deepseek_key
