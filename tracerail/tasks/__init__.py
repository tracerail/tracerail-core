"""
TraceRail Task Management Module

This package contains all components related to task management for human-in-the-loop
workflows. It includes data models for tasks, base interfaces for task managers
and strategies, and factory functions for creating task management components.
"""

# Import key data models for easier access
from .models import (
    TaskData,
    TaskResult,
    TaskStatus,
    TaskPriority,
    TaskComment,
    TaskAttachment,
)

# Import base classes for extension
from .base import (
    BaseTaskManager,
    BaseAssignmentStrategy,
    BaseSLAManager,
    BaseEscalationPolicy,
    BaseNotificationService,
)

# Import factory functions for creating instances
from .factory import (
    create_task_manager,
    create_assignment_strategy,
    create_sla_manager,
    create_escalation_policy,
    create_notification_service,
)

# Import exceptions for clear error handling
from .exceptions import (
    TaskError,
    TaskConfigurationError,
    TaskNotFoundError,
    DuplicateTaskError,
    TaskAssignmentError,
)

__all__ = [
    # --- Models ---
    "TaskData",
    "TaskResult",
    "TaskStatus",
    "TaskPriority",
    "TaskComment",
    "TaskAttachment",

    # --- Base Classes ---
    "BaseTaskManager",
    "BaseAssignmentStrategy",
    "BaseSLAManager",
    "BaseEscalationPolicy",
    "BaseNotificationService",

    # --- Factory Functions ---
    "create_task_manager",
    "create_assignment_strategy",
    "create_sla_manager",
    "create_escalation_policy",
    "create_notification_service",

    # --- Exceptions ---
    "TaskError",
    "TaskConfigurationError",
    "TaskNotFoundError",
    "DuplicateTaskError",
    "TaskAssignmentError",
]
