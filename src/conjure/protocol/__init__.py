"""Wire protocol types for Conjure adapter communication.

This package defines the message formats used for communication between
adapters, the hosted server, and bridge components.

Message Types:
    - CommandEnvelope: Incoming commands from server/bridge
    - CommandResponse: Outgoing responses to server/bridge
    - RegistrationPayload: Adapter registration during connection
    - HeartbeatPayload: Keep-alive heartbeat messages
    - Capability: Standard capability identifiers

Example:
    >>> from conjure.protocol import CommandEnvelope, CommandResponse, Capability
    >>>
    >>> # Parse incoming command
    >>> envelope = CommandEnvelope.from_wire({
    ...     "type": "create_box",
    ...     "params": {"width": 10}
    ... })
    >>>
    >>> # Build response
    >>> response = CommandResponse(
    ...     success=True,
    ...     data={"object_id": "Box001"}
    ... )
    >>> response.to_wire()
    {'success': True, 'data': {'object_id': 'Box001'}}
"""

from .capabilities import Capability
from .commands import CommandEnvelope, CommandResponse
from .registration import HeartbeatPayload, RegistrationPayload

__all__ = [
    "CommandEnvelope",
    "CommandResponse",
    "RegistrationPayload",
    "HeartbeatPayload",
    "Capability",
]
