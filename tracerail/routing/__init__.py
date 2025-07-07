"""
TraceRail Routing Module

This package contains the components for intelligent routing of content
based on LLM outputs, business rules, and other contextual information.
"""

# Import key data models and base classes for easier access
from .base import (
    BaseRoutingEngine,
    RoutingContext,
    RoutingResult,
    RoutingDecision,
    RoutingRule,
    RoutingRuleType,
    RoutingPriority,
)

# Import factory functions
from .factory import create_routing_engine

# Import exceptions for convenience
from ..exceptions import RoutingError


__all__ = [
    # Base Classes
    "BaseRoutingEngine",
    # Core Models
    "RoutingContext",
    "RoutingResult",
    "RoutingDecision",
    "RoutingRule",
    "RoutingRuleType",
    "RoutingPriority",
    # Factory Functions
    "create_routing_engine",
    # Exceptions
    "RoutingError",
]
