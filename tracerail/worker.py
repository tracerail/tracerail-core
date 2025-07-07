"""
This script runs a Temporal Worker that hosts the FlexibleCaseWorkflow.

The Worker connects to the Temporal service, listens on a specific task queue,
and executes workflow code when tasks become available.
"""

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

# Import the workflow that this worker will run.
# The `from __future__` is a good practice for forward compatibility in Python.
from __future__ import annotations
from tracerail.workflows.flexible_case_workflow import FlexibleCaseWorkflow


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

    print(f"Connecting to Temporal service at {target}...")
    try:
        # Create a client to connect to the Temporal service.
        client = await Client.connect(target, namespace=namespace)
        print("✅ Successfully connected to Temporal.")
    except Exception as e:
        print(f"❌ Failed to connect to Temporal: {e}")
        return

    # Create and run the worker.
    # The worker is configured with the client, the task queue it should listen on,
    # and the list of workflows it is capable of executing.
    print(f"Starting worker on task queue: '{task_queue}'...")
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[FlexibleCaseWorkflow],
        # We could also register activities here if the workflow needed them:
        # activities=[...],
    )

    try:
        # This is a long-running process that will continuously poll the
        # task queue for new work.
        await worker.run()
        print("Worker has started successfully.")
    except KeyboardInterrupt:
        print("\nWorker shutting down gracefully...")
    except Exception as e:
        print(f"❌ An unexpected error occurred with the worker: {e}")


if __name__ == "__main__":
    # Run the main async function using Python's asyncio event loop.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
