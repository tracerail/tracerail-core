"""
This module defines the FlexibleCaseWorkflow, a generic workflow that can
execute any business process defined by a versioned Process Definition.
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict

from temporalio import activity, workflow

# Import the domain models we'll be using
from tracerail.domain.cases import ActivityStreamItem, Case

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
        self._decision: str = None

    @workflow.signal
    def decision(self, choice: str) -> None:
        """Signal handler for receiving a decision from an agent."""
        self._decision = choice

    @workflow.run
    async def run(self, process_name: str, process_version: str, initial_payload: Dict[str, Any]) -> Case:
        """
        The main entry point for the workflow.

        Args:
            process_name: The name of the business process to execute (e.g., "expense_approval").
            process_version: The version of the process definition to use (e.g., "1.2.0").
            initial_payload: The initial data that starts the case (e.g., the submitted expense report).
        """
        workflow.logger.info(
            "Starting FlexibleCaseWorkflow",
            process_name=process_name,
            process_version=process_version,
            workflow_id=workflow.info().workflow_id,
        )

        # Construct the initial case state from the incoming payload.
        now = workflow.now()
        case_id = workflow.info().workflow_id
        title = (
            initial_payload.get("title")
            or f"Expense from {initial_payload.get('submitter_name', 'N/A')}"
        )

        self._case_state = Case(
            caseDetails={
                "caseId": case_id,
                "caseTitle": title,
                "status": "Pending Agent Approval",
                "assignee": {"name": "AI Triage", "email": "ai@tracerail.io"},
                "submitter": {
                    "name": initial_payload.get("submitter_name"),
                    "email": initial_payload.get("submitter_email"),
                },
                "createdAt": now,
                "updatedAt": now,
                "caseData": {
                    "amount": initial_payload.get("amount"),
                    "currency": initial_payload.get("currency"),
                    "category": initial_payload.get("category"),
                    # These will be populated by a real AI activity later
                    "ai_summary": "Initial analysis pending.",
                    "ai_policy_check": "Awaiting AI policy check.",
                    "ai_risk_score": "Unknown",
                },
            },
            activityStream=[
                {
                    "id": 1,
                    "type": "system_event",
                    "sender": "System",
                    "text": f"Case created by {initial_payload.get('submitter_name')}.",
                    "timestamp": now,
                }
            ],
            activeInteraction={
                "interactionId": f"approve_request_{case_id}",
                "interactionType": "action_buttons",
                "prompt": "Please review the initial case submission.",
                "payload": {
                    "actions": [
                        {"label": "Approve", "value": "approved", "style": "primary"},
                        {"label": "Reject", "value": "rejected", "style": "danger"},
                    ],
                },
                "submitUrl": f"/api/v1/cases/{case_id}/decision",
            },
        )

        # Execute the enrichment activity to get AI-driven insights.
        workflow.logger.info("Executing enrichment activity")
        enrichment_result = await workflow.execute_activity(
            "enrich_case_data_activity",
            self._case_state.caseDetails.caseData.model_dump(),
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Update the case state with the results from the activity.
        self._case_state.caseDetails.caseData.ai_summary = enrichment_result.get("ai_summary")
        self._case_state.caseDetails.caseData.ai_policy_check = enrichment_result.get("ai_policy_check")
        self._case_state.caseDetails.caseData.ai_risk_score = enrichment_result.get("ai_risk_score")
        self._case_state.caseDetails.updatedAt = workflow.now()
        workflow.logger.info("Enrichment complete, case state updated")

        # The workflow will now pause and wait for the 'decision' signal to be
        # sent. The `wait_condition` will unblock the execution as soon as the
        # `self._decision` attribute is populated by the signal handler.
        workflow.logger.info("Workflow waiting for agent decision")
        await workflow.wait_condition(lambda: self._decision is not None)

        workflow.logger.info("Decision received, updating case state", decision=self._decision)

        # Update the case status based on the decision
        if self._decision.lower() == "approved":
            self._case_state.caseDetails.status = "Approved"
        elif self._decision.lower() == "rejected":
            self._case_state.caseDetails.status = "Rejected"
        else:
            # Handle any other decision as a generic 'processed' state
            self._case_state.caseDetails.status = f"Processed: {self._decision}"

        # The interaction is now complete, so we remove it from the state.
        self._case_state.activeInteraction = None

        # Add the decision to the activity stream for historical record.
        new_activity = ActivityStreamItem(
            id=len(self._case_state.activityStream) + 1,
            type="agent_decision",
            sender="Agent",  # In a real app, this would be the actual agent's ID/name
            text=f"Case marked as '{self._decision}'.",
            timestamp=workflow.now(),
        )
        self._case_state.activityStream.append(new_activity)

        workflow.logger.info(
            "Case status updated",
            case_id=self._case_state.caseDetails.caseId,
            new_status=self._case_state.caseDetails.status,
        )

        # Return the final state so it's recorded in the workflow history.
        return self._case_state

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
