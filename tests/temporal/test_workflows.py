import pytest
from unittest.mock import AsyncMock

from temporalio import workflow

from tracerail.config import TraceRailConfig
from tracerail.llm import LLMRequest, LLMResponse
from tracerail.routing import RoutingContext, RoutingDecision, RoutingResult
from tracerail.temporal.workflows import BaseAIWorkflow

# --- Test Setup ---

# A concrete workflow implementation is needed to test the abstract base class.
# This allows us to define a `run` method that calls the base class's
# helper methods (`process_with_llm`, `get_routing_decision`, etc.).
class ConcreteWorkflow(BaseAIWorkflow):
    """
    A simple, concrete implementation of BaseAIWorkflow for unit testing the
    orchestration logic provided by the base class.
    """

    @workflow.run
    async def run(self, text_input: str) -> dict:
        """
        Orchestrates a simple test flow:
        1. Calls the LLM activity wrapper from the base class.
        2. Calls the routing activity wrapper from the base class.
        3. Returns a result based on the routing decision.
        """
        # 1. Prepare requests for the base class methods
        llm_request = LLMRequest(content=text_input)

        # 2. Call the orchestration methods we want to test
        llm_response = await self.process_with_llm(llm_request)
        routing_context = RoutingContext(content=text_input, llm_response=llm_response)
        routing_result = await self.get_routing_decision(routing_context)

        # 3. Return a final result based on the outcome
        if routing_result.decision == RoutingDecision.HUMAN:
            # In a real workflow, this might be followed by a workflow.wait_for() call.
            # For this test, we just confirm the path was taken.
            return {"status": "HUMAN_REVIEW_REQUIRED", "reason": routing_result.reason}
        else:
            return {"status": "COMPLETED_AUTOMATICALLY", "reason": routing_result.reason}

# --- Test Class ---

@pytest.mark.asyncio
class TestBaseAIWorkflow:
    """
    Unit tests for the BaseAIWorkflow's orchestration logic.

    These tests mock the underlying Temporal `workflow.execute_activity` function
    to isolate and verify the workflow's internal logic without making real
    network calls or running actual activities.
    """

    @pytest.fixture(autouse=True)
    def mock_temporal_dependencies(self, mocker):
        """
        Automatically mock temporalio functions for all tests in this class.
        This prevents actual RPC calls and isolates the workflow logic for testing.
        """
        # We mock `execute_activity` as this is what the base class helper methods call internally.
        mocker.patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
        # Mock the logger to prevent errors if it's used inside the workflow.
        mocker.patch("temporalio.workflow.logger")

    async def test_workflow_follows_automatic_path(self, mocker):
        """
        Tests the workflow's execution path when the routing decision is AUTOMATIC.
        """
        # --- Arrange ---
        # Get the mock for the already-patched `execute_activity` function
        mocked_execute_activity = workflow.execute_activity

        # Configure the mock to return different values on consecutive calls.
        # First call (for llm_activity) returns an LLMResponse.
        # Second call (for routing_activity) returns an AUTOMATIC RoutingResult.
        mocked_execute_activity.side_effect = [
            LLMResponse(content="This is a simple response."),
            RoutingResult(decision=RoutingDecision.AUTOMATIC, reason="Default rule"),
        ]

        # Instantiate the workflow with a default config
        config = TraceRailConfig()
        workflow_instance = ConcreteWorkflow(config)

        # --- Act ---
        # Execute the workflow's run method
        result = await workflow_instance.run("A simple test case")

        # --- Assert ---
        # Verify the final status is correct for the automatic path
        assert result["status"] == "COMPLETED_AUTOMATICALLY"
        assert result["reason"] == "Default rule"
        # Verify that exactly two activities were called (LLM and routing)
        assert mocked_execute_activity.call_count == 2

    async def test_workflow_follows_human_path(self, mocker):
        """
        Tests the workflow's execution path when the routing decision is HUMAN.
        """
        # --- Arrange ---
        mocked_execute_activity = workflow.execute_activity

        # Configure the mock for the human-in-the-loop scenario.
        # The routing_activity now returns a HUMAN decision.
        mocked_execute_activity.side_effect = [
            LLMResponse(content="This response is complex and requires review."),
            RoutingResult(decision=RoutingDecision.HUMAN, reason="Low confidence score"),
        ]

        config = TraceRailConfig()
        workflow_instance = ConcreteWorkflow(config)

        # --- Act ---
        result = await workflow_instance.run("A complex test case")

        # --- Assert ---
        # Verify the final status reflects the need for human review
        assert result["status"] == "HUMAN_REVIEW_REQUIRED"
        assert result["reason"] == "Low confidence score"
        # Verify that the LLM and routing activities were still called
        assert mocked_execute_activity.call_count == 2
