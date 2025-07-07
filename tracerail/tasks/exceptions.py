"""
TraceRail Task Management Exceptions

This module defines the custom exception hierarchy for errors related to
task management in the TraceRail Core SDK.
"""

from typing import Any, Optional

# Import the base exception and configuration error from the main exceptions module
from ..exceptions import TraceRailException, ConfigurationError


class TaskError(TraceRailException):
    """
    Base exception for all errors related to task management.
    """
    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes the task error.

        Args:
            message: The human-readable error message.
            task_id: The ID of the task involved, if applicable.
            **kwargs: Additional details.
        """
        details = {"task_id": task_id, **kwargs}
        super().__init__(message, details)
        self.task_id = task_id


class TaskConfigurationError(ConfigurationError, TaskError):
    """
    Raised for errors in the configuration of a task manager or its components.
    """
    pass


class TaskNotFoundError(TaskError):
    """
    Raised when an operation is attempted on a task that does not exist.
    """
    pass


class DuplicateTaskError(TaskError):
    """
    Raised when attempting to create a task with an ID that already exists.
    """
    pass


class TaskAssignmentError(TaskError):
    """Raised when a task cannot be assigned."""
    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        assignee: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes the task assignment error.

        Args:
            message: The human-readable error message.
            task_id: The ID of the task that failed to be assigned.
            assignee: The intended assignee, if any.
            **kwargs: Additional details.
        """
        super().__init__(message, task_id=task_id, assignee=assignee, **kwargs)
        self.assignee = assignee
