"""
TraceRail Configuration

This module defines the configuration models for the TraceRail Core SDK using Pydantic.
It allows for configuration via environment variables, files, or direct instantiation.
"""
import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()


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


# --- Configuration Models ---

class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: LLMProvider = Field(
        default=LLMProvider.DEEPSEEK,
        description="The LLM provider to use.",
        json_schema_extra={"env": "TRACERAIL_LLM_PROVIDER"},
    )
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for the selected LLM provider.",
        json_schema_extra={
            "env": ["DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY"]
        },  # Pydantic will check these in order
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for the LLM provider API, for proxies or custom deployments."
    )
    model: Optional[str] = Field(
        default=None,
        description="The specific model to use (e.g., 'gpt-4-turbo')."
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Default temperature for LLM responses."
    )
    max_tokens: Optional[int] = Field(
        default=2048,
        description="Default maximum tokens for LLM responses."
    )
    timeout: int = Field(
        default=60,
        description="Request timeout in seconds."
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests."
    )
    retry_delay: float = Field(
        default=1.0,
        description="Initial delay between retries in seconds."
    )
    provider_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific configuration."
    )


class RoutingConfig(BaseModel):
    """Configuration for the routing engine."""
    engine_type: RoutingEngine = Field(
        default=RoutingEngine.RULES,
        description="The type of routing engine to use.",
        json_schema_extra={"env": "TRACERAIL_ROUTING_ENGINE"},
    )
    confidence_threshold: float = Field(
        default=0.8,
        description="Confidence score threshold for automatic processing."
    )
    fallback_to_human: bool = Field(
        default=True,
        description="Whether to fall back to human review if routing is uncertain."
    )
    engine_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional engine-specific configuration (e.g., rules file path)."
    )


class TaskConfig(BaseModel):
    """Configuration for the task management system."""
    enabled: bool = Field(
        default=True,
        description="Enable or disable the task management system.",
        json_schema_extra={"env": "TRACERAIL_TASKS_ENABLED"},
    )
    manager_type: TaskManagerType = Field(
        default=TaskManagerType.MEMORY,
        description="The type of task manager to use.",
        json_schema_extra={"env": "TRACERAIL_TASK_MANAGER_TYPE"},
    )
    default_sla_hours: int = Field(
        default=24,
        description="Default Service Level Agreement (SLA) in hours for tasks."
    )
    assignment_strategy: str = Field(
        default="round_robin",
        description="Default strategy for assigning tasks (e.g., 'round_robin', 'skill_based')."
    )
    # Sub-component configurations
    manager_config: Dict[str, Any] = Field(default_factory=dict)
    assignment_config: Dict[str, Any] = Field(default_factory=dict)
    sla_manager: str = Field(default="basic", description="The SLA manager to use.")
    sla_config: Dict[str, Any] = Field(default_factory=dict)
    escalation_policy: str = Field(default="basic", description="The escalation policy to use.")
    escalation_config: Dict[str, Any] = Field(default_factory=dict)
    notification_service: str = Field(default="basic", description="The notification service to use.")
    notification_config: Dict[str, Any] = Field(default_factory=dict)


class TemporalConfig(BaseModel):
    """Configuration for the Temporal client."""
    host: str = Field(
        default="localhost",
        description="The host for the Temporal service.",
        json_schema_extra={"env": "TEMPORAL_HOST"},
    )
    port: int = Field(
        default=7233,
        description="The port for the Temporal service.",
        json_schema_extra={"env": "TEMPORAL_PORT"},
    )
    namespace: str = Field(
        default="default",
        description="The Temporal namespace to use.",
        json_schema_extra={"env": "TEMPORAL_NAMESPACE"},
    )
    task_queue: str = Field(
        default="tracerail-task-queue",
        description="The default task queue for workflows.",
        json_schema_extra={"env": "TEMPORAL_TASK_QUEUE"},
    )


class TraceRailConfig(BaseModel):
    """
    Main configuration for the TraceRail client.
    This model composes all other configuration models.
    """
    llm: LLMConfig = Field(default_factory=LLMConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    tasks: TaskConfig = Field(default_factory=TaskConfig)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)

    model_config = ConfigDict(
        env_nested_delimiter="_",
        env_prefix="TRACERAIL_",
        protected_namespaces=(),
    )
