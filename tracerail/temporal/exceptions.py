"""
TraceRail Temporal Integration Exceptions

This module defines the custom exception hierarchy for errors related to
Temporal workflows, activities, and client interactions within the TraceRail SDK.
"""

from typing import Optional

# Import the base exception and configuration error from the main exceptions module
from ..exceptions import TraceRailException, ConfigurationError


class TemporalWorkflowError(TraceRailException):
    """
    Base exception for all errors related to Temporal workflows and activities.
    """
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initializes the Temporal workflow error.

        Args:
            message: The human-readable error message.
            workflow_id: The ID of the workflow where the error occurred.
            run_id: The run ID of the workflow execution.
            **kwargs: Additional details.
        """
        details = {"workflow_id": workflow_id, "run_id": run_id, **kwargs}
        super().__init__(message, details)
        self.workflow_id = workflow_id
        self.run_id = run_id


class ActivityError(TemporalWorkflowError):
    """
    Raised when a Temporal activity fails during execution.
    """
    def __init__(
        self,
        message: str,
        activity_name: Optional[str] = None,
        **kwargs,
    ):
        """
        Initializes the activity error.

        Args:
            message: The human-readable error message.
            activity_name: The name of the activity that failed.
            **kwargs: Additional details inherited from TemporalWorkflowError.
        """
        super().__init__(message, activity_name=activity_name, **kwargs)
        self.activity_name = activity_name


class WorkflowConfigurationError(ConfigurationError, TemporalWorkflowError):
    """
    Raised for errors in configuring a Temporal client, workflow, or worker.

    This inherits from both ConfigurationError and TemporalWorkflowError to indicate
    it's a configuration issue within the Temporal integration context.
    """
    pass
