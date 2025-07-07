"""
In-Memory Task Manager for TraceRail

This module provides a simple, non-persistent implementation of the
`BaseTaskManager`. It stores all tasks in an in-memory dictionary, making it
suitable for development, testing, or simple single-process applications.

Note: All data will be lost when the application process terminates.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import BaseTaskManager
from ..models import TaskData, TaskResult, TaskStatus
from ..exceptions import TaskNotFoundError, DuplicateTaskError

logger = logging.getLogger(__name__)


class MemoryTaskManager(BaseTaskManager):
    """
    An in-memory implementation of the BaseTaskManager.
    """

    def __init__(self, manager_name: str, **kwargs: Any):
        """Initializes the in-memory task manager."""
        super().__init__(manager_name, **kwargs)
        self._tasks: Dict[str, TaskResult] = {}

    async def initialize(self) -> None:
        """Initializes the manager."""
        if self.is_initialized:
            logger.warning("MemoryTaskManager is already initialized.")
            return
        logger.info("Initializing MemoryTaskManager.")
        self.is_initialized = True

    async def close(self) -> None:
        """Clears the in-memory task store."""
        logger.info("Closing MemoryTaskManager and clearing all tasks.")
        self._tasks.clear()
        self.is_initialized = False

    async def create_task(self, task_data: TaskData) -> TaskResult:
        """
        Creates a new task and stores it in memory.

        Args:
            task_data: The data for the task to be created.

        Returns:
            The created task result.
        """
        if not self.is_initialized:
            raise RuntimeError("Task manager is not initialized.")

        task_id = str(uuid.uuid4())

        # In a real system, you might check for ID collisions, but it's highly unlikely.
        if task_id in self._tasks:
            raise DuplicateTaskError(f"Task ID collision for {task_id}", task_id=task_id)

        task = TaskResult(
            task_id=task_id,
            data=task_data,
            status=TaskStatus.OPEN,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Handle assignment if a strategy is attached
        if self.assignment_strategy and not task.data.assignee_id:
            # Assuming candidates might be passed in config or are static for this manager
            candidates = self.config.get("assignment_candidates", [])
            assignee = await self.assignment_strategy.assign_task(task.data, candidates)
            task.data.assignee_id = assignee
            logger.info(f"Task '{task_id}' assigned to '{assignee}' by '{self.assignment_strategy.strategy_name}'.")

        self._tasks[task_id] = task
        logger.info(f"Task '{task_id}' created successfully in memory.")

        # Start SLA tracking if a manager is attached
        if self.sla_manager:
            self.sla_manager.start_tracking_task(task)

        return task

    async def get_task(self, task_id: str) -> Optional[TaskResult]:
        """
        Retrieves a single task by its ID from memory.
        """
        logger.debug(f"Attempting to retrieve task '{task_id}'.")
        return self._tasks.get(task_id)

    async def update_task(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Optional[TaskResult]:
        """
        Updates an existing task in memory.
        """
        task = self._tasks.get(task_id)
        if not task:
            logger.warning(f"Attempted to update non-existent task '{task_id}'.")
            return None

        # Update fields in the nested TaskData model
        task_data_dict = task.data.model_dump()
        for key, value in updates.items():
            if key in task_data_dict:
                setattr(task.data, key, value)
            elif key == "status": # Handle status separately
                task.status = TaskStatus(value)

        task.updated_at = datetime.now()
        if task.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
            # Stop SLA tracking
            if self.sla_manager:
                self.sla_manager.stop_tracking_task(task_id)

        logger.info(f"Task '{task_id}' updated successfully.")
        return task

    async def delete_task(self, task_id: str) -> bool:
        """
        Deletes a task from memory.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info(f"Task '{task_id}' deleted from memory.")
            return True
        logger.warning(f"Attempted to delete non-existent task '{task_id}'.")
        return False

    async def get_tasks_by_user(
        self, user_id: str, status: Optional[TaskStatus] = None, limit: int = 50
    ) -> List[TaskResult]:
        """
        Retrieves a list of tasks assigned to a specific user.
        """
        user_tasks = []
        for task in self._tasks.values():
            if task.data.assignee_id == user_id:
                if status is None or task.status == status:
                    user_tasks.append(task)
            if len(user_tasks) >= limit:
                break
        return user_tasks

    async def health_check(self) -> Dict[str, Any]:
        """
        Performs a health check on the in-memory task manager.
        """
        return {
            "status": "healthy" if self.is_initialized else "unhealthy",
            "reason": "Manager is initialized" if self.is_initialized else "Manager not initialized",
            "task_count": len(self._tasks),
        }
