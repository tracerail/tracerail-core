"""
TraceRail Core SDK

A production-ready library for AI workflow systems with human-in-the-loop task management.
Built on Temporal for reliability and scalability.

Example usage:
    import tracerail

    # Simple usage
    client = tracerail.create_client()
    result = await client.process_content("Analyze this document...")

    # Advanced usage with a custom workflow
    class MyWorkflow(tracerail.BaseAIWorkflow):
        async def run(self, input_data):
            llm_result = await self.process_with_llm(input_data)
            if self.routing_says_human(llm_result):
                return await self.wait_for_human_decision(llm_result)
            return llm_result
"""

# --- Metadata ---
__version__ = "1.0.0-alpha.1"
__author__ = "TraceRail Team <team@tracerail.io>"
__description__ = "Core SDK for AI workflow systems with human-in-the-loop task management"
__url__ = "https://github.com/tracerail/tracerail-core"


# --- Core Client and Configuration ---
# Note: These imports will fail until all modules are created.
from .client import TraceRail, create_client, create_client_async
from .config import TraceRailConfig

# --- Core Exceptions ---
from .exceptions import (
    TraceRailException,
    TraceRailError,
    ConfigurationError,
    LLMError,
    RoutingError,
    TaskError,
)

# --- LLM Module ---
from .llm import (
    BaseLLMProvider,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMMessage,
    LLMUsage,
    LLMCapabilities,
    create_llm_provider,
)

# --- Routing Module ---
from .routing import (
    BaseRoutingEngine,
    RoutingContext,
    RoutingResult,
    RoutingDecision,
    create_routing_engine,
)

# --- Task Management Module ---
from .tasks import (
    BaseTaskManager,
    TaskData,
    TaskResult,
    TaskStatus,
    TaskPriority,
    create_task_manager,
)

# --- Temporal Integration ---
from .temporal import BaseAIWorkflow, TemporalWorkflowError, ActivityError


# --- Public API Definition (`__all__`) ---
__all__ = [
    # Metadata
    "__version__",
    "get_version",

    # Main Client & Config
    "TraceRail",
    "create_client",
    "create_client_async",
    "TraceRailConfig",

    # Core Exceptions
    "TraceRailException",
    "TraceRailError",
    "ConfigurationError",
    "LLMError",
    "RoutingError",
    "TaskError",

    # LLM Components
    "BaseLLMProvider",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "LLMMessage",
    "LLMUsage",
    "LLMCapabilities",
    "create_llm_provider",

    # Routing Components
    "BaseRoutingEngine",
    "RoutingContext",
    "RoutingResult",
    "RoutingDecision",
    "create_routing_engine",

    # Task Components
    "BaseTaskManager",
    "TaskData",
    "TaskResult",
    "TaskStatus",
    "TaskPriority",
    "create_task_manager",

    # Temporal Components
    "BaseAIWorkflow",
    "TemporalWorkflowError",
    "ActivityError",
]

# --- Convenience Functions ---

def get_version():
    """Return the current version of the TraceRail Core SDK."""
    return __version__
