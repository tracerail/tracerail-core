"""
TraceRail Core Library
======================

This is the central library for the TraceRail platform, containing the core
business logic, domain models, and workflow definitions.

This __init__.py file exposes the primary "public API" of the library,
allowing other services to import key components directly from the `tracerail`
package, simplifying development in consuming projects like the task bridge.

Example:
    from tracerail import CaseService, FlexibleCaseWorkflow
"""

# Expose the primary domain models and services from the `domain` module.
from .domain.cases import (
    Case,
    CaseDetails,
    CaseService,
    ActivityStreamItem,
    ActiveInteraction,
)

# Expose the primary workflow definition from the `workflows` module.
from .workflows.flexible_case_workflow import FlexibleCaseWorkflow

# Define the explicit public API of the 'tracerail' package.
# When a consumer runs `from tracerail import *`, only these names will be
# imported. This also serves as clear documentation for what parts of the
# library are intended for public use.
__all__ = [
    "Case",
    "CaseDetails",
    "CaseService",
    "ActivityStreamItem",
    "ActiveInteraction",
    "FlexibleCaseWorkflow",
]
