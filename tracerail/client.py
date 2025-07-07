"""
TraceRail Core Client

This module provides the main client interface for the TraceRail system,
offering a simplified entry point for processing content, handling routing,
and managing human-in-the-loop tasks.
"""
import logging
import time
from typing import Any, Dict, Optional

from temporalio.client import WorkflowHandle

from .config import TraceRailConfig
from .exceptions import TraceRailError, TaskError
from .llm.base import BaseLLMProvider, LLMRequest, LLMResponse
from .llm.factory import create_llm_provider
from .routing.base import BaseRoutingEngine, RoutingContext, RoutingResult
from .routing.factory import create_routing_engine
from .tasks.base import BaseTaskManager
from .tasks.factory import create_task_manager
from .tasks.models import TaskData, TaskPriority, TaskResult

logger = logging.getLogger(__name__)


class ProcessingResult:
    """
    Represents the final result of a content processing request.
    This object encapsulates the outputs from each stage of the TraceRail pipeline.
    """

    def __init__(
        self,
        llm_response: LLMResponse,
        routing_decision: RoutingResult,
        task_result: Optional[TaskResult] = None,
        processing_time_ms: float = 0.0,
    ):
        self.llm_response = llm_response
        self.routing_decision = routing_decision
        self.task_result = task_result
        self.processing_time_ms = processing_time_ms

    @property
    def requires_human(self) -> bool:
        """Indicates if the process resulted in a human task."""
        return self.routing_decision.requires_human

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the result to a dictionary."""
        return {
            "requires_human": self.requires_human,
            "llm_response": self.llm_response.to_dict(),
            "routing_decision": self.routing_decision.to_dict(),
            "task_result": self.task_result.to_dict() if self.task_result else None,
            "processing_time_ms": self.processing_time_ms,
        }


class TraceRail:
    """
    The main client for interacting with the TraceRail system.

    This client orchestrates LLM processing, intelligent routing, and task
    management to create robust AI workflows with human-in-the-loop capabilities.
    """

    def __init__(self, config: Optional[TraceRailConfig] = None):
        """
        Initializes the TraceRail client.

        Args:
            config: A TraceRailConfig object. If None, configuration is
                    loaded from environment variables.
        """
        self.config = config or TraceRailConfig()
        self._llm_provider: Optional[BaseLLMProvider] = None
        self._routing_engine: Optional[BaseRoutingEngine] = None
        self._task_manager: Optional[BaseTaskManager] = None
        self._initialized = False

    async def initialize(self):
        """
        Initializes the client and its components asynchronously.
        This method must be called before using the client.
        """
        if self._initialized:
            logger.warning("TraceRail client is already initialized.")
            return

        logger.info("Initializing TraceRail client...")
        try:
            self._llm_provider = await create_llm_provider(self.config.llm)
            self._routing_engine = await create_routing_engine(self.config.routing)
            if self.config.tasks.enabled:
                self._task_manager = await create_task_manager(self.config.tasks)
            self._initialized = True
            logger.info("TraceRail client initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize TraceRail client: %s", e, exc_info=True)
            raise TraceRailError(f"Client initialization failed: {e}") from e

    def _ensure_initialized(self):
        """Raises an error if the client has not been initialized."""
        if not self._initialized:
            raise TraceRailError(
                "Client not initialized. Call `await client.initialize()` or use an async context manager."
            )

    @property
    def llm_provider(self) -> BaseLLMProvider:
        """Returns the configured LLM provider instance."""
        self._ensure_initialized()
        if not self._llm_provider:
             raise TraceRailError("LLM provider is not available.")
        return self._llm_provider

    @property
    def routing_engine(self) -> BaseRoutingEngine:
        """Returns the configured routing engine instance."""
        self._ensure_initialized()
        if not self._routing_engine:
             raise TraceRailError("Routing engine is not available.")
        return self._routing_engine

    @property
    def task_manager(self) -> BaseTaskManager:
        """Returns the configured task manager instance."""
        self._ensure_initialized()
        if not self._task_manager:
            raise TaskError("Task manager is not enabled or configured.")
        return self._task_manager

    async def process_content(self, content: str, **kwargs) -> ProcessingResult:
        """
        Processes content through the full LLM, routing, and tasking workflow.

        Args:
            content: The text content to process.
            **kwargs: Additional options to pass to the LLM request.

        Returns:
            A ProcessingResult object containing the outcomes of each stage.
        """
        start_time = time.time()
        self._ensure_initialized()

        # 1. LLM Processing
        llm_request = LLMRequest(content=content, **kwargs)
        llm_response = await self.llm_provider.process(llm_request)

        # 2. Routing Decision
        routing_context = RoutingContext(content=content, llm_response=llm_response)
        routing_decision = await self.routing_engine.route(routing_context)

        # 3. Task Creation (if required)
        task_result = None
        if routing_decision.requires_human:
            if not self.config.tasks.enabled or not self._task_manager:
                logger.warning(
                    "Routing decided human review is needed, but task manager is not enabled."
                )
            else:
                task_data = TaskData(
                    title=f"Review required: {content[:50]}...",
                    description=f"AI-driven routing requested human review. Reason: {routing_decision.reason}",
                    priority=self._determine_task_priority(routing_decision),
                    metadata={
                        "source": "process_content",
                        "original_content": content,
                        "llm_response_id": llm_response.request_id,
                        "routing_decision_id": routing_decision.request_id,
                    },
                )
                created_task_data = await self.task_manager.create_task(task_data)
                task_result = await self.task_manager.get_task(created_task_data.task_id)

        processing_time_ms = (time.time() - start_time) * 1000
        return ProcessingResult(
            llm_response, routing_decision, task_result, processing_time_ms
        )

    async def start_workflow(
        self,
        workflow: Any,
        arg: Any,
        *,
        id: str,
        task_queue: Optional[str] = None,
        **kwargs: Any,
    ) -> WorkflowHandle:
        """
        Starts a new Temporal workflow execution.

        This method is a convenient wrapper around the underlying Temporal client's
        `start_workflow` method, using the client's configuration for defaults.

        Args:
            workflow: The workflow function or `ClassName.run` to execute.
            arg: The single argument to pass to the workflow.
            id: A unique business ID for the workflow execution.
            task_queue: The task queue to run on. If None, uses the queue from config.
            **kwargs: Additional options to pass to Temporal's `start_workflow`.

        Returns:
            A handle to the started workflow execution.
        """
        from .temporal.client import get_temporal_client

        self._ensure_initialized()

        # Get a connection to the temporal service
        temporal_client = await get_temporal_client(self.config.temporal)

        # Use the provided task_queue, or fall back to the one in the config
        final_task_queue = task_queue or self.config.temporal.task_queue

        return await temporal_client.start_workflow(
            workflow,
            arg,
            id=id,
            task_queue=final_task_queue,
            **kwargs,
        )

    def _determine_task_priority(self, routing_result: RoutingResult) -> TaskPriority:
        """Determines task priority based on routing result confidence."""
        confidence = routing_result.confidence or 0.0
        if confidence < 0.4:
            return TaskPriority.HIGH
        if confidence < 0.7:
            return TaskPriority.NORMAL
        return TaskPriority.LOW

    async def close(self):
        """Closes the client and cleans up resources."""
        if self._llm_provider:
            await self._llm_provider.close()
        if self._routing_engine:
            await self._routing_engine.close()
        if self._task_manager:
            await self._task_manager.close()
        self._initialized = False
        logger.info("TraceRail client closed.")

    async def __aenter__(self):
        """Enables usage of the client as an async context manager."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleans up resources when exiting the async context."""
        await self.close()


def create_client(config: Optional[TraceRailConfig] = None) -> TraceRail:
    """
    Factory function to create a TraceRail client instance.

    Note: The client must be initialized with `await client.initialize()`
    or used as an async context manager before it can be used.

    Args:
        config: Optional configuration object. Loads from environment if None.

    Returns:
        An uninitialized TraceRail client instance.
    """
    return TraceRail(config)


async def create_client_async(config: Optional[TraceRailConfig] = None) -> TraceRail:
    """
    Factory function to create and asynchronously initialize a TraceRail client.

    Args:
        config: Optional configuration object. Loads from environment if None.

    Returns:
        An initialized TraceRail client instance.
    """
    client = TraceRail(config)
    await client.initialize()
    return client
