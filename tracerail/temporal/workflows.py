"""
TraceRail Temporal Workflows

This module provides the base workflow class for building resilient and
stateful AI workflows with TraceRail and Temporal.
"""
import logging
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Optional, Dict

from temporalio import workflow
from temporalio.exceptions import ActivityError as TemporalActivityError

# Import activities with a clear alias to avoid name clashes
from . import activities as tracerail_activities
from .exceptions import ActivityError

# Import core TraceRail models
from ..config import TraceRailConfig
from ..llm import LLMRequest, LLMResponse
from ..routing import RoutingContext, RoutingResult
from ..tasks import TaskData, TaskResult
from ..tasks.notification import Notification

# It's recommended to type the activity stubs for better static analysis
# and editor support.
with workflow.unsafe.imports_passed_through():
    from .activities import (
        llm_activity,
        routing_activity,
        create_task_activity,
        notify_activity,
    )


logger = logging.getLogger(__name__)


@workflow.defn
class BaseAIWorkflow(ABC):
    """
    An abstract base class for creating stateful, long-running AI workflows.

    This class provides a structured framework and helper methods to orchestrate
    LLM calls, routing logic, and human-in-the-loop task management using
    Temporal activities.
    """

    def __init__(self, config: TraceRailConfig):
        """
        Initializes the base workflow with the given configuration.

        Args:
            config: The main TraceRail configuration object.
        """
        self._config = config
        self._config_dict = config.model_dump()  # Serialize config for activities

    @workflow.run
    @abstractmethod
    async def run(self, input_data: Any) -> Any:
        """
        The main entry point for the workflow's execution logic.

        This method must be implemented by subclasses to define the specific
        steps and logic of the AI process.

        Args:
            input_data: The initial data required to start the workflow.

        Returns:
            The final result of the workflow execution.
        """
        pass

    def _get_activity_options(self, timeout_seconds: int = 60) -> Dict[str, Any]:
        """Returns default options for executing activities."""
        return {
            "start_to_close_timeout": timedelta(seconds=timeout_seconds),
            # Example retry policy: retry on non-application errors
            "retry_policy": {
                "initial_interval": timedelta(seconds=2),
                "backoff_coefficient": 2.0,
                "maximum_interval": timedelta(seconds=100),
                "non_retryable_error_types": ["ApplicationError"],
            },
        }

    async def process_with_llm(self, request: LLMRequest) -> LLMResponse:
        """
        Executes the LLM activity to process a request.

        Args:
            request: The LLMRequest to be sent to the provider.

        Returns:
            The LLMResponse from the provider.
        """
        workflow.logger.info(f"Executing LLM activity for request ID: {request.request_id}")
        try:
            return await workflow.execute_activity(
                llm_activity,
                arg=request,
                **self._get_activity_options(timeout_seconds=self._config.llm.timeout),
            )
        except TemporalActivityError as e:
            workflow.logger.error(f"LLM activity failed: {e}")
            raise ActivityError(f"LLM processing failed: {e.cause}", activity_name="llm_activity") from e

    async def get_routing_decision(self, context: RoutingContext) -> RoutingResult:
        """
        Executes the routing activity to get a routing decision.

        Args:
            context: The context for the routing decision.

        Returns:
            The RoutingResult.
        """
        workflow.logger.info("Executing routing activity.")
        try:
            return await workflow.execute_activity(
                routing_activity,
                arg=context,
                **self._get_activity_options(),
            )
        except TemporalActivityError as e:
            workflow.logger.error(f"Routing activity failed: {e}")
            raise ActivityError(f"Routing failed: {e.cause}", activity_name="routing_activity") from e

    async def create_human_task(self, task_data: TaskData) -> TaskResult:
        """
        Executes the activity to create a human-in-the-loop task.

        Args:
            task_data: The data for the task to be created.

        Returns:
            The result of the task creation.
        """
        workflow.logger.info(f"Executing task creation activity for title: {task_data.title}")
        try:
            return await workflow.execute_activity(
                create_task_activity,
                arg=task_data,
                **self._get_activity_options(),
            )
        except TemporalActivityError as e:
            workflow.logger.error(f"Task creation activity failed: {e}")
            raise ActivityError(f"Task creation failed: {e.cause}", activity_name="create_task_activity") from e

    async def send_notification(self, notification: Notification) -> None:
        """
        Executes the activity to send a notification.

        Args:
            notification: The notification to be sent.
        """
        workflow.logger.info(f"Executing notification activity for recipient: {notification.recipient}")
        try:
            await workflow.execute_activity(
                notify_activity,
                arg=notification,
                **self._get_activity_options(),
            )
        except TemporalActivityError as e:
            workflow.logger.error(f"Notification activity failed: {e}")
            # Often, we might not want to fail the whole workflow for a notification failure.
            # Here we log it but don't re-raise, allowing the workflow to continue.
            pass

    async def wait_for_human_decision(
        self, signal_name: str = "decision", timeout_seconds: int = 3600
    ) -> Any:
        """
        Pauses the workflow to wait for a signal from a human interaction.

        Args:
            signal_name: The name of the signal to wait for. Defaults to "decision".
            timeout_seconds: The maximum time to wait for the signal.

        Returns:
            The payload of the received signal, or None if timed out.
        """
        workflow.logger.info(f"Workflow is now waiting for signal '{signal_name}' for up to {timeout_seconds} seconds.")
        decision_payload = None
        try:
            # wait_for() returns True if the signal was received, False on timeout
            signal_received = await workflow.wait_for(
                lambda: decision_payload is not None, timeout=timedelta(seconds=timeout_seconds)
            )
            if not signal_received:
                workflow.logger.warning(f"Timed out waiting for signal '{signal_name}'.")
                return None
        except Exception as e:
            workflow.logger.error(f"Error while waiting for signal: {e}")
            raise

        return decision_payload

    @workflow.signal
    def decision(self, payload: Any):
        """Signal handler for receiving a human decision."""
        workflow.logger.info(f"Received 'decision' signal with payload: {payload}")
        self.decision_payload = payload
