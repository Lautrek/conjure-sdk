"""Base adapter class for all Conjure CAD clients."""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from .result import AdapterResult

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Abstract base class for Conjure CAD adapters.

    Provides unified command dispatch with support for both sync and async handlers.

    Subclasses can register handlers in two ways:
    1. Explicit: call register_handler(command_type, handler_func)
    2. By prefix: call register_handlers_by_prefix("_cmd_") to auto-discover methods

    The execute() method handles both sync and async handlers transparently.

    Example:
        >>> class MyAdapter(BaseAdapter):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.register_handlers_by_prefix("_cmd_")
        ...
        ...     def _cmd_create_box(self, params: Dict) -> AdapterResult:
        ...         width = params.get("width", 1.0)
        ...         return AdapterResult.ok(object_id="Box001", width=width)
        ...
        ...     def health_check(self) -> bool:
        ...         return True
        ...
        ...     def get_capabilities(self) -> List[str]:
        ...         return ["primitives"]
        ...
        >>> adapter = MyAdapter()
        >>> result = asyncio.run(adapter.execute("create_box", {"width": 10.0}))
        >>> result.success
        True
    """

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register_handler(self, command_type: str, handler: Callable) -> None:
        """Register a handler for a command type.

        Args:
            command_type: The command identifier (e.g., "create_box")
            handler: Callable that takes params dict and returns AdapterResult or dict

        Example:
            >>> def my_handler(params):
            ...     return AdapterResult.ok(value=42)
            >>> adapter.register_handler("my_command", my_handler)
        """
        self._handlers[command_type] = handler

    def register_handlers_by_prefix(self, prefix: str = "_cmd_") -> None:
        """Auto-discover and register handlers by method name prefix.

        Methods named {prefix}{command_type} are registered for {command_type}.
        E.g., _cmd_create_cube -> "create_cube"

        Args:
            prefix: Method name prefix to search for (default: "_cmd_")

        Example:
            >>> class MyAdapter(BaseAdapter):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self.register_handlers_by_prefix("_cmd_")
            ...
            ...     def _cmd_create_box(self, params):
            ...         return AdapterResult.ok()
        """
        prefix_len = len(prefix)
        for name in dir(self):
            if name.startswith(prefix):
                cmd_type = name[prefix_len:]
                handler = getattr(self, name)
                if callable(handler):
                    self._handlers[cmd_type] = handler
                    logger.debug(f"Registered handler: {cmd_type} -> {name}")

    async def execute(self, command_type: str, params: Dict[str, Any]) -> AdapterResult:
        """Execute a command by type.

        Dispatches to the registered handler. Supports both sync and async handlers.
        Returns AdapterResult. If handler returns a dict, wraps it in AdapterResult.ok().

        Args:
            command_type: The command to execute
            params: Parameters for the command

        Returns:
            AdapterResult with success status and data

        Example:
            >>> result = await adapter.execute("create_box", {"width": 10})
            >>> if result.success:
            ...     print(f"Created: {result.data['object_id']}")
        """
        handler = self._handlers.get(command_type)
        if handler is None:
            logger.warning(f"Unknown command: {command_type}")
            return AdapterResult.fail(f"Unknown command: {command_type}")

        try:
            # Handle both async and sync handlers
            if inspect.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)

            # Allow handlers to return AdapterResult directly or a dict
            if isinstance(result, AdapterResult):
                return result
            if isinstance(result, dict):
                # Check for error status in dict (legacy support)
                if result.get("status") == "error":
                    return AdapterResult.fail(result.get("error", "Unknown error"))
                return AdapterResult(success=True, data=result)
            # No return value means success with no data
            return AdapterResult.ok()
        except Exception as e:
            logger.exception(f"Handler error for {command_type}")
            return AdapterResult.fail(str(e))

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the underlying CAD application is available.

        Returns:
            True if the CAD application is responsive, False otherwise

        Example:
            >>> if adapter.health_check():
            ...     print("CAD application is running")
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of supported capability categories.

        Returns:
            List of capability identifiers (e.g., ["primitives", "booleans"])

        Example:
            >>> adapter.get_capabilities()
            ['primitives', 'booleans', 'transforms']
        """
        ...

    def get_supported_commands(self) -> List[str]:
        """Return list of registered command types.

        Returns:
            List of command type strings

        Example:
            >>> adapter.get_supported_commands()
            ['create_box', 'create_cylinder', 'boolean_union']
        """
        return list(self._handlers.keys())

    def get_registration_payload(self) -> Dict[str, Any]:
        """Build registration payload for server connection.

        This is used when the adapter connects to the hosted Conjure server
        to advertise its capabilities and supported commands.

        Returns:
            Dictionary with capabilities and commands

        Example:
            >>> payload = adapter.get_registration_payload()
            >>> payload.keys()
            dict_keys(['capabilities', 'commands'])
        """
        return {
            "capabilities": self.get_capabilities(),
            "commands": self.get_supported_commands(),
        }
