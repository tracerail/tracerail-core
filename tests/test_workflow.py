"""
Tests for the FlexibleCaseWorkflow.
"""

import pytest
import asyncio
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

# Import the workflow we want to test
from tracerail.workflows.flexible_case_workflow import FlexibleCaseWorkflow
from tracerail.domain.cases import Case
# Import the real activity we want to mock
from tracerail.activities.case_activities import enrich_case_data
# Import the real activity we want to test
from tracerail.activities.case_activities import enrich_case_data


# --- The Test Case ---

@pytest.mark.asyncio
async def test_workflow_calls_real_activity():
    """
    This test verifies that the workflow correctly calls the real enrichment
    activity and uses its result to populate the case state.
    """
    # Use the Temporal testing environment to run the workflow in-memory.
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Create a worker that knows about the workflow and the REAL activity.
        async with Worker(
            env.client,
            task_queue="test-real-activity-queue",
            workflows=[FlexibleCaseWorkflow],
            activities=[enrich_case_data],
        ):
            # The initial data to start the workflow.
            initial_payload = {
                "submitter_name": "Real Activity Tester",
                "amount": 750.00,
                "currency": "USD",
                "category": "Travel"
            }

            # Start the workflow
            handle = await env.client.start_workflow(
                FlexibleCaseWorkflow.run,
                args=["test_process", "1.0", initial_payload],
                id="test-real-activity-workflow",
                task_queue="test-real-activity-queue",
            )

            # Give the workflow a moment to run and call the activity.
            await asyncio.sleep(2)

            # Query the workflow's state and validate it.
            queried_state_dict = await handle.query("get_current_state")
            queried_state = Case.model_validate(queried_state_dict)

            # Assert that the case data contains the results from the real activity.
            # These values come from the logic inside `case_activities.py`.
            assert queried_state.caseDetails.caseData.ai_policy_check == "Compliant with company policy."
            assert queried_state.caseDetails.caseData.ai_risk_score == "Low"

            # Terminate the workflow to clean up the test
            await handle.terminate()
