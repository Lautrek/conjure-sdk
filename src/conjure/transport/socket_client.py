"""Socket client mixin for connecting to CAD application socket servers."""

import json
import logging
import socket
from typing import Any, Dict

logger = logging.getLogger(__name__)


class SocketClientMixin:
    """Mixin for engines that connect to a socket server (e.g., FreeCAD, Blender).

    Provides connect/send/receive over TCP sockets with newline-delimited JSON.
    This is the client-side pattern where the adapter connects TO the CAD application.

    The CAD application runs a TCP server (e.g., on port 9876), and this client
    connects to it to send commands and receive responses.

    Usage:
        >>> class MyEngine(SocketClientMixin, BaseEngine):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self._socket_host = "localhost"
        ...         self._socket_port = 9876
        ...
        ...     def execute(self, command):
        ...         return self.socket_execute(command)
        ...
        ...     def health_check(self):
        ...         return self.socket_health_check()

    Attributes:
        _socket_host: Server hostname (default: "localhost")
        _socket_port: Server port (default: 9876)
        _socket_timeout: Socket timeout in seconds (default: 30.0)
        _recv_buffer_size: Receive buffer size in bytes (default: 8192)
    """

    _socket_host: str = "localhost"
    _socket_port: int = 9876
    _socket_timeout: float = 30.0
    _recv_buffer_size: int = 8192

    def socket_connect(self) -> socket.socket:
        """Create and connect a TCP socket.

        Returns:
            Connected socket instance

        Raises:
            ConnectionError: If connection fails or times out

        Example:
            >>> sock = self.socket_connect()
            >>> sock.send(b"hello\\n")
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._socket_timeout)
            sock.connect((self._socket_host, self._socket_port))
            logger.debug(f"Connected to {self._socket_host}:{self._socket_port}")
            return sock
        except ConnectionRefusedError:
            raise ConnectionError(
                f"Cannot connect to {self._socket_host}:{self._socket_port} "
                f"(connection refused). Is the CAD application running?"
            )
        except socket.timeout:
            raise ConnectionError(
                f"Connection to {self._socket_host}:{self._socket_port} timed out after {self._socket_timeout}s"
            )

    def socket_send(self, sock: socket.socket, data: Dict[str, Any]) -> None:
        """Send newline-delimited JSON to socket.

        Args:
            sock: Connected socket
            data: Dictionary to send (will be JSON-serialized)

        Example:
            >>> self.socket_send(sock, {"type": "create_box", "params": {}})
        """
        payload = json.dumps(data) + "\n"
        sock.sendall(payload.encode("utf-8"))
        logger.debug(f"Sent: {data.get('type', 'unknown')}")

    def socket_receive(self, sock: socket.socket) -> Dict[str, Any]:
        """Receive and parse JSON from socket. Handles multi-chunk responses.

        Args:
            sock: Connected socket

        Returns:
            Parsed JSON response dictionary

        Raises:
            ConnectionError: If connection closed without response
            json.JSONDecodeError: If response is not valid JSON

        Example:
            >>> response = self.socket_receive(sock)
            >>> response["success"]
            True
        """
        chunks = []
        while True:
            chunk = sock.recv(self._recv_buffer_size)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                # Try to parse accumulated data
                data = b"".join(chunks).decode("utf-8")
                return json.loads(data)
            except json.JSONDecodeError:
                # Not complete yet, continue receiving
                continue

        if not chunks:
            raise ConnectionError("Connection closed without response")

        # Last attempt to parse complete data
        raw = b"".join(chunks).decode("utf-8")
        return json.loads(raw)

    def socket_execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Connect, send command, receive response, close. One-shot pattern.

        This is the most common usage pattern - open connection, send one
        command, get response, close connection.

        Args:
            command: Command dictionary to execute

        Returns:
            Response dictionary from CAD application

        Raises:
            ConnectionError: If unable to connect or communicate
            json.JSONDecodeError: If response is invalid JSON

        Example:
            >>> result = self.socket_execute({"type": "create_box", "params": {}})
            >>> result["success"]
            True
        """
        sock = self.socket_connect()
        try:
            self.socket_send(sock, command)
            return self.socket_receive(sock)
        finally:
            sock.close()

    def socket_health_check(self) -> bool:
        """Check if the socket server is responsive.

        Returns:
            True if server is reachable, False otherwise

        Example:
            >>> if self.socket_health_check():
            ...     print("CAD application is running")
        """
        try:
            sock = self.socket_connect()
            sock.close()
            return True
        except (ConnectionError, OSError):
            return False
