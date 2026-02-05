"""Convenience runner for wiring adapter + server client."""

import logging
from typing import Optional

from .base_adapter import BaseAdapter
from .base_server_client import BaseServerClient
from .config import ServerClientConfig

logger = logging.getLogger(__name__)


class AdapterRunner:
    """Convenience class for running an adapter with a server client.

    Simplifies the common pattern of connecting an adapter to the hosted
    Conjure server and running the main event loop.

    Example:
        >>> adapter = MyAdapter()
        >>> runner = AdapterRunner(
        ...     adapter,
        ...     server_url="wss://conjure.lautrek.com/api/v1/adapter/ws",
        ...     api_key="sk_test_123",
        ...     adapter_type="freecad"
        ... )
        >>> asyncio.run(runner.run())
    """

    def __init__(
        self,
        adapter: BaseAdapter,
        server_url: str = "wss://conjure.lautrek.com/api/v1/adapter/ws",
        api_key: Optional[str] = None,
        adapter_type: str = "generic",
        adapter_id: Optional[str] = None,
    ):
        """Initialize the runner.

        Args:
            adapter: Adapter instance to connect to the server
            server_url: WebSocket URL of the Conjure server
            api_key: API key for authentication
            adapter_type: Type identifier (e.g., "freecad", "blender")
            adapter_id: Unique adapter instance ID (optional)
        """
        self.adapter = adapter
        self.config = ServerClientConfig(
            server_url=server_url,
            api_key=api_key,
            adapter_type=adapter_type,
            adapter_id=adapter_id,
        )
        self._client = _DefaultServerClient(self.config, adapter)

    async def run(self):
        """Run the adapter service.

        Connects to the server and processes messages until interrupted
        or max reconnection attempts are reached.

        Example:
            >>> async def main():
            ...     runner = AdapterRunner(adapter, api_key="sk_test_123")
            ...     await runner.run()
            >>> asyncio.run(main())
        """
        try:
            logger.info(f"Starting {self.config.adapter_type} adapter service")
            await self._client.run()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await self._client.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to the server."""
        return self._client.is_connected

    @property
    def state(self):
        """Get current connection state."""
        return self._client.state


class _DefaultServerClient(BaseServerClient):
    """Default server client implementation for AdapterRunner."""

    pass
