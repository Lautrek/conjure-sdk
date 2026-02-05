"""Base engine class for transport abstraction."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from .config import BaseEngineConfig

logger = logging.getLogger(__name__)


class BaseEngine(ABC):
    """Abstract base class for Conjure transport engines.

    Engines handle the transport layer - how commands get to the CAD application.
    Subclasses implement specific transports: socket, HTTP, IPC, etc.

    Example:
        >>> class SocketEngine(BaseEngine):
        ...     def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        ...         # Send command via socket
        ...         return {"success": True}
        ...
        ...     def health_check(self) -> bool:
        ...         # Check socket connection
        ...         return True
    """

    def __init__(self, config: BaseEngineConfig = None):
        """Initialize the engine.

        Args:
            config: Engine configuration (defaults to BaseEngineConfig)
        """
        self.config = config or BaseEngineConfig()

    @abstractmethod
    def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command and return the response.

        Args:
            command: Command dict with at minimum a 'type' key

        Returns:
            Response dict from the CAD application

        Raises:
            ConnectionError: If unable to communicate with the CAD application
            TimeoutError: If the operation times out

        Example:
            >>> command = {"type": "create_box", "params": {"width": 10}}
            >>> response = engine.execute(command)
            >>> response["success"]
            True
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the engine can communicate with its target.

        Returns:
            True if the target is reachable, False otherwise

        Example:
            >>> if engine.health_check():
            ...     print("Engine is ready")
        """
        ...

    def get_state(self, verbose: bool = False) -> Dict[str, Any]:
        """Get document state. Default implementation via execute().

        Args:
            verbose: Whether to include detailed state information

        Returns:
            Dictionary with document state

        Example:
            >>> state = engine.get_state(verbose=True)
            >>> state.get("objects", [])
            [{'name': 'Box001', 'type': 'Part::Box'}]
        """
        return self.execute({"type": "get_state", "params": {"verbose": verbose}})
