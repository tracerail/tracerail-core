"""
This module defines the core domain models and services for 'Cases'.

A Case represents a primary unit of work within the TraceRail system,
such as an expense report, a support ticket, or any other workflow instance
that requires tracking and potential human interaction.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from temporalio.client import Client, WorkflowHandle
from temporalio.service import RPCError


# --- Pydantic Models for the Case Domain ---
# These models define the canonical data structure for a Case and its components.
# They are used to ensure data consistency across different layers of the application.

class CaseParticipant(BaseModel):
    name: str
    email: Optional[str] = None


class CaseData(BaseModel):
    amount: float
    currency: str
    category: str
    ai_summary: str
    ai_policy_check: str
    ai_risk_score: str


class CaseDetails(BaseModel):
    caseId: str
    caseTitle: str
    status: str
    assignee: CaseParticipant
    submitter: CaseParticipant
    createdAt: datetime
    updatedAt: datetime
    caseData: CaseData


class ActivityStreamItem(BaseModel):
    id: int
    type: str
    sender: str
    text: str
    timestamp: datetime


class ActionButton(BaseModel):
    label: str
    value: str
    style: str


class InteractionPayload(BaseModel):
    actions: List[ActionButton]


class ActiveInteraction(BaseModel):
    interactionId: str
    interactionType: str
    prompt: str
    payload: InteractionPayload
    submitUrl: str


class Case(BaseModel):
    """
    The top-level model representing a complete Case.
    """
    caseDetails: CaseDetails
    activityStream: List[ActivityStreamItem]
    activeInteraction: ActiveInteraction


# --- Service Layer for Case Management ---

class CaseService:
    """
    A service class that encapsulates business logic for managing cases by
    interacting with the Temporal service.

    This acts as an abstraction layer between the Temporal client and the
    application layers that need to interact with Case data (like the API bridge).
    """

    def __init__(self, client: Client):
        """
        Initializes the CaseService with a Temporal client.

        Args:
            client: An active temporalio.Client instance.
        """
        self.client = client

    async def get_by_id(self, case_id: str) -> Optional[Case]:
        """
        Retrieves a single case by querying its running workflow execution.

        Args:
            case_id: The ID of the case, which corresponds to the workflow_id.

        Returns:
            A `Case` object if a running workflow with that ID is found and
            successfully queried, otherwise `None`.
        """
        print(f"[Core Service] Attempting to query workflow with ID: {case_id}")
        try:
            # Get a handle to the workflow. The workflow_id is our case_id.
            handle: WorkflowHandle = self.client.get_workflow_handle(case_id)

            # Execute the "get_current_state" query against the workflow.
            # The result is automatically deserialized by Temporal into the
            # return type hint of the query method (which is our Case model).
            result = await handle.query("get_current_state")

            if isinstance(result, Case):
                print(f"[Core Service] Successfully retrieved state for case: {case_id}")
                return result
            else:
                # This case should ideally not be hit if the workflow query
                # is correctly type-hinted, but it's a good safeguard.
                print(f"[Core Service] ERROR: Query for case {case_id} returned unexpected type: {type(result)}")
                return None

        except RPCError as e:
            # This is a common error, e.g., if the workflow doesn't exist.
            # We log it and return None to the caller.
            print(f"[Core Service] ERROR: RPC error while querying case {case_id}: {e.message}")
            return None
