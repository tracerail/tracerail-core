"""
Logging-Based Notification Service for TraceRail

This module provides a simple, logging-based implementation of the
`BaseNotificationService`. Instead of sending real notifications (e.g., emails
or Slack messages), this service simply logs the notification content. It is
highly useful for development and testing environments where you want to verify
that notifications are being triggered without setting up actual delivery systems.
"""

import logging
from typing import Any

from ..base import BaseNotificationService
from ..models import Notification

# Get a logger for this module
logger = logging.getLogger(__name__)


class LoggingNotificationService(BaseNotificationService):
    """
    A notification service that logs notifications instead of sending them.

    This service is the default implementation and is used for development
    and testing. It logs the details of each notification to the standard
    logging output at the INFO level.
    """

    def __init__(self, service_name: str, **kwargs: Any):
        """
        Initializes the logging notification service.

        Args:
            service_name: The name of the service instance.
            **kwargs: Additional configuration parameters (ignored by this service).
        """
        super().__init__(service_name, **kwargs)
        logger.info(f"LoggingNotificationService '{self.service_name}' initialized.")

    async def send(self, notification: Notification) -> None:
        """
        "Sends" a notification by logging its contents.

        Args:
            notification: The Notification object containing the details to be logged.
        """
        log_message = (
            f"--- NOTIFICATION ---"
            f"\nChannel:   {notification.channel}"
            f"\nRecipient: {notification.recipient}"
            f"\nSubject:   {notification.subject}"
            f"\nBody:      {notification.body}"
        )
        if notification.metadata:
            log_message += f"\nMetadata:  {notification.metadata}"

        # Log the formatted message
        logger.info(log_message)
