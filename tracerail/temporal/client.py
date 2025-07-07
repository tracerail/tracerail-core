"""
TraceRail Temporal Client Utilities

This module provides helper functions for interacting with the Temporal service,
such as obtaining a connected client and starting workflows. It simplifies the
process of connecting to Temporal and ensures that client connections are
managed efficiently.
"""
import logging
from typing import Any, Optional

from temporalio.client import Client, WorkflowHandle
from temporalio.service import RPCError

from ..config import TraceRailConfig, TemporalConfig
from .exceptions import WorkflowConfigurationError

logger = logging.getLogger(__name__)

# A simple in-memory cache for the Temporal client to avoid reconnecting.
# In a multi-worker or more complex scenario, a more robust solution for
# client management would be needed.
_client_instance: Optional[Client] = None


async def get_temporal_client(config: Optional[TemporalConfig] = None) -> Client:
    """
    Retrieves a connected Temporal client.

    This function provides a singleton-like pattern for the Temporal client,
    ensuring that only one connection is established and reused per worker process.

    Args:
        config: The Temporal configuration object. If not provided, it will
                be created with default settings.

    Returns:
        A connected Temporal client instance.

    Raises:
        WorkflowConfigurationError: If the client cannot be connected to the
                                    Temporal service.
    """
    global _client_instance
    if _client_instance:
        logger.debug("Returning existing Temporal client instance.")
        return _client_instance

    cfg = config or TemporalConfig()
    target_host = f"{cfg.host}:{cfg.port}"
    logger.info(f"Connecting to Temporal service at {target_host} in namespace '{cfg.namespace}'...")

    try:
        client = await Client.connect(
            target_host,
            namespace=cfg.namespace,
            # It's good practice to set an identity for the worker/client
            identity="tracerail-core-client",
        )
        _client_instance = client
        logger.info("Successfully connected to Temporal service.")
        return client
    except RPCError as e:
        logger.error(f"Failed to connect to Temporal service at {target_host}: {e}", exc_info=True)
        raise WorkflowConfigurationError(
            f"Could not connect to Temporal at {target_host}. "
            "Please ensure the service is running and accessible."
        ) from e
    except Exception as e:
        logger.error(f"An unexpected error occurred while connecting to Temporal: {e}", exc_info=True)
        raise WorkflowConfigurationError("An unexpected error occurred during Temporal client initialization.") from e


async def start_workflow(
    workflow: Any,
    workflow_input: Any,
    config: TraceRailConfig,
    workflow_id: Optional[str] = None,
) -> WorkflowHandle:
    """
    Starts a new Temporal workflow execution.

    Args:
        workflow: The workflow class or function to execute.
        workflow_input: The input data to pass to the workflow.
        config: The main TraceRail configuration object.
        workflow_id: An optional unique ID for the workflow execution. If not
                     provided, Temporal will generate one.

    Returns:
        A WorkflowHandle for the started workflow execution.
    """
    client = await get_temporal_client(config.temporal)
    task_queue = config.temporal.task_queue

    logger.info(f"Starting workflow '{getattr(workflow, '__name__', 'workflow')}' on task queue '{task_queue}'...")

    handle = await client.start_workflow(
        workflow,
        workflow_input,
        id=workflow_id,
        task_queue=task_queue,
    )

    logger.info(f"Workflow started successfully with ID: {handle.id} and Run ID: {handle.first_execution_run_id}")
    return handle
