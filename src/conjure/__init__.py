"""
Conjure SDK - Official Python client for the Conjure CAD API.

Imperative API:
    from conjure import ConjureClient

    client = ConjureClient(api_key="your-api-key")
    box = client.create_box(width=50, height=30, depth=20)

Builder Pattern (Build123d-style):
    from conjure import Part

    with Part("Holder") as p:
        base = p.box(100, 50, 30)
        hole = p.cylinder(10, 40, position=[50, 25, 0])
        base.cut(hole)
        base.fillet("top", 2)
"""

from .builder import ObjectRef, Part, part
from .client import AsyncConjureClient, ConjureClient
from .exceptions import (
    AuthenticationError,
    ConjureAPIError,
    ConjureError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

__version__ = "0.1.0"
__all__ = [
    # Builder pattern (primary API)
    "Part",
    "ObjectRef",
    "part",
    # Imperative client
    "ConjureClient",
    "AsyncConjureClient",
    # Exceptions
    "ConjureError",
    "ConjureAPIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
]
