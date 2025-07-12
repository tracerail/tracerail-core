"""
This script is a utility for starting a new FlexibleCaseWorkflow execution.

It connects to the Temporal service and executes the `start_workflow` method
on the client, providing the necessary arguments to begin a new case.
"""

import asyncio
import os
from typing import Any, Dict

from temporalio.client import Client

# Import the workflow we want to start
from tracerail.workflows.flexible_case_workflow import FlexibleCaseWorkflow


async def main():
    """
    Connects to Temporal and starts a new workflow execution.
    """
    # Get Temporal connection details from environment variables with defaults.
    host = os.getenv("TEMPORAL_HOST", "localhost")
    port = int(os.getenv("TEMPORAL_PORT", 7233))
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("TEMPORAL_CASES_TASK_QUEUE", "cases-task-queue")
    target = f"{host}:{port}"

    # Define the parameters for our new workflow.
    # We use a hardcoded ID here to ensure it matches what the frontend expects.
    case_id = "ER-2024-08-124"
    process_name = "expense_approval"
    process_version = "1.0.0"

    # This is the initial data payload that would trigger the workflow.
    # It represents the submitted expense report data.
    initial_payload: Dict[str, Any] = {
        "submitter": {"name": "John Doe", "email": "john.doe@example.com"},
        "amount": 750.00,
        "currency": "USD",
        "category": "Travel",
        "line_items": [{"description": "Flight to conference", "amount": 750.00}],
        "attachments": [{"fileName": "receipt_flight.pdf", "url": "/files/receipt1.pdf"}],
    }

    try:
        # Create a client to connect to the Temporal service.
        client = await Client.connect(target, namespace=namespace)
        print("✅ Successfully connected to Temporal.")

        # Start the workflow.
        # This sends a command to the Temporal service to create a new
        # workflow execution. The service will then place a task on the
        # specified task queue, which our worker will pick up.
        handle = await client.start_workflow(
            FlexibleCaseWorkflow.run,
            args=[process_name, process_version, initial_payload],
            id=case_id,
            task_queue=task_queue,
        )

        print(f"🚀 Successfully started workflow.")
        print(f"   Workflow ID (Case ID): {handle.id}")
        print(f"   Run ID: {handle.result_run_id}")

    except Exception as e:
        print(f"❌ Failed to start workflow: {e}")
        return


if __name__ == "__main__":
    # Run the main async function using Python's asyncio event loop.
    asyncio.run(main())
