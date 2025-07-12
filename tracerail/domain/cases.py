"""
This module defines the core domain models and services for 'Cases'.

A Case represents a primary unit of work within the TraceRail system,
such as an expense report, a support ticket, or any other workflow instance
that requires tracking and potential human interaction.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ValidationError
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
    activeInteraction: Optional[ActiveInteraction]


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
        Retrieves a single case by its ID. It first tries to query a running
        workflow. If that fails because the workflow is not found (e.g., it has
        already completed), it attempts to fetch the final result from history.
        """
        handle = self.client.get_workflow_handle(case_id)
        try:
            # First, try to query the running workflow.
            print(f"[Core Service] Attempting to query active workflow: {case_id}")
            result_dict = await handle.query("get_current_state")

            if result_dict:
                try:
                    validated_case = Case.model_validate(result_dict)
                    print(f"[Core Service] Successfully retrieved state via query for case: {case_id}")
                    return validated_case
                except ValidationError as e:
                    print(f"[Core Service] ERROR: Pydantic validation failed for active case {case_id}: {e}")
                    return None

            print(f"[Core Service] WARN: Active query for case {case_id} returned no data.")
            return None

        except RPCError as e:
            # If a 'not found' error occurs, the workflow might be complete.
            if e.status and e.status.name == 'NOT_FOUND':
                print(f"[Core Service] Workflow not queryable. Attempting to fetch result from history for case: {case_id}")
                try:
                    # This relies on the workflow returning its final state.
                    result = await handle.result()
                    if isinstance(result, Case):
                        print(f"[Core Service] Successfully retrieved 'Case' object result for completed case: {case_id}")
                        return result
                    elif isinstance(result, dict):
                        print(f"[Core Service] Successfully retrieved 'dict' result for completed case: {case_id}")
                        return Case.model_validate(result)

                    print(f"[Core Service] Completed workflow {case_id} did not return a readable state.")
                    return None
                except Exception as hist_e:
                    print(f"[Core Service] ERROR: Could not fetch result for completed workflow {case_id}: {hist_e}")
                    return None

            # For any other RPC error, log and return None.
            print(f"[Core Service] ERROR: Unexpected RPC error for case {case_id}: {e.message}")
            return None
