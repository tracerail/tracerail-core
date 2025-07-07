"""
TraceRail Task Management Factories

This module provides factory functions for creating instances of the various
components of the task management system, such as task managers, assignment
strategies, and more.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Generic, TypeVar

from ..config import TaskConfig
from .exceptions import TaskConfigurationError
from .base import (
    BaseTaskManager,
    BaseAssignmentStrategy,
    BaseSLAManager,
    BaseEscalationPolicy,
    BaseNotificationService,
)

logger = logging.getLogger(__name__)

# --- Generic Component Registry ---
T = TypeVar("T")

class ComponentRegistry(Generic[T]):
    """A generic registry for task management components."""

    def __init__(self, component_type: str):
        self._component_type = component_type
        self._registry: Dict[str, Type[T]] = {}
        logger.debug(f"{self._component_type} registry created.")

    def register(self, name: str, implementation_class: Type[T]):
        if name in self._registry:
            logger.warning(
                f"{self._component_type} '{name}' is already registered and will be overridden."
            )
        self._registry[name] = implementation_class
        logger.debug(f"Registered {self._component_type}: {name}")

    def get(self, name: str) -> Type[T]:
        if name not in self._registry:
            available = list(self._registry.keys())
            raise TaskConfigurationError(
                f"Unknown {self._component_type}: '{name}'. Available options: {available}"
            )
        return self._registry[name]

# --- Initialize Registries ---
task_manager_registry = ComponentRegistry[BaseTaskManager]("TaskManager")
assignment_strategy_registry = ComponentRegistry[BaseAssignmentStrategy]("AssignmentStrategy")
sla_manager_registry = ComponentRegistry[BaseSLAManager]("SLAManager")
escalation_policy_registry = ComponentRegistry[BaseEscalationPolicy]("EscalationPolicy")
notification_service_registry = ComponentRegistry[BaseNotificationService]("NotificationService")

# --- Registration Functions ---
def register_task_manager(name: str, cls: Type[BaseTaskManager]):
    task_manager_registry.register(name, cls)

def register_assignment_strategy(name: str, cls: Type[BaseAssignmentStrategy]):
    assignment_strategy_registry.register(name, cls)

def register_sla_manager(name: str, cls: Type[BaseSLAManager]):
    sla_manager_registry.register(name, cls)

def register_escalation_policy(name: str, cls: Type[BaseEscalationPolicy]):
    escalation_policy_registry.register(name, cls)

def register_notification_service(name: str, cls: Type[BaseNotificationService]):
    notification_service_registry.register(name, cls)

# --- Register Built-in Implementations ---
def _register_builtin_components():
    # Task Managers
    try:
        from .managers.memory import MemoryTaskManager
        register_task_manager("memory", MemoryTaskManager)
    except ImportError:
        logger.debug("MemoryTaskManager not available.")

    # Assignment Strategies
    try:
        from .strategies.round_robin import RoundRobinAssignmentStrategy
        register_assignment_strategy("round_robin", RoundRobinAssignmentStrategy)
    except ImportError:
        logger.debug("RoundRobinAssignmentStrategy not available.")

    # SLA Managers
    try:
        from .managers.sla import BasicSlaManager
        register_sla_manager("basic", BasicSlaManager)
    except ImportError:
        logger.debug("BasicSlaManager not available.")


    # Escalation Policies
    try:
        from .policies.escalation import BasicEscalationPolicy
        register_escalation_policy("basic", BasicEscalationPolicy)
    except ImportError:
        logger.debug("BasicEscalationPolicy not available.")


    # Notification Services
    try:
        from .notification.logging_service import LoggingNotificationService
        register_notification_service("logging", LoggingNotificationService)
        register_notification_service("basic", LoggingNotificationService) # Alias
    except ImportError:
        logger.debug("LoggingNotificationService not available.")


_register_builtin_components()

# --- Factory Functions ---

async def create_task_manager(config: TaskConfig) -> BaseTaskManager:
    """Creates and initializes a task manager instance from configuration."""
    logger.info(f"Creating task manager of type: {config.manager_type.value}")
    try:
        manager_class = task_manager_registry.get(config.manager_type.value)
        manager = manager_class(
            manager_name=config.manager_type.value, **config.manager_config
        )

        # Create and attach dependencies
        manager.assignment_strategy = await create_assignment_strategy(config)
        manager.sla_manager = await create_sla_manager(config)
        # manager.escalation_policy = await create_escalation_policy(config)
        # manager.notification_service = await create_notification_service(config)


        await manager.initialize()
        logger.info(f"Task manager '{config.manager_type.value}' initialized successfully.")
        return manager
    except Exception as e:
        logger.error(f"Failed to create task manager: {e}", exc_info=True)
        if isinstance(e, TaskConfigurationError):
            raise
        raise TaskConfigurationError(f"Failed to create task manager: {e}") from e

async def create_assignment_strategy(config: TaskConfig) -> BaseAssignmentStrategy:
    """Creates an assignment strategy instance from configuration."""
    strategy_name = config.assignment_strategy
    logger.debug(f"Creating assignment strategy: {strategy_name}")
    strategy_class = assignment_strategy_registry.get(strategy_name)
    return strategy_class(strategy_name=strategy_name, **config.assignment_config)

async def create_sla_manager(config: TaskConfig) -> BaseSLAManager:
    """Creates an SLA manager instance from configuration."""
    manager_name = config.sla_manager
    logger.debug(f"Creating SLA manager: {manager_name}")
    manager_class = sla_manager_registry.get(manager_name)
    return manager_class(manager_name=manager_name, **config.sla_config)

async def create_escalation_policy(config: TaskConfig) -> BaseEscalationPolicy:
    """Creates an escalation policy instance from configuration."""
    policy_name = config.escalation_policy
    logger.debug(f"Creating escalation policy: {policy_name}")
    policy_class = escalation_policy_registry.get(policy_name)
    return policy_class(policy_name=policy_name, **config.escalation_config)

async def create_notification_service(config: TaskConfig) -> BaseNotificationService:
    """Creates a notification service instance from configuration."""
    service_name = config.notification_service
    logger.debug(f"Creating notification service: {service_name}")
    service_class = notification_service_registry.get(service_name)
    return service_class(service_name=service_name, **config.notification_config)
