"""Conjure SDK Adapter Framework - Base classes for building CAD client adapters.

This package provides the foundational classes for creating Conjure adapters
that connect CAD applications (FreeCAD, Blender, KiCad, Fusion360) to the
hosted Conjure server.

Main Components:
    - BaseAdapter: Abstract base class for implementing command handlers
    - BaseEngine: Abstract base class for transport layer (socket, IPC, HTTP)
    - BaseServerClient: WebSocket client for cloud server connection
    - AdapterResult: Unified result type for all operations
    - AdapterRunner: Convenience class for running adapter services

Example:
    >>> from conjure.adapter import BaseAdapter, AdapterResult, AdapterRunner
    >>>
    >>> class MyAdapter(BaseAdapter):
    ...     def __init__(self):
    ...         super().__init__()
    ...         self.register_handlers_by_prefix("_cmd_")
    ...
    ...     def _cmd_create_box(self, params):
    ...         return AdapterResult.ok(object_id="Box001")
    ...
    ...     def health_check(self):
    ...         return True
    ...
    ...     def get_capabilities(self):
    ...         return ["primitives"]
    >>>
    >>> runner = AdapterRunner(MyAdapter(), api_key="sk_test_123")
    >>> asyncio.run(runner.run())
"""

from .base_adapter import BaseAdapter
from .base_engine import BaseEngine
from .base_server_client import BaseServerClient, ConnectionState
from .config import BaseEngineConfig, ServerClientConfig, SocketEngineConfig
from .result import AdapterResult
from .runner import AdapterRunner

__all__ = [
    "AdapterResult",
    "BaseAdapter",
    "BaseEngine",
    "BaseServerClient",
    "ConnectionState",
    "BaseEngineConfig",
    "ServerClientConfig",
    "SocketEngineConfig",
    "AdapterRunner",
]
