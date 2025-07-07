"""
TraceRail Task Assignment Strategies

This package contains implementations of the `BaseAssignmentStrategy`.
These strategies define the logic for automatically assigning tasks to users
or groups based on various algorithms like round-robin, load balancing, or
skill matching.
"""

from .round_robin import RoundRobinAssignmentStrategy

__all__ = ["RoundRobinAssignmentStrategy"]
