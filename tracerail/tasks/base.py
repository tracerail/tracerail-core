"""
TraceRail Task Management Base Interfaces

This module defines the fundamental abstract base classes (ABCs) for the
task management system in the TraceRail Core SDK. These interfaces provide
a contract for concrete implementations of task managers, assignment strategies,
SLA managers, escalation policies, and notification services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import (
    TaskData,
    TaskResult,
    TaskStatus,
    EscalationAction,
    Notification,
)


class BaseTaskManager(ABC):
    """
    Abstract base class for all task managers.

    A task manager is responsible for the full lifecycle of tasks, including
    creation, retrieval, updates, and deletion. It serves as the central
    component for interacting with a task storage backend (e.g., in-memory,
    database, or a third-party service).
    """

    def __init__(self, manager_name: str, **kwargs: Any):
        self.manager_name = manager_name
        self.config = kwargs
        self.is_initialized = False
        self.assignment_strategy: Optional[BaseAssignmentStrategy] = None
        self.sla_manager: Optional[BaseSLAManager] = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initializes the task manager and its dependencies."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cleans up resources used by the task manager."""
        pass

    @abstractmethod
    async def create_task(self, task_data: TaskData) -> TaskResult:
        """
        Creates a new task in the storage backend.

        Args:
            task_data: The data for the task to be created.

        Returns:
            The created task, including its unique ID and status.
        """
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[TaskResult]:
        """
        Retrieves a single task by its unique ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            The task result if found, otherwise None.
        """
        pass

    @abstractmethod
    async def update_task(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Optional[TaskResult]:
        """
        Updates an existing task.

        Args:
            task_id: The ID of the task to update.
            updates: A dictionary of fields to update.

        Returns:
            The updated task result, or None if the task was not found.
        """
        pass

    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """
        Deletes a task from the system.

        Args:
            task_id: The ID of the task to delete.

        Returns:
            True if the task was deleted successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def get_tasks_by_user(
        self, user_id: str, status: Optional[TaskStatus] = None, limit: int = 50
    ) -> List[TaskResult]:
        """
        Retrieves a list of tasks assigned to a specific user.

        Args:
            user_id: The ID of the user.
            status: Optional filter to get tasks with a specific status.
            limit: The maximum number of tasks to return.

        Returns:
            A list of tasks assigned to the user.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Performs a health check on the task manager and its dependencies.

        Returns:
            A dictionary with the health status and details.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(manager_name='{self.manager_name}')>"


class BaseAssignmentStrategy(ABC):
    """
    Abstract base class for task assignment strategies.

    An assignment strategy encapsulates the logic for deciding which user or
    group should be assigned a new task.
    """

    def __init__(self, strategy_name: str, **kwargs: Any):
        self.strategy_name = strategy_name
        self.config = kwargs

    @abstractmethod
    async def assign_task(self, task: TaskData, candidates: List[str]) -> Optional[str]:
        """
        Determines the assignee for a given task.

        Args:
            task: The task to be assigned.
            candidates: A list of potential user or group IDs.

        Returns:
            The ID of the chosen assignee, or None if no suitable assignee is found.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(strategy_name='{self.strategy_name}')>"


class BaseSLAManager(ABC):
    """
    Abstract base class for Service Level Agreement (SLA) managers.
    """

    def __init__(self, manager_name: str, **kwargs: Any):
        self.manager_name = manager_name
        self.config = kwargs

    @abstractmethod
    def start_tracking_task(self, task: TaskResult) -> None:
        """Starts tracking a task for SLA compliance."""
        pass

    @abstractmethod
    def stop_tracking_task(self, task_id: str) -> None:
        """Stops tracking a task, e.g., upon completion."""
        pass

    @abstractmethod
    async def check_sla_violations(self) -> List[TaskResult]:
        """
        Checks all tracked tasks for SLA violations.

        Returns:
            A list of tasks that have violated their SLA.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(manager_name='{self.manager_name}')>"


class BaseEscalationPolicy(ABC):
    """
    Abstract base class for task escalation policies.

    An escalation policy defines what happens when a task breaches an SLA or
    is otherwise marked for escalation.
    """

    def __init__(self, policy_name: str, **kwargs: Any):
        self.policy_name = policy_name
        self.config = kwargs

    @abstractmethod
    async def determine_escalation(self, task: TaskResult) -> EscalationAction:
        """
        Determines the appropriate escalation action for a given task.

        Args:
            task: The task that requires an escalation decision.

        Returns:
            An EscalationAction object detailing the steps to take.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(policy_name='{self.policy_name}')>"


class BaseNotificationService(ABC):
    """
    Abstract base class for notification services.
    """

    def __init__(self, service_name: str, **kwargs: Any):
        self.service_name = service_name
        self.config = kwargs

    @abstractmethod
    async def send(self, notification: Notification) -> None:
        """
        Sends a notification.

        Args:
            notification: The notification object to be sent.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(service_name='{self.service_name}')>"
