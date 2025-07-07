"""
TraceRail Task Policies

This package contains implementations of various policies that govern task
behavior, such as escalation policies, retry policies, or assignment policies
that are more complex than simple strategies.
"""

from .escalation import BasicEscalationPolicy, EscalationPolicy

__all__ = ["BasicEscalationPolicy", "EscalationPolicy"]
