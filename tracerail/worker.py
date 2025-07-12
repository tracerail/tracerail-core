from __future__ import annotations
"""
This script runs a Temporal Worker that hosts the FlexibleCaseWorkflow.

The Worker connects to the Temporal service, listens on a specific task queue,
and executes workflow code when tasks become available.
"""

import asyncio
import os
import structlog

from temporalio.client import Client
from temporalio.worker import Worker

# Import the workflow that this worker will run.
from tracerail.workflows.flexible_case_workflow import FlexibleCaseWorkflow
from tracerail.activities.case_activities import enrich_case_data


# --- Structured Logging Setup ---
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
log = structlog.get_logger()


async def main():
    """
    The main entry point for the worker process.
    """
    # Get Temporal connection details from environment variables with defaults.
    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = int(os.getenv("TEMPORAL_PORT", 7233))
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_CASES_TASK_QUEUE", "cases-task-queue")
    target = f"{host}:{port}"

    log.info("Connecting to Temporal service", target=target)
    try:
        # Create a client to connect to the Temporal service.
        client = await Client.connect(target, namespace=namespace)
        log.info("Successfully connected to Temporal.")
    except Exception as e:
        log.error("Failed to connect to Temporal", error=str(e))
        return

    # Create and run the worker.
    # The worker is configured with the client, the task queue it should listen on,
    # and the list of workflows it is capable of executing.
    log.info("Starting worker", task_queue=task_queue)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[FlexibleCaseWorkflow],
        activities=[enrich_case_data],
    )

    try:
        # This is a long-running process that will continuously poll the
        # task queue for new work.
        await worker.run()
        log.info("Worker has started successfully.")
    except KeyboardInterrupt:
        log.info("Worker shutting down gracefully...")
    except Exception as e:
        log.error("An unexpected error occurred with the worker", error=str(e))


if __name__ == "__main__":
    # Run the main async function using Python's asyncio event loop.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Process interrupted by user.")
