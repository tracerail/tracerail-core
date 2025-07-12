"""
This module defines the FlexibleCaseWorkflow, a generic workflow that can
execute any business process defined by a versioned Process Definition.
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict

from temporalio import activity, workflow

# Import the domain models we'll be using
from tracerail.domain.cases import ActivityStreamItem, Case, ActiveInteraction

# Import the activity definitions that this workflow can call.
# While they are not directly referenced, this ensures the worker is aware of them.
from tracerail.activities import case_activities, process_activities


@workflow.defn
class FlexibleCaseWorkflow:
    """
    A generic process engine workflow that executes steps based on a declarative
    process definition document.
    """

    def __init__(self) -> None:
        self._case_state: Case = None
        self._last_signal: str = None
        self._process_definition: Dict[str, Any] = None

    @workflow.signal
    def decision(self, choice: str) -> None:
        """Signal handler for receiving a decision from an agent."""
        self._last_signal = choice

    @workflow.run
    async def run(self, process_name: str, process_version: str, initial_payload: Dict[str, Any]) -> Case:
        """The main entry point for the process engine."""
        workflow.logger.info("Starting new process engine workflow", process_name=process_name, version=process_version)

        # Load the process definition via an activity
        self._process_definition = await workflow.execute_activity(
            "load_process_definition_activity",
            args=[process_name, process_version],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Initialize the case state
        self._initialize_case_state(initial_payload)

        current_step_id = self._process_definition["initial_step"]

        # Main process engine loop
        while current_step_id:
            workflow.logger.info("Executing step", step_id=current_step_id)
            current_step_config = self._get_step_config(current_step_id)
            step_type = current_step_config["step_type"]

            if step_type == "human_in_the_loop":
                await self._execute_human_in_the_loop_step(current_step_config)
                # After waiting, determine the next step based on the signal.
                transition = self._find_transition(current_step_config, self._last_signal)
                current_step_id = transition.get("next_step")

            elif step_type == "final_commit":
                self._execute_final_commit_step(current_step_config)
                current_step_id = None # End the loop

            else:
                raise ValueError(f"Unknown step type: {step_type}")

        return self._case_state

    def _initialize_case_state(self, initial_payload: Dict[str, Any]):
        """Builds the initial Case object."""
        now = workflow.now()
        case_id = workflow.info().workflow_id
        title = f"Expense from {initial_payload.get('submitter_name', 'N/A')}"

        self._case_state = Case(
            caseDetails={
                "caseId": case_id,
                "caseTitle": title,
                "status": "Processing",
                "assignee": {"name": "System", "email": "system@tracerail.io"},
                "submitter": {
                    "name": initial_payload.get("submitter_name"),
                    "email": initial_payload.get("submitter_email"),
                },
                "createdAt": now,
                "updatedAt": now,
                "caseData": {
                    "amount": initial_payload.get("amount", 0.0),
                    "currency": initial_payload.get("currency", "USD"),
                    "category": initial_payload.get("category", "Uncategorized"),
                    "ai_summary": "N/A",
                    "ai_policy_check": "N/A",
                    "ai_risk_score": "N/A",
                },
            },
            activityStream=[
                ActivityStreamItem(
                    id=1,
                    type="system_event",
                    sender="System",
                    text=f"Case created by {initial_payload.get('submitter_name')}.",
                    timestamp=now,
                )
            ],
            activeInteraction=None,
        )

    async def _execute_human_in_the_loop_step(self, step_config: Dict[str, Any]):
        """Handles a 'human_in_the_loop' step."""
        self._last_signal = None # Reset signal at the start of the step
        interaction_config = step_config["configuration"]

        self._case_state.activeInteraction = ActiveInteraction(
            interactionId=f"interaction_{workflow.info().workflow_id}",
            interactionType="action_buttons",
            prompt=interaction_config["prompt"],
            payload={"actions": interaction_config["actions"]},
            submitUrl=f"/api/v1/cases/{self._case_state.caseDetails.caseId}/decision",
        )
        self._case_state.caseDetails.status = "Pending Human Review"

        await workflow.wait_condition(lambda: self._last_signal is not None)

        # Add a record of the decision to the activity stream
        new_activity = ActivityStreamItem(
            id=len(self._case_state.activityStream) + 1,
            type="agent_decision",
            sender="Agent",
            text=f"Decision submitted: {self._last_signal}",
            timestamp=workflow.now(),
        )
        self._case_state.activityStream.append(new_activity)
        self._case_state.activeInteraction = None

    def _execute_final_commit_step(self, step_config: Dict[str, Any]):
        """Handles a 'final_commit' step."""
        final_status = step_config["configuration"]["final_status"]
        self._case_state.caseDetails.status = final_status
        self._case_state.caseDetails.updatedAt = workflow.now()

    def _get_step_config(self, step_id: str) -> Dict[str, Any]:
        """Finds a step's configuration by its ID."""
        # The steps in our process definition are a list of dictionaries.
        for step in self._process_definition["steps"]:
            if step["step_id"] == step_id:
                return step
        raise ValueError(f"Step with ID '{step_id}' not found in process definition.")

    def _find_transition(self, current_step_config: Dict[str, Any], signal_value: str) -> Dict[str, Any]:
        """Finds the correct transition to the next step based on the signal received."""
        for transition in current_step_config.get("transitions", []):
            if transition.get("on_signal") == signal_value:
                return transition
        # If no specific signal transition is found, check for a default transition
        for transition in current_step_config.get("transitions", []):
            if transition.get("on_signal") is None:
                return transition
        raise ValueError(
            f"No transition found for signal '{signal_value}' on step '{current_step_config['step_id']}'"
        )

    @workflow.query(name="get_current_state")
    def get_current_state(self) -> Case:
        """
        A query method that allows external clients to get the complete,
        up-to-the-minute state of the case.

        Returns:
            The full Case object, including details, activity stream, and the
            active interaction required from the agent.
        """
        return self._case_state
