"""
TraceRail Temporal Activities

This module defines the Temporal activities that encapsulate the core
functionalities of the TraceRail SDK, such as interacting with LLMs,
executing routing logic, and managing tasks.

These activities are designed to be called from within Temporal workflows.
"""
import logging
from typing import Dict, Any

from temporalio import activity

# Import core TraceRail components and models
from ..config import TraceRailConfig
from ..llm import create_llm_provider, LLMRequest, LLMResponse
from ..routing import create_routing_engine, RoutingContext, RoutingResult
from ..tasks import create_task_manager, TaskData, TaskResult
from ..tasks.notification import create_notification_service, Notification

# Initialize logger
logger = logging.getLogger(__name__)

# A best practice is to initialize clients/providers once per activity worker
# and pass them via a shared context or dependency injection framework.
# For simplicity and to make activities self-contained, these examples
# initialize components within each call.

@activity.defn
async def llm_activity(request: LLMRequest, config_dict: Dict[str, Any]) -> LLMResponse:
    """
    Activity to process a request through an LLM provider.

    Args:
        request: The LLMRequest object containing the prompt and parameters.
        config_dict: A dictionary representing the TraceRail configuration.

    Returns:
        An LLMResponse object with the result from the LLM.
    """
    activity.heartbeat("Initializing LLM provider...")
    logger.info(f"Executing llm_activity for request_id: {request.request_id}")

    try:
        # Create config and provider from the dictionary
        config = TraceRailConfig.model_validate(config_dict)
        llm_provider = await create_llm_provider(config.llm)

        activity.heartbeat(f"Processing with model: {config.llm.model}")
        response = await llm_provider.process(request)

        logger.info(f"LLM processing complete for request_id: {request.request_id}")
        await llm_provider.close()
        return response

    except Exception as e:
        logger.error(f"Error in llm_activity: {e}", exc_info=True)
        # Re-raise the exception to allow Temporal to handle it as an ApplicationError
        raise


@activity.defn
async def routing_activity(context: RoutingContext, config_dict: Dict[str, Any]) -> RoutingResult:
    """
    Activity to perform intelligent routing based on a given context.

    Args:
        context: The RoutingContext containing data for the routing decision.
        config_dict: A dictionary representing the TraceRail configuration.

    Returns:
        A RoutingResult object with the decision.
    """
    activity.heartbeat("Initializing routing engine...")
    logger.info("Executing routing_activity...")

    try:
        config = TraceRailConfig.model_validate(config_dict)
        routing_engine = await create_routing_engine(config.routing)

        activity.heartbeat("Evaluating routing rules...")
        result = await routing_engine.route(context)

        logger.info(f"Routing decision: {result.decision}, Reason: {result.reason}")
        await routing_engine.close()
        return result

    except Exception as e:
        logger.error(f"Error in routing_activity: {e}", exc_info=True)
        raise

@activity.defn
async def create_task_activity(task_data: TaskData, config_dict: Dict[str, Any]) -> TaskResult:
    """
    Activity to create a human-in-the-loop task.

    Args:
        task_data: The data for the task to be created.
        config_dict: A dictionary representing the TraceRail configuration.

    Returns:
        A TaskResult object representing the created task.
    """
    activity.heartbeat("Initializing task manager...")
    logger.info("Executing create_task_activity...")

    try:
        config = TraceRailConfig.model_validate(config_dict)
        if not config.tasks.enabled:
            logger.warning("Task management is disabled; create_task_activity will have no effect.")
            # Return a dummy or empty result if tasks are disabled
            return TaskResult(task_id="disabled", status="cancelled", data=task_data)

        task_manager = await create_task_manager(config.tasks)

        activity.heartbeat(f"Creating task with title: {task_data.title}")
        created_task = await task_manager.create_task(task_data)

        logger.info(f"Task '{created_task.task_id}' created successfully.")
        await task_manager.close()
        return created_task

    except Exception as e:
        logger.error(f"Error in create_task_activity: {e}", exc_info=True)
        raise

@activity.defn
async def notify_activity(notification: Notification, config_dict: Dict[str, Any]) -> None:
    """
    Activity to send a notification.

    Args:
        notification: The Notification object to be sent.
        config_dict: A dictionary representing the TraceRail configuration.
    """
    activity.heartbeat(f"Initializing notification service for channel: {notification.channel}")
    logger.info(f"Executing notify_activity for recipient: {notification.recipient}")

    try:
        config = TraceRailConfig.model_validate(config_dict)
        notification_service = create_notification_service(
            config.tasks.notification_service, **config.tasks.notification_config
        )

        activity.heartbeat(f"Sending notification: {notification.subject}")
        await notification_service.send(notification)

        logger.info(f"Notification sent successfully to {notification.recipient}.")

    except Exception as e:
        logger.error(f"Error in notify_activity: {e}", exc_info=True)
        raise
