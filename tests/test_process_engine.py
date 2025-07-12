import asyncio
import pytest
from unittest.mock import MagicMock
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity
from temporalio.contrib.pydantic import pydantic_data_converter


from tracerail.workflows.flexible_case_workflow import FlexibleCaseWorkflow
from tracerail.domain.cases import Case

# A mock process definition that our test will use.
# This represents the data that would be loaded from a YAML file.
MOCK_PROCESS_DEFINITION = {
    "process_name": "test_process",
    "process_version": "1.0.0",
    "initial_step": "human_review_step",
    "steps": [
        {
            "step_id": "human_review_step",
            "step_type": "human_in_the_loop",
            "configuration": {
                "prompt": "Test prompt from process definition.",
                "actions": [
                    {"label": "Approve", "value": "approved", "style": "primary"},
                ],
            },
            "transitions": [
                {"on_signal": "approved", "next_step": "end_approved"}
            ],
        },
        {
            "step_id": "end_approved",
            "step_type": "final_commit",
            "configuration": {"final_status": "Test-Succeeded"},
        },
    ]
}

# --- The Test Case (Refactored) ---
@pytest.mark.asyncio
async def test_workflow_engine_with_mocked_activity():
    """
    Tests that the workflow engine correctly calls the loader activity
    and executes the returned process definition.
    """
    # Create a mock for the activity that loads our process definition.
    @activity.defn(name="load_process_definition_activity")
    async def load_process_definition_mock(process_name: str, version: str) -> dict:
        return MOCK_PROCESS_DEFINITION

    # Use the test environment with the Pydantic data converter
    async with await WorkflowEnvironment.start_time_skipping(
        data_converter=pydantic_data_converter,
    ) as env:
        async with Worker(
            env.client,
            task_queue="test-engine-queue",
            workflows=[FlexibleCaseWorkflow],
            activities=[load_process_definition_mock],
        ):
            handle = await env.client.start_workflow(
                FlexibleCaseWorkflow.run,
                args=["test_process", "1.0.0", {"submitter_name": "Engine Tester"}],
                id="test-engine-workflow",
                task_queue="test-engine-queue",
            )

            # Give the workflow a moment to initialize
            await asyncio.sleep(0.1)

            # 1. Verify the initial state is set by the process definition.
            # In the test environment, the query returns a dict, so we validate it directly.
            initial_state = await handle.query("get_current_state")
            assert isinstance(initial_state, dict)
            assert (
                initial_state["activeInteraction"]["prompt"]
                == "Test prompt from process definition."
            )

            # 2. Send the signal that the 'human_review_step' is waiting for.
            await handle.signal("decision", "approved")

            # 3. Get the final result of the workflow.
            # The workflow's return value *is* a hydrated Pydantic model.
            final_result = await handle.result()
            assert isinstance(final_result, Case)

            # 4. Assert that the final status matches the 'end_approved' step.
            assert final_result.caseDetails.status == "Test-Succeeded"
