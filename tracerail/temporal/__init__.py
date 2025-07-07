"""
TraceRail Temporal Integration Module

This package provides the core components for building and running TraceRail
workflows on the Temporal platform. It includes base classes for workflows,
activity definitions, and utilities for interacting with the Temporal client.

The primary entry point for developers is the `BaseAIWorkflow`, which provides
a structured way to define complex, stateful, and resilient AI processes.
"""

# Import key components for public API
from .workflows import BaseAIWorkflow
from .activities import (
    llm_activity,
    routing_activity,
    create_task_activity,
    notify_activity,
)
from .exceptions import (
    TemporalWorkflowError,
    ActivityError,
    WorkflowConfigurationError,
)
from .client import get_temporal_client, start_workflow

__all__ = [
    # Workflows
    "BaseAIWorkflow",
    # Activities
    "llm_activity",
    "routing_activity",
    "create_task_activity",
    "notify_activity",
    # Exceptions
    "TemporalWorkflowError",
    "ActivityError",
    "WorkflowConfigurationError",
    # Client Utilities
    "get_temporal_client",
    "start_workflow",
]
