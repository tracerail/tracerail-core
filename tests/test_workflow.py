"""
Tests for the FlexibleCaseWorkflow, focusing on different paths through a
declarative process definition.
"""

import pytest
import asyncio
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter

# Import the workflow we want to test
from tracerail.workflows.flexible_case_workflow import FlexibleCaseWorkflow
from tracerail.domain.cases import Case


# A mock process definition that includes a rejection path.
MOCK_REJECT_PROCESS_DEFINITION = {
    "process_name": "test_rejection_process",
    "process_version": "1.0.0",
    "initial_step": "human_review_step",
    "steps": [
        {
            "step_id": "human_review_step",
            "step_type": "human_in_the_loop",
            "configuration": {
                "prompt": "Test prompt for rejection.",
                "actions": [
                    {"label": "Approve", "value": "approved", "style": "primary"},
                    {"label": "Reject", "value": "rejected", "style": "danger"},
                ],
            },
            "transitions": [
                {"on_signal": "approved", "next_step": "end_approved"},
                {"on_signal": "rejected", "next_step": "end_rejected"},
            ],
        },
        {
            "step_id": "end_approved",
            "step_type": "final_commit",
            "configuration": {"final_status": "Approved"},
        },
        {
            "step_id": "end_rejected",
            "step_type": "final_commit",
            "configuration": {"final_status": "Rejected"},
        },
    ],
}


@pytest.mark.asyncio
async def test_workflow_handles_rejection_path():
    """
    This test verifies that the workflow correctly follows the 'rejection'
    path based on a received signal.
    """
    # Create a mock for the activity that loads our process definition.
    @activity.defn(name="load_process_definition_activity")
    async def load_process_definition_mock(process_name: str, version: str) -> dict:
        return MOCK_REJECT_PROCESS_DEFINITION

    # Use the Temporal testing environment to run the workflow in-memory.
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter,
    ) as env:
        # Create a worker that knows about the workflow and the MOCKED activity.
        async with Worker(
            env.client,
            task_queue="test-rejection-queue",
            workflows=[FlexibleCaseWorkflow],
            activities=[load_process_definition_mock],
        ):
            # The initial data to start the workflow.
            initial_payload = {"submitter_name": "Rejection Tester"}

            # Start the workflow
            handle = await env.client.start_workflow(
                FlexibleCaseWorkflow.run,
                args=["test_rejection_process", "1.0", initial_payload],
                id="test-rejection-workflow",
                task_queue="test-rejection-queue",
            )

            # Give the workflow a moment to initialize and enter the human step.
            await asyncio.sleep(0.1)

            # Query the workflow state to ensure it's waiting for a decision.
            # In the test environment, the query returns a dict, so we validate it directly.
            initial_state = await handle.query("get_current_state")
            assert isinstance(initial_state, dict)
            assert initial_state["caseDetails"]["status"] == "Pending Human Review"
            assert initial_state["activeInteraction"] is not None

            # Send the 'rejected' signal
            await handle.signal("decision", "rejected")

            # Wait for the workflow to process the signal and finish.
            # The workflow's return value *is* a hydrated Pydantic model.
            final_result = await handle.result()
            assert isinstance(final_result, Case)


            # Assert that the final status is 'Rejected'
            assert final_result.caseDetails.status == "Rejected"
