"""
TraceRail Routing Engine Factory

This module provides a factory function for creating routing engine instances.
It handles the instantiation and initialization of different routing engines
based on a provided configuration.
"""
import logging
from typing import Any, Dict, List, Optional, Type

from ..config import RoutingConfig, RoutingEngine as RoutingEngineEnum
from ..exceptions import RoutingError, ConfigurationError
from .base import BaseRoutingEngine

logger = logging.getLogger(__name__)


class RoutingEngineRegistry:
    """Registry for routing engine implementations."""

    def __init__(self):
        self._engines: Dict[str, Type[BaseRoutingEngine]] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, name: str, engine_class: Type[BaseRoutingEngine], aliases: Optional[List[str]] = None):
        """
        Register a routing engine implementation.

        Args:
            name: The name of the engine.
            engine_class: The class of the engine.
            aliases: A list of alternative names for the engine.
        """
        if name in self._engines:
            logger.warning(f"Routing engine '{name}' is already registered and will be overridden.")
        self._engines[name] = engine_class
        if aliases:
            for alias in aliases:
                self._aliases[alias] = name
        logger.debug(f"Registered routing engine: {name}")

    def get_engine_class(self, name: str) -> Type[BaseRoutingEngine]:
        """
        Get a routing engine class by its registered name or alias.

        Args:
            name: The name or alias of the engine.

        Returns:
            The engine class if found.

        Raises:
            ConfigurationError: If the engine is not registered.
        """
        resolved_name = self._aliases.get(name, name)
        engine_class = self._engines.get(resolved_name)
        if not engine_class:
            available = list(self._engines.keys())
            raise ConfigurationError(
                f"Unknown routing engine: '{name}'. Available engines: {available}"
            )
        return engine_class


_engine_registry = RoutingEngineRegistry()


def register_routing_engine(name: str, engine_class: Type[BaseRoutingEngine], aliases: Optional[List[str]] = None):
    """Registers a routing engine with the global registry."""
    _engine_registry.register(name, engine_class, aliases)


def _register_builtin_engines():
    """Dynamically registers the built-in routing engines."""
    try:
        # Assuming engines are located in an `engines` sub-package
        from .engines.rules_engine import RulesBasedRoutingEngine
        register_routing_engine(RoutingEngineEnum.RULES.value, RulesBasedRoutingEngine)
    except ImportError:
        logger.debug("RulesBasedRoutingEngine not available. Please ensure it is correctly installed.")
    try:
        from .engines.static_engine import StaticRoutingEngine
        register_routing_engine(RoutingEngineEnum.STATIC.value, StaticRoutingEngine)
    except ImportError:
        logger.debug("StaticRoutingEngine not available. Please ensure it is correctly installed.")

# Call at import time to populate the registry with default engines.
_register_builtin_engines()


async def create_routing_engine(config: RoutingConfig) -> BaseRoutingEngine:
    """
    Creates and initializes a routing engine instance from configuration.

    This factory function selects the appropriate engine class based on the
    `engine_type` in the configuration, instantiates it with engine-specific
    settings, and calls its `initialize` method.

    Args:
        config: The routing configuration object.

    Returns:
        An initialized routing engine instance ready for use.

    Raises:
        ConfigurationError: If the specified engine cannot be found,
                            instantiated, or initialized.
    """
    engine_name = config.engine_type.value
    logger.info(f"Creating routing engine of type: {engine_name}")

    try:
        engine_class = _engine_registry.get_engine_class(engine_name)

        # Pass engine-specific config directly to the constructor
        init_kwargs = {
            "engine_name": engine_name,
            **config.engine_config,
        }

        engine = engine_class(**init_kwargs)

        await engine.initialize()
        logger.info(f"Routing engine '{engine_name}' initialized successfully.")
        return engine

    except Exception as e:
        logger.error(f"Failed to create routing engine '{engine_name}': {e}", exc_info=True)
        # Don't re-wrap our own exceptions, just let them propagate.
        if isinstance(e, ConfigurationError):
            raise
        # Wrap other exceptions for consistent error handling.
        raise ConfigurationError(
            f"Failed to create '{engine_name}' routing engine: {e}"
        ) from e
