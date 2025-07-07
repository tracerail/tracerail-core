"""
Static Routing Engine for TraceRail

This module provides a simple implementation of the `BaseRoutingEngine`
that always returns a static, pre-configured routing decision. This is useful
for testing, development, or as a fallback engine.
"""

import logging
from typing import Any, Dict

from ..base import (
    BaseRoutingEngine,
    RoutingContext,
    RoutingDecision,
    RoutingResult,
)
from ...exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class StaticRoutingEngine(BaseRoutingEngine):
    """
    A routing engine that returns a fixed, pre-configured decision.

    This engine ignores the routing context and always returns the same
    `RoutingResult`. It is useful for simple workflows, testing, or as a
    default fallback when no other engine is suitable.

    Configuration in `engine_config`:
        - `decision` (str): The static decision to return (e.g., "human", "automatic").
        - `reason` (str): The static reason to provide for the decision.
    """

    def __init__(self, engine_name: str, **kwargs):
        """
        Initializes the static routing engine.

        Args:
            engine_name: The name of the engine instance.
            **kwargs: Configuration dictionary. Expects 'decision' and 'reason'.
        """
        super().__init__(engine_name, **kwargs)
        self.static_decision: RoutingDecision = RoutingDecision.HUMAN
        self.static_reason: str = "Default static routing configuration."

    async def initialize(self) -> None:
        """
        Initializes the engine by loading the static decision from config.
        """
        logger.info(f"Initializing StaticRoutingEngine '{self.engine_name}'.")

        decision_str = self.config.get("decision")
        if not decision_str:
            raise ConfigurationError(
                "StaticRoutingEngine requires a 'decision' in its configuration."
            )
        try:
            self.static_decision = RoutingDecision(decision_str)
        except ValueError:
            raise ConfigurationError(
                f"Invalid decision '{decision_str}' for StaticRoutingEngine. "
                f"Valid decisions are: {[d.value for d in RoutingDecision]}"
            )

        self.static_reason = self.config.get("reason", f"Static decision: {self.static_decision.value}")
        self.is_initialized = True
        logger.info(f"StaticRoutingEngine configured to always return '{self.static_decision.value}'.")

    async def close(self) -> None:
        """Closes the static routing engine."""
        logger.info(f"Closing StaticRoutingEngine '{self.engine_name}'.")
        self.is_initialized = False

    async def route(self, context: RoutingContext) -> RoutingResult:
        """
        Returns the pre-configured static routing decision, ignoring the context.

        Args:
            context: The routing context (ignored by this engine).

        Returns:
            A RoutingResult with the static decision.
        """
        if not self.is_initialized:
            raise ConfigurationError("StaticRoutingEngine is not initialized.")

        logger.debug(
            f"StaticRoutingEngine returning pre-configured decision: {self.static_decision.value}"
        )
        return RoutingResult(
            decision=self.static_decision,
            reason=self.static_reason,
            confidence=1.0,  # Confidence is absolute for a static rule
            triggered_rules=["static-rule"],
            request_id=context.llm_response.request_id if context.llm_response else None
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Performs a health check on the static routing engine.
        """
        return {
            "status": "healthy" if self.is_initialized else "unhealthy",
            "reason": "Engine is initialized" if self.is_initialized else "Engine not initialized",
            "configured_decision": self.static_decision.value if self.is_initialized else None,
        }
