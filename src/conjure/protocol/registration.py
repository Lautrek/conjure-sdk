"""Registration protocol types."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RegistrationPayload:
    """Payload sent when adapter registers with server.

    This message is sent during the initial connection handshake to
    advertise the adapter's capabilities and supported commands.

    Attributes:
        adapter_type: Type identifier (e.g., "freecad", "blender", "kicad")
        adapter_id: Unique instance identifier
        version: Adapter version string
        capabilities: List of capability categories
        commands: List of supported command types
        metadata: Additional adapter-specific metadata

    Example:
        >>> payload = RegistrationPayload(
        ...     adapter_type="freecad",
        ...     adapter_id="adapter_001",
        ...     version="1.0.0",
        ...     capabilities=["primitives", "booleans"],
        ...     commands=["create_box", "boolean_union"]
        ... )
        >>> payload.to_wire()
        {'type': 'adapter_registration', 'adapter_type': 'freecad', ...}
    """

    adapter_type: str
    adapter_id: Optional[str] = None
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_wire(self) -> Dict[str, Any]:
        """Serialize to wire format for transmission.

        Returns:
            Dictionary suitable for JSON serialization

        Example:
            >>> payload = RegistrationPayload(adapter_type="freecad")
            >>> wire = payload.to_wire()
            >>> wire["type"]
            'adapter_registration'
        """
        return {
            "type": "adapter_registration",
            "adapter_type": self.adapter_type,
            "adapter_id": self.adapter_id,
            "version": self.version,
            "capabilities": self.capabilities,
            "commands": self.commands,
            **self.metadata,
        }


@dataclass
class HeartbeatPayload:
    """Heartbeat keep-alive payload.

    Sent periodically to maintain the connection and report adapter status.

    Attributes:
        adapter_id: Unique adapter instance identifier
        status: Current status (e.g., "available", "busy", "error")
        active_jobs: Number of currently executing jobs
        metadata: Additional status information

    Example:
        >>> heartbeat = HeartbeatPayload(
        ...     adapter_id="adapter_001",
        ...     status="available",
        ...     active_jobs=0
        ... )
        >>> heartbeat.to_wire()
        {'type': 'heartbeat', 'adapter_id': 'adapter_001', 'status': 'available', ...}
    """

    adapter_id: str
    status: str = "available"
    active_jobs: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_wire(self) -> Dict[str, Any]:
        """Serialize to wire format for transmission.

        Returns:
            Dictionary suitable for JSON serialization

        Example:
            >>> heartbeat = HeartbeatPayload(adapter_id="adapter_001")
            >>> wire = heartbeat.to_wire()
            >>> wire["type"]
            'heartbeat'
        """
        return {
            "type": "heartbeat",
            "adapter_id": self.adapter_id,
            "status": self.status,
            "active_jobs": self.active_jobs,
            **self.metadata,
        }
