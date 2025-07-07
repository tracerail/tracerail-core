"""
TraceRail Task Notification Services

This package contains implementations of the `BaseNotificationService`.
These services are responsible for sending notifications to users or systems
based on task events, such as assignment, completion, or escalation.
"""

from .logging_service import LoggingNotificationService
from ..models import Notification
from ..factory import create_notification_service

__all__ = ["LoggingNotificationService", "Notification", "create_notification_service"]
