"""
TraceRail Task Escalation Policies

This module defines the policies that govern what happens when a task
breaches its Service Level Agreement (SLA) or otherwise requires escalation.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..base import BaseEscalationPolicy
from ..models import EscalationAction, Notification, TaskResult, TaskPriority


class EscalationPolicy(BaseEscalationPolicy, ABC):
    """
    Abstract base class for escalation policies. This is a concrete type of
    BaseEscalationPolicy for direct use, but still requires implementation.
    """
    pass


class BasicEscalationPolicy(EscalationPolicy):
    """
    A basic escalation policy with a predefined set of actions.

    This policy escalates a task by:
    - Reassigning it to a default user or role (e.g., 'manager').
    - Increasing its priority to 'HIGH'.
    - Creating a notification to be sent to a default recipient.
    """

    def __init__(self, policy_name: str, **kwargs: Any):
        """
        Initializes the basic escalation policy.

        Args:
            policy_name: The name of the policy instance.
            **kwargs: Configuration dictionary. Can contain keys like
                      'default_assignee' and 'notification_recipient'.
        """
        super().__init__(policy_name, **kwargs)
        self.default_assignee = self.config.get("default_assignee", "manager")
        self.notification_recipient = self.config.get(
            "notification_recipient", "escalations@example.com"
        )

    async def determine_escalation(self, task: TaskResult) -> EscalationAction:
        """
        Determines the escalation action for the given task.

        Args:
            task: The task that has violated an SLA or requires escalation.

        Returns:
            An EscalationAction object detailing the steps to take.
        """
        notification = Notification(
            channel="email",
            recipient=self.notification_recipient,
            subject=f"SLA Violation: Task '{task.task_id}' requires attention",
            body=(
                f"The task '{task.data.title}' (ID: {task.task_id}) "
                f"has breached its SLA and has been escalated.\n"
                f"New Assignee: {self.default_assignee}\n"
                f"New Priority: {TaskPriority.HIGH.value}"
            ),
        )

        return EscalationAction(
            new_assignee=self.default_assignee,
            new_priority=TaskPriority.HIGH,
            notifications_to_send=[notification],
            reason="Task breached its Service Level Agreement (SLA).",
        )
