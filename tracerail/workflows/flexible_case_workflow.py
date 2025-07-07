"""
This module defines the FlexibleCaseWorkflow, a generic workflow that can
execute any business process defined by a versioned Process Definition.
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow

# Import the domain model we'll be returning
from tracerail.domain.cases import Case

# This mock data is used by the query handler to return a consistent state
# for our integration tests. In a real workflow, this state would be built
# dynamically based on the process definition and signals.
MOCK_CASE_DATA: Dict[str, Any] = {
    "caseDetails": {
        "caseId": "ER-2024-08-124",
        "caseTitle": "Expense Report from John Doe for $750.00",
        "status": "Pending Agent Approval",
        "assignee": {"name": "Jane Smith", "email": "jane.smith@example.com"},
        "submitter": {"name": "John Doe", "email": "john.doe@example.com"},
        "createdAt": "2024-08-21T10:30:00Z",
        "updatedAt": "2024-08-21T10:35:00Z",
        "caseData": {
            "amount": 750.0,
            "currency": "USD",
            "category": "Travel",
            "ai_summary": "This is a request for a flight to the annual conference.",
            "ai_policy_check": "Warning: Expense exceeds the $500 standard limit for this role.",
            "ai_risk_score": "Medium",
        },
    },
    "activityStream": [
        {
            "id": 1,
            "type": "system_event",
            "sender": "System",
            "text": "Case created and assigned to AI Agent for triage.",
            "timestamp": "2024-08-21T10:30:00Z",
        },
        {
            "id": 2,
            "type": "ai_analysis",
            "sender": "AI Agent",
            "text": "Analysis complete. Risk Score: Medium. Assigning to manager for review.",
            "timestamp": "2024-08-21T10:35:00Z",
        },
    ],
    "activeInteraction": {
        "interactionId": "approve_request_ER-2024-08-124",
        "interactionType": "action_buttons",
        "prompt": "Please review the expense report. The amount is above the standard policy limit.",
        "payload": {
            "actions": [
                {"label": "Approve", "value": "approved", "style": "primary"},
                {"label": "Reject", "value": "rejected", "style": "danger"},
            ],
        },
        "submitUrl": "https://api.tracerail.com/v1/responses/ER-2024-08-124",
    },
}


@workflow.defn
class FlexibleCaseWorkflow:
    """
    A long-running, generic workflow to manage the lifecycle of any Case.

    This workflow is driven by a Process Definition document, which dictates
    the states, transitions, and interactions required for a specific business
    process.
    """

    def __init__(self) -> None:
        # The `Case` object will hold the entire state of the workflow.
        # It's initialized as None and will be populated when the workflow runs.
        self._case_state: Case = None

    @workflow.run
    async def run(self, process_name: str, process_version: str, initial_payload: Dict[str, Any]) -> None:
        """
        The main entry point for the workflow.

        Args:
            process_name: The name of the business process to execute (e.g., "expense_approval").
            process_version: The version of the process definition to use (e.g., "1.2.0").
            initial_payload: The initial data that starts the case (e.g., the submitted expense report).
        """
        workflow.logger.info(
            f"Starting FlexibleCaseWorkflow for process '{process_name}' "
            f"version '{process_version}' with ID: {workflow.info().workflow_id}"
        )

        # In a real implementation, the first step would be to call an activity
        # to load the process definition from the artifact store based on the
        # process_name and process_version.
        #
        # E.g.: self._process_definition = await workflow.execute_activity(
        #     load_process_definition,
        #     ProcessId(name=process_name, version=process_version),
        #     start_to_close_timeout=timedelta(seconds=10),
        # )

        # For now, we will use our mock data to populate the initial state.
        # This allows us to test the query method and the API layer.
        self._case_state = Case.model_validate(MOCK_CASE_DATA)

        # The core of the workflow engine would be a loop that waits for signals
        # from the agent, processes them according to the rules in the process
        # definition, and transitions to the next state.
        #
        # For now, we will just wait indefinitely to simulate an active, running
        # workflow that is waiting for a human interaction.
        await asyncio.sleep(3600)  # Wait for 1 hour

    @workflow.query
    def get_current_state(self) -> Case:
        """
        A query method that allows external clients to get the complete,
        up-to-the-minute state of the case.

        Returns:
            The full Case object, including details, activity stream, and the
            active interaction required from the agent.
        """
        return self._case_state
