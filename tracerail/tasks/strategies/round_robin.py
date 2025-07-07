"""
Round-Robin Task Assignment Strategy for TraceRail

This module provides a simple, stateful implementation of the `BaseAssignmentStrategy`
that assigns tasks to a list of candidates in a round-robin fashion.
"""

import logging
from typing import Any, List, Optional

from ..base import BaseAssignmentStrategy
from ..models import TaskData

logger = logging.getLogger(__name__)


class RoundRobinAssignmentStrategy(BaseAssignmentStrategy):
    """
    Assigns tasks to a list of candidates one by one in a looping sequence.

    This strategy maintains an internal counter to track the last assigned
    candidate index, ensuring that tasks are distributed evenly among the
    available candidates.

    Note: This in-memory implementation is not suitable for distributed or
    multi-worker environments, as each worker would have its own independent
    counter. For such scenarios, a distributed counter (e.g., using Redis or
    a database) would be required.
    """

    def __init__(self, strategy_name: str, **kwargs: Any):
        """
        Initializes the round-robin assignment strategy.

        Args:
            strategy_name: The name of the strategy instance.
            **kwargs: Additional configuration parameters (not used by this strategy).
        """
        super().__init__(strategy_name, **kwargs)
        self._current_index = 0
        logger.info(f"RoundRobinAssignmentStrategy '{self.strategy_name}' initialized.")

    async def assign_task(self, task: TaskData, candidates: List[str]) -> Optional[str]:
        """
        Determines the next assignee from the list of candidates in a round-robin manner.

        Args:
            task: The task to be assigned (not used in this simple strategy, but
                  available for more complex implementations).
            candidates: A list of potential user or group IDs to choose from.

        Returns:
            The ID of the next assignee in the sequence, or None if the candidate
            list is empty.
        """
        if not candidates:
            logger.warning("No candidates available for round-robin assignment.")
            return None

        # Ensure the index is within the bounds of the current candidate list
        if self._current_index >= len(candidates):
            self._current_index = 0

        # Select the next assignee
        assignee = candidates[self._current_index]
        logger.debug(f"Assigning task '{task.title}' to '{assignee}' using round-robin.")

        # Increment the index for the next assignment, wrapping around if necessary
        self._current_index = (self._current_index + 1) % len(candidates)

        return assignee
