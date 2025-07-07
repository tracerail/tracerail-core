"""
SLA (Service Level Agreement) Manager Implementation for TraceRail

This module provides a basic, in-memory implementation of the `BaseSLAManager`.
It is suitable for development and testing purposes where SLA tracking does not
need to be persistent.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..base import BaseSLAManager
from ..models import TaskResult

logger = logging.getLogger(__name__)


class BasicSlaManager(BaseSLAManager):
    """
    A basic, in-memory SLA manager.

    This implementation tracks tasks in a simple dictionary and is not
    suitable for production environments where state needs to be preserved
    across application restarts. It relies on being explicitly given tasks
    to track by a `BaseTaskManager`.
    """

    def __init__(self, manager_name: str, **kwargs: Any):
        """
        Initializes the basic SLA manager.

        Args:
            manager_name: The name of the SLA manager instance.
            **kwargs: Configuration for the manager. Expects 'default_sla_hours'.
        """
        super().__init__(manager_name=manager_name, **kwargs)
        # In-memory store for tasks being tracked
        self._tracked_tasks: Dict[str, TaskResult] = {}
        self.default_sla_hours = self.config.get('default_sla_hours', 24)
        logger.info(f"BasicSlaManager initialized with default SLA of {self.default_sla_hours} hours.")

    def start_tracking_task(self, task: TaskResult) -> None:
        """
        Adds a task to the manager for SLA tracking.

        This method is typically called by the main TaskManager when a task
        is created or enters a state where SLA monitoring is required.
        """
        if not task.data.due_date:
            task.data.due_date = self.calculate_sla_for_task(task)

        self._tracked_tasks[task.task_id] = task
        logger.debug(f"SLA Manager started tracking task '{task.task_id}' with due date {task.data.due_date}.")

    def stop_tracking_task(self, task_id: str) -> None:
        """
        Stops tracking a task, for example, when it is completed or cancelled.
        """
        if task_id in self._tracked_tasks:
            del self._tracked_tasks[task_id]
            logger.debug(f"SLA Manager stopped tracking task '{task_id}'.")

    def calculate_sla_for_task(self, task: TaskResult) -> datetime:
        """
        Calculates the SLA deadline for a given task based on its creation
        time and the default SLA in hours.
        """
        # If task has a specific due date set, respect it.
        if task.data.due_date:
            return task.data.due_date

        creation_time = task.created_at
        return creation_time + timedelta(hours=self.default_sla_hours)

    async def is_task_overdue(self, task: TaskResult) -> bool:
        """
        Checks if a single task is currently overdue.
        """
        due_date = task.data.due_date
        if not due_date:
            # If there's no due date, it can't be overdue.
            return False
        return datetime.now() > due_date

    async def check_sla_violations(self) -> List[TaskResult]:
        """
        Checks all tracked tasks for SLA violations.

        This method iterates through all tasks being monitored and returns a
        list of those that are currently overdue.

        Returns:
            A list of tasks that are currently overdue.
        """
        violated_tasks: List[TaskResult] = []
        # Iterate over a copy of the values to avoid issues if the dict changes during iteration
        for task in list(self._tracked_tasks.values()):
            if await self.is_task_overdue(task):
                logger.warning(f"SLA VIOLATION detected for task '{task.task_id}'.")
                violated_tasks.append(task)
        return violated_tasks

# Alias for convenience and backward compatibility.
SlaManager = BasicSlaManager
