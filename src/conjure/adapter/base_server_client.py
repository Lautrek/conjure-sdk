"""Base WebSocket server client for cloud bridge connections."""

import asyncio
import json
import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional

from .config import ServerClientConfig

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """Client connection state.

    Attributes:
        DISCONNECTED: Not connected to server
        CONNECTING: Attempting initial connection
        CONNECTED: Connected and registered
        RECONNECTING: Attempting to reconnect after disconnect
    """

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class BaseServerClient:
    """WebSocket client that connects to the hosted Conjure server.

    Handles:
    - Connection lifecycle with auto-reconnect
    - Adapter registration protocol
    - Command routing (server -> adapter -> result -> server)
    - Heartbeat keep-alive

    Requires the `websockets` package.

    Example:
        >>> config = ServerClientConfig(
        ...     server_url="wss://conjure.lautrek.com/api/v1/adapter/ws",
        ...     api_key="sk_test_123",
        ...     adapter_type="freecad"
        ... )
        >>> client = BaseServerClient(config, adapter=my_adapter)
        >>> await client.run()
    """

    def __init__(self, config: ServerClientConfig, adapter=None):
        """Initialize the server client.

        Args:
            config: Server connection configuration
            adapter: Adapter instance to route commands to
        """
        self.config = config
        self.adapter = adapter
        self._ws = None
        self._state = ConnectionState.DISCONNECTED
        self._reconnect_attempts = 0
        self._running = False
        self._message_handlers: Dict[str, Callable] = {}

        self._register_default_handlers()

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == ConnectionState.CONNECTED and self._ws is not None

    def _register_default_handlers(self):
        """Register default message handlers."""
        self._message_handlers = {
            "execute_command": self._handle_execute_command,
            "health_check": self._handle_health_check,
            "disconnect": self._handle_disconnect,
        }

    async def connect(self) -> bool:
        """Connect to the hosted server.

        Returns:
            True if connection succeeded, False otherwise

        Raises:
            ImportError: If websockets package is not installed
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required: pip install conjure-sdk[adapter]")

        if self.is_connected:
            return True

        self._state = ConnectionState.CONNECTING

        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._ws = await websockets.connect(
                self.config.server_url,
                extra_headers=headers,
                ping_interval=self.config.heartbeat_interval,
            )

            await self._register()
            self._state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            logger.info(f"Connected to server: {self.config.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._state = ConnectionState.DISCONNECTED
            return False

    async def _register(self):
        """Send adapter registration to server."""
        registration = {
            "type": "adapter_registration",
            "adapter_id": self.config.adapter_id,
            "adapter_type": self.config.adapter_type,
            "version": "1.0.0",
        }
        if self.adapter:
            registration.update(self.adapter.get_registration_payload())
        await self._send(registration)
        logger.info(f"Registered as {self.config.adapter_type} adapter")

    async def disconnect(self):
        """Disconnect from server."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        self._state = ConnectionState.DISCONNECTED
        logger.info("Disconnected from server")

    async def run(self):
        """Main loop - connect and process messages with auto-reconnect.

        This is the primary entry point for running the client. It handles:
        - Initial connection
        - Auto-reconnection on disconnect
        - Message processing
        - Graceful shutdown

        Example:
            >>> async def main():
            ...     client = BaseServerClient(config, adapter)
            ...     await client.run()
            >>> asyncio.run(main())
        """
        import websockets

        self._running = True
        while self._running:
            if not self.is_connected:
                connected = await self.connect()
                if not connected:
                    self._reconnect_attempts += 1
                    if self._reconnect_attempts > self.config.max_reconnect_attempts:
                        logger.error("Max reconnection attempts reached")
                        break
                    logger.warning(
                        f"Reconnection attempt {self._reconnect_attempts}/"
                        f"{self.config.max_reconnect_attempts} in {self.config.reconnect_delay}s"
                    )
                    await asyncio.sleep(self.config.reconnect_delay)
                    continue

            try:
                async for message in self._ws:
                    await self._handle_message(message)
            except websockets.ConnectionClosed:
                logger.warning("Connection closed by server")
                self._state = ConnectionState.RECONNECTING
                self._ws = None
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                self._state = ConnectionState.RECONNECTING
                await asyncio.sleep(1)

    async def _send(self, message: Dict[str, Any]):
        """Send message to server.

        Args:
            message: Message dict to send

        Raises:
            RuntimeError: If not connected
        """
        if not self._ws:
            raise RuntimeError("Not connected")
        await self._ws.send(json.dumps(message))

    async def _handle_message(self, raw: str):
        """Route incoming message to handler.

        Args:
            raw: Raw JSON message string
        """
        try:
            message = json.loads(raw)
            msg_type = message.get("type")
            handler = self._message_handlers.get(msg_type)
            if handler:
                response = await handler(message)
                if response:
                    await self._send(response)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON message")
        except Exception as e:
            logger.exception(f"Error handling message: {e}")

    async def _handle_execute_command(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle command execution request.

        Args:
            message: Message dict with command_type and params

        Returns:
            Response dict with command result
        """
        if not self.adapter:
            return {
                "type": "command_result",
                "request_id": message.get("request_id"),
                "success": False,
                "error": "No adapter configured",
            }

        result = await self.adapter.execute(
            message.get("command_type", ""),
            message.get("params", {}),
        )

        return {
            "type": "command_result",
            "request_id": message.get("request_id"),
            **result.to_wire(),
        }

    async def _handle_health_check(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check request.

        Args:
            message: Message dict with request_id

        Returns:
            Health check response
        """
        adapter_healthy = self.adapter.health_check() if self.adapter else False
        return {
            "type": "health_check_response",
            "request_id": message.get("request_id"),
            "adapter_healthy": adapter_healthy,
        }

    async def _handle_disconnect(self, message: Dict[str, Any]) -> None:
        """Handle server disconnect request.

        Args:
            message: Disconnect message

        Returns:
            None
        """
        logger.info("Server requested disconnect")
        await self.disconnect()
        return None
