"""
TraceRail Core Exceptions

This module defines the custom exception hierarchy for the TraceRail library.
It establishes a common base exception, `TraceRailException`, and specialized
exceptions for different submodules like configuration, LLM, routing, and tasks.
"""
from typing import Any, Dict, Optional


class TraceRailException(Exception):
    """
    Base exception for all errors raised by the TraceRail library.

    This class provides a consistent structure for error handling, including
    a message and an optional dictionary for detailed context.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the exception to a dictionary for logging or API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self):
        """Provides a user-friendly string representation of the exception."""
        return f"{self.__class__.__name__}: {self.message}"


# Alias for backward compatibility or more general error catching.
TraceRailError = TraceRailException


class ErrorCode:
    """Standard error codes for routing and other operations."""
    ROUTING_ERROR = "ROUTING_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# --- Category-Specific Base Exceptions ---

class ConfigurationError(TraceRailException):
    """Base class for all configuration-related errors."""
    pass


class LLMError(TraceRailException):
    """Base class for all LLM-related errors."""
    pass


class RoutingError(TraceRailException):
    """Base class for all routing-related errors."""
    pass


class TaskError(TraceRailException):
    """Base class for all task management errors."""
    pass

# --- More Specific Exception Types ---

# These could be further specialized in their respective submodule `exceptions.py` files
# if needed, but defining them here provides a central registry.

class RuleExecutionError(RoutingError):
    """Raised when a routing rule fails during execution."""
    def __init__(self, message: str, rule_name: str, **kwargs):
        super().__init__(message, details={"rule_name": rule_name, **kwargs})
        self.rule_name = rule_name


class TaskNotFoundError(TaskError):
    """Raised when a specified task cannot be found."""
    pass


class DuplicateTaskError(TaskError):
    """Raised when attempting to create a task with an ID that already exists."""
    pass


class TaskAssignmentError(TaskError):
    """Raised when a task cannot be assigned."""
    pass
