"""Configuration dataclasses for adapter components."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseEngineConfig:
    """Base configuration for engines.

    Attributes:
        timeout: Operation timeout in seconds
    """

    timeout: float = 30.0


@dataclass
class SocketEngineConfig(BaseEngineConfig):
    """Configuration for socket-based engines (FreeCAD, Blender).

    Used when the CAD application runs a TCP socket server that the
    adapter connects to.

    Attributes:
        host: Socket server hostname
        port: Socket server port
        recv_buffer_size: Size of receive buffer in bytes
        timeout: Operation timeout in seconds (inherited)

    Example:
        >>> config = SocketEngineConfig(host="localhost", port=9876)
        >>> config.timeout
        30.0
    """

    host: str = "localhost"
    port: int = 9876
    recv_buffer_size: int = 8192


@dataclass
class ServerClientConfig:
    """Configuration for WebSocket server client connections.

    Used when the adapter connects to the hosted Conjure server for
    cloud-based operation routing.

    Attributes:
        server_url: WebSocket URL of the Conjure server
        api_key: API key for authentication
        adapter_id: Unique identifier for this adapter instance
        adapter_type: Type identifier (e.g., "freecad", "blender", "kicad")
        reconnect_delay: Delay between reconnection attempts in seconds
        max_reconnect_attempts: Maximum number of reconnection attempts
        heartbeat_interval: Interval between heartbeat messages in seconds

    Example:
        >>> config = ServerClientConfig(
        ...     server_url="wss://conjure.lautrek.com/api/v1/adapter/ws",
        ...     api_key="sk_test_123",
        ...     adapter_type="freecad"
        ... )
    """

    server_url: str = "wss://conjure.lautrek.com/api/v1/adapter/ws"
    api_key: Optional[str] = None
    adapter_id: Optional[str] = None
    adapter_type: str = "generic"
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 10
    heartbeat_interval: float = 30.0
