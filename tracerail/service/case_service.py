"""
This module defines the core service layer for managing Cases.
"""

from typing import Optional, Dict, Any

from pydantic import ValidationError
from temporalio.client import Client
from temporalio.service import RPCError

# The service layer needs to know about the domain models it's working with.
from tracerail.domain.cases import Case


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

    # Updated to be tenant-aware. In a real Phase 2 implementation, the
    # tenant_id would be used to select the correct Temporal Namespace client.
    async def get_by_id(self, case_id: str, tenant_id: str) -> Optional[Case]:
        """
        Retrieves a single case by its ID. It first tries to query a running
        workflow. If that fails because the workflow is not found (e.g., it has
        already completed), it attempts to fetch the final result from history.
        """
        print(f"[Core Service] Getting handle for case '{case_id}' in tenant '{tenant_id}'")
        handle = self.client.get_workflow_handle(case_id)
        try:
            # First, try to query the running workflow.
            print(f"[Core Service] Attempting to query active workflow: {case_id}")
            result_dict = await handle.query("get_current_state")

            if result_dict:
                try:
                    # The pydantic_data_converter should return a Case object,
                    # but we defensively validate it here.
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

    # New method to handle submitting a decision, now tenant-aware.
    async def submit_decision(self, case_id: str, decision: str, tenant_id: str) -> Dict[str, Any]:
        """
        Sends a signal to a running workflow case.
        """
        print(f"[Core Service] Submitting decision '{decision}' for case '{case_id}' in tenant '{tenant_id}'")
        try:
            handle = self.client.get_workflow_handle(case_id)
            await handle.signal("decision", decision)
            return {
                "caseId": case_id,
                "status": "Signal Sent",
                "message": f"Decision '{decision}' was successfully sent to the case.",
            }
        except RPCError as e:
            # Re-raise RPC errors to be handled by the API layer, which can
            # return appropriate HTTP status codes.
            print(f"[Core Service] ERROR: RPC error signaling case {case_id}: {e.message}")
            raise
