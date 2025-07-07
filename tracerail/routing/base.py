"""
TraceRail Routing Base Interfaces and Models

This module defines the fundamental interfaces, abstract classes, and data
models for the content routing engine in the TraceRail Core SDK.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..llm.base import LLMResponse
from ..exceptions import RoutingError, ErrorCode


# --- Enums for Routing Logic ---

class RoutingDecision(str, Enum):
    """Enumeration of possible routing decisions."""
    AUTOMATIC = "automatic"      # Process automatically
    HUMAN = "human"              # Escalate to a human for review
    REJECT = "reject"            # Reject the content outright
    UNCERTAIN = "uncertain"      # Could not determine a clear path


class RoutingRuleType(str, Enum):
    """Enumeration of different types of routing rules."""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    KEYWORD_MATCH = "keyword_match"
    CONTENT_FILTER = "content_filter"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    COMPLEXITY_SCORE = "complexity_score"
    CUSTOM_LOGIC = "custom_logic"


class RoutingPriority(str, Enum):
    """Enumeration for the priority of a routing rule."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# --- Data Models for Routing ---

@dataclass
class RoutingContext:
    """
    Contextual information provided to the routing engine to make a decision.
    """
    content: str
    llm_response: Optional[LLMResponse] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    user_roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the context to a dictionary."""
        return {
            "content": self.content,
            "llm_response": self.llm_response.to_dict() if self.llm_response else None,
            "metadata": self.metadata,
            "user_id": self.user_id,
            "user_roles": self.user_roles,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class RoutingRule:
    """
    Represents a single rule used by the routing engine.
    """
    name: str
    rule_type: RoutingRuleType
    decision: RoutingDecision
    priority: RoutingPriority = RoutingPriority.NORMAL
    condition: Union[str, Dict[str, Any]] = field(default_factory=dict)
    description: Optional[str] = None
    is_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the rule to a dictionary."""
        return {
            "name": self.name,
            "rule_type": self.rule_type.value,
            "decision": self.decision.value,
            "priority": self.priority.value,
            "condition": self.condition,
            "description": self.description,
            "is_enabled": self.is_enabled,
        }


@dataclass
class RoutingResult:
    """
    Encapsulates the outcome of a routing decision.
    """
    decision: RoutingDecision
    reason: str
    confidence: Optional[float] = None
    triggered_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None

    @property
    def requires_human(self) -> bool:
        """Convenience property to check if human review is needed."""
        return self.decision == RoutingDecision.HUMAN

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the result to a dictionary."""
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "confidence": self.confidence,
            "triggered_rules": self.triggered_rules,
            "metadata": self.metadata,
            "request_id": self.request_id,
        }


# --- Abstract Base Class for Routing Engines ---

class BaseRoutingEngine(ABC):
    """
    Abstract base class for all routing engines in TraceRail.
    """

    def __init__(self, engine_name: str, **kwargs: Any):
        """
        Initializes the base routing engine.

        Args:
            engine_name: The name of the routing engine implementation.
            **kwargs: Additional configuration parameters.
        """
        self.engine_name = engine_name
        self.config = kwargs
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Performs any necessary setup for the engine, such as loading rules
        from a file or connecting to a service.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Cleans up any resources used by the engine.
        """
        pass

    @abstractmethod
    async def route(self, context: RoutingContext) -> RoutingResult:
        """
        Processes a routing request based on the provided context.

        Args:
            context: The RoutingContext object containing all necessary
                     information for the decision.

        Returns:
            A RoutingResult object with the outcome of the routing logic.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Performs a health check on the routing engine and its dependencies.

        Returns:
            A dictionary with health status and details.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(engine_name='{self.engine_name}')>"
