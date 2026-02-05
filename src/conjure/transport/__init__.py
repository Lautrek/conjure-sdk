"""Transport mixins for socket and WebSocket communication.

This package provides reusable transport layer implementations that can be
mixed into engine classes to handle low-level communication.

Patterns:
    - SocketClientMixin: Connect TO a CAD app's socket server (FreeCAD pattern)
    - SocketServerMixin: Host a socket server IN the CAD app (Blender pattern)

Example - Socket Client (FreeCAD):
    >>> from conjure.adapter import BaseEngine
    >>> from conjure.transport import SocketClientMixin
    >>>
    >>> class FreeCADEngine(SocketClientMixin, BaseEngine):
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

Example - Socket Server (Blender):
    >>> from conjure.transport import SocketServerMixin
    >>>
    >>> class BlenderAdapter(SocketServerMixin, BaseAdapter):
    ...     def __init__(self):
    ...         super().__init__()
    ...         self.server_init(host="127.0.0.1", port=9877)
    ...         self.server_start()
    ...
    ...     def run_timer(self):
    ...         # Called by Blender timer
    ...         return self.server_process_queue(self.execute_sync)
"""

from .socket_client import SocketClientMixin
from .socket_server import SocketServerMixin

__all__ = ["SocketServerMixin", "SocketClientMixin"]
