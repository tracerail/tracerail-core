"""
TraceRail Configuration

This module defines the configuration models for the TraceRail Core SDK using
Pydantic's settings management. It allows for hierarchical configuration
loaded from environment variables, providing a robust and type-safe way to
configure the application.
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field, SecretStr, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Enums for Configuration Choices ---


class LLMProvider(str, Enum):
    """Enumeration of supported LLM providers."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class RoutingEngine(str, Enum):
    """Enumeration of supported routing engines."""
    RULES = "rules"
    STATIC = "static"


class TaskManagerType(str, Enum):
    """Enumeration of supported task managers."""
    MEMORY = "memory"
    DATABASE = "database"
    TEMPORAL = "temporal"


# --- Leaf Configuration Models ---
# These models inherit from BaseSettings and are configured to ignore extra
# fields that might be passed down from the parent configuration's environment
# variable parsing.


class LLMConfig(BaseSettings):
    """Configuration for LLM providers."""
    model_config = SettingsConfigDict(extra='ignore')

    provider: LLMProvider = LLMProvider.DEEPSEEK
    # This field specifically looks for non-prefixed keys, which is useful for
    # picking up credentials from standard shell environments.
    api_key: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices(
            "DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY"
        ),
    )
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    provider_config: Dict[str, Any] = Field(default_factory=dict)


class RoutingConfig(BaseSettings):
    """Configuration for the routing engine."""
    model_config = SettingsConfigDict(extra='ignore')

    engine_type: RoutingEngine = RoutingEngine.RULES
    confidence_threshold: float = 0.8
    fallback_to_human: bool = True
    engine_config: Dict[str, Any] = Field(default_factory=dict)


class TaskConfig(BaseSettings):
    """Configuration for the task management system."""
    model_config = SettingsConfigDict(extra='ignore')

    enabled: bool = True
    manager_type: TaskManagerType = TaskManagerType.MEMORY
    default_sla_hours: int = 24
    assignment_strategy: str = "round_robin"
    manager_config: Dict[str, Any] = Field(default_factory=dict)
    assignment_config: Dict[str, Any] = Field(default_factory=dict)
    sla_manager: str = "basic"
    sla_config: Dict[str, Any] = Field(default_factory=dict)
    escalation_policy: str = "basic"
    escalation_config: Dict[str, Any] = Field(default_factory=dict)
    notification_service: str = "basic"
    notification_config: Dict[str, Any] = Field(default_factory=dict)


class TemporalConfig(BaseSettings):
    """Configuration for the Temporal client."""
    model_config = SettingsConfigDict(extra='ignore')

    host: str = "localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "tracerail-task-queue"


# --- Root Configuration Model ---


class TraceRailConfig(BaseSettings):
    """
    Main configuration for the TraceRail client.
    This model composes all other configuration models and enables nested
    environment variable loading.
    """
    # These fields will be populated by Pydantic using nested environment variables.
    # For example, `TRACERAIL_LLM__PROVIDER` will map to `config.llm.provider`.
    llm: LLMConfig = Field(default_factory=LLMConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    tasks: TaskConfig = Field(default_factory=TaskConfig)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)

    # Configure Pydantic to look for environment variables with a specific prefix
    # and use "__" as the delimiter for nested models.
    model_config = SettingsConfigDict(
        env_prefix="TRACERAIL_",
        env_nested_delimiter="__",
        extra='ignore',
        protected_namespaces=(),
    )
