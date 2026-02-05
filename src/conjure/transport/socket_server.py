"""Socket server mixin for hosting a command server inside CAD applications."""

import json
import logging
import queue
import socket
import threading
import uuid
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class SocketServerMixin:
    """Mixin for running a socket server inside a CAD application.

    Used by clients like Blender where the CAD app hosts the server
    and external tools (MCP bridge) connect as clients.

    This is the reverse pattern from SocketClientMixin - here the CAD application
    IS the server, and external tools connect to it.

    Features:
    - Threaded socket accept loop
    - Thread-safe command queue for main-thread execution
    - Result map with threading events for synchronization

    Usage:
        >>> class MyAdapter:
        ...     def __init__(self):
        ...         self.server_init(host="127.0.0.1", port=9877)
        ...         self.server_start()
        ...
        ...     def execute_command(self, cmd_type, params):
        ...         # Execute on main thread
        ...         return {"success": True}

    Attributes:
        _server_host: Server bind address (default: "127.0.0.1")
        _server_port: Server bind port (default: 9877)
        _server_running: Whether server is running
        _server_socket: Server socket instance
        _server_thread: Background accept thread
        _operation_queue: Queue for commands to execute on main thread
        _result_map: Map of request_id -> result
        _result_events: Map of request_id -> threading.Event for sync
    """

    _server_host: str = "127.0.0.1"
    _server_port: int = 9877
    _server_running: bool = False
    _server_socket: Optional[socket.socket] = None
    _server_thread: Optional[threading.Thread] = None
    _operation_queue: Optional[queue.Queue] = None
    _result_map: Optional[Dict[str, Any]] = None
    _result_events: Optional[Dict[str, threading.Event]] = None

    def server_init(self, host: str = "127.0.0.1", port: int = 9877):
        """Initialize server state.

        Args:
            host: Bind address (default: "127.0.0.1")
            port: Bind port (default: 9877)

        Example:
            >>> self.server_init(host="127.0.0.1", port=9877)
        """
        self._server_host = host
        self._server_port = port
        self._operation_queue = queue.Queue()
        self._result_map = {}
        self._result_events = {}
        logger.info(f"Server initialized for {host}:{port}")

    def server_start(self):
        """Start the socket server in a background thread.

        Example:
            >>> self.server_start()
            >>> # Server now accepting connections in background
        """
        if self._server_running:
            logger.warning("Server already running")
            return
        self._server_running = True
        self._server_thread = threading.Thread(target=self._server_accept_loop, daemon=True)
        self._server_thread.start()
        logger.info(f"Server started on {self._server_host}:{self._server_port}")

    def server_stop(self):
        """Stop the socket server.

        Example:
            >>> self.server_stop()
        """
        self._server_running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None
        logger.info("Server stopped")

    def _server_accept_loop(self):
        """Accept connections and handle clients (runs in background thread)."""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._server_socket.bind((self._server_host, self._server_port))
            self._server_socket.listen(1)
            self._server_socket.settimeout(1.0)
            logger.info(f"Listening on {self._server_host}:{self._server_port}")
        except OSError as e:
            logger.error(f"Failed to bind to {self._server_host}:{self._server_port}: {e}")
            self._server_running = False
            return

        while self._server_running:
            try:
                client, addr = self._server_socket.accept()
                logger.info(f"Client connected from {addr}")
                # Handle each client in a separate thread
                client_thread = threading.Thread(target=self._server_handle_client, args=(client,), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._server_running:
                    logger.error(f"Server error: {e}")

    def _server_handle_client(self, client: socket.socket):
        """Handle newline-delimited JSON commands from a client (runs in client thread).

        Args:
            client: Connected client socket
        """
        buffer = ""
        while self._server_running:
            try:
                data = client.recv(8192).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        response = self._server_queue_and_wait(line.strip())
                        client.send((json.dumps(response) + "\n").encode("utf-8"))
            except Exception as e:
                logger.error(f"Client error: {e}")
                break
        client.close()
        logger.debug("Client disconnected")

    def _server_queue_and_wait(self, command_str: str, timeout: float = 60.0) -> Dict[str, Any]:
        """Parse command, queue for main thread, wait for result.

        Args:
            command_str: JSON command string
            timeout: Maximum wait time in seconds

        Returns:
            Response dictionary

        Example:
            >>> response = self._server_queue_and_wait('{"type": "create_box", "params": {}}')
        """
        try:
            cmd = json.loads(command_str)
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"Invalid JSON: {e}"}

        request_id = cmd.get("request_id", str(uuid.uuid4()))
        event = threading.Event()
        self._result_events[request_id] = event
        self._operation_queue.put((cmd.get("type", ""), cmd.get("params", {}), request_id))

        if event.wait(timeout=timeout):
            result = self._result_map.pop(request_id, {"status": "error", "error": "No result"})
            del self._result_events[request_id]
            return result

        self._result_events.pop(request_id, None)
        return {"status": "error", "error": "Operation timed out"}

    def server_process_queue(self, executor: Callable, max_ops: int = 10) -> bool:
        """Process queued operations on the main thread.

        Call this from your application's timer/idle callback.

        Args:
            executor: Callable(cmd_type: str, params: dict) -> dict that executes commands
            max_ops: Maximum operations to process per call

        Returns:
            True if server is still running (keep timer alive), False to stop

        Example:
            >>> # In Blender timer callback
            >>> def timer_callback():
            ...     return self.server_process_queue(self.execute_command)
            >>> bpy.app.timers.register(timer_callback, first_interval=0.1, persistent=True)
        """
        if not self._server_running:
            return False

        for _ in range(max_ops):
            try:
                cmd_type, params, request_id = self._operation_queue.get_nowait()
                try:
                    result = executor(cmd_type, params)
                except Exception as e:
                    logger.exception(f"Executor error for {cmd_type}")
                    result = {"status": "error", "error": str(e)}
                self._result_map[request_id] = result
                if request_id in self._result_events:
                    self._result_events[request_id].set()
            except queue.Empty:
                break

        return True

    @property
    def server_queue_size(self) -> int:
        """Get number of pending operations in queue.

        Returns:
            Number of operations waiting to be processed

        Example:
            >>> print(f"Pending operations: {self.server_queue_size}")
        """
        if self._operation_queue:
            return self._operation_queue.qsize()
        return 0
