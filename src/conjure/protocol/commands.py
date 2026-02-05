"""Command wire protocol types."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CommandEnvelope:
    """Incoming command from server or bridge.

    Represents a command message sent to the adapter for execution.

    Attributes:
        type: Command type identifier (e.g., "create_box")
        params: Command parameters
        request_id: Optional request identifier for tracking

    Example:
        >>> envelope = CommandEnvelope.from_wire({
        ...     "type": "create_box",
        ...     "params": {"width": 10, "height": 20, "depth": 30},
        ...     "request_id": "req_123"
        ... })
        >>> envelope.type
        'create_box'
    """

    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None

    @classmethod
    def from_wire(cls, data: Dict[str, Any]) -> "CommandEnvelope":
        """Parse command from wire format.

        Args:
            data: Raw message dictionary

        Returns:
            CommandEnvelope instance

        Example:
            >>> data = {"type": "create_box", "params": {"width": 10}}
            >>> envelope = CommandEnvelope.from_wire(data)
        """
        return cls(
            type=data.get("type", ""),
            params=data.get("params", {}),
            request_id=data.get("request_id"),
        )


@dataclass
class CommandResponse:
    """Outgoing response to server or bridge.

    Represents the result of command execution sent back to the requester.

    Attributes:
        success: Whether the command succeeded
        data: Result data dictionary
        error: Error message if failed
        request_id: Request identifier (echo from request)

    Example:
        >>> response = CommandResponse(
        ...     success=True,
        ...     data={"object_id": "Box001"},
        ...     request_id="req_123"
        ... )
        >>> response.to_wire()
        {'success': True, 'data': {'object_id': 'Box001'}, 'request_id': 'req_123'}
    """

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    request_id: Optional[str] = None

    def to_wire(self) -> Dict[str, Any]:
        """Serialize to wire format for transmission.

        Returns:
            Dictionary suitable for JSON serialization

        Example:
            >>> response = CommandResponse(success=True, data={"value": 42})
            >>> response.to_wire()
            {'success': True, 'data': {'value': 42}}
        """
        d = {"success": self.success, "data": self.data}
        if self.error:
            d["error"] = self.error
        if self.request_id:
            d["request_id"] = self.request_id
        return d
