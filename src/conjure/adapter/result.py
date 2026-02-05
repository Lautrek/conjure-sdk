"""Unified operation result for all Conjure adapters."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AdapterResult:
    """Result from an adapter command execution.

    This is the canonical result type used by all Conjure client adapters.

    Attributes:
        success: Whether the operation succeeded
        data: Result data dictionary (empty if failed)
        error: Error message if the operation failed

    Examples:
        >>> result = AdapterResult.ok(object_id="Box001", volume=1000.0)
        >>> result.success
        True
        >>> result.data
        {'object_id': 'Box001', 'volume': 1000.0}

        >>> result = AdapterResult.fail("Object not found")
        >>> result.success
        False
        >>> result.error
        'Object not found'
    """

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @classmethod
    def ok(cls, **data) -> "AdapterResult":
        """Create a successful result.

        Args:
            **data: Result data as keyword arguments

        Returns:
            AdapterResult with success=True

        Example:
            >>> AdapterResult.ok(object_id="Box001", volume=1000.0)
        """
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str, **data) -> "AdapterResult":
        """Create a failed result.

        Args:
            error: Error message
            **data: Additional error context as keyword arguments

        Returns:
            AdapterResult with success=False

        Example:
            >>> AdapterResult.fail("Object not found", object_id="Invalid")
        """
        return cls(success=False, data=data, error=error)

    def to_wire(self) -> Dict[str, Any]:
        """Serialize for wire protocol (WebSocket/socket).

        Returns:
            Dictionary suitable for JSON serialization

        Example:
            >>> result = AdapterResult.ok(value=42)
            >>> result.to_wire()
            {'success': True, 'data': {'value': 42}}
        """
        d = {"success": self.success, "data": self.data}
        if self.error:
            d["error"] = self.error
        return d

    def __bool__(self) -> bool:
        """Allow using result in boolean context.

        Example:
            >>> result = AdapterResult.ok()
            >>> if result:
            ...     print("Success!")
        """
        return self.success
