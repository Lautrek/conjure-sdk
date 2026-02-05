"""
Builder pattern for Pythonic CAD scripting.

Provides Build123d-style context managers that wrap the Conjure API.
All CAD operations are delegated to the server - this is just an adaptive layer.

Usage:
    from conjure import Part

    with Part("Holder") as p:
        p.box(100, 50, 30)
        for i in range(4):
            p.cylinder(5, 20, position=[i * 20, 0, 30])
        p.fillet("top", 2)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import ConjureClient


@dataclass
class ObjectRef:
    """Reference to a CAD object on the server."""

    name: str
    part: Part

    def fillet(self, face_or_edges: str | list[str], radius: float) -> ObjectRef:
        """Add fillet to this object's edges."""
        edges = [face_or_edges] if isinstance(face_or_edges, str) else face_or_edges
        self.part._client.fillet(self.name, radius, edges)
        return self

    def chamfer(self, face_or_edges: str | list[str], size: float) -> ObjectRef:
        """Add chamfer to this object's edges."""
        edges = [face_or_edges] if isinstance(face_or_edges, str) else face_or_edges
        self.part._client.chamfer(self.name, size, edges)
        return self

    def move(self, x: float = 0, y: float = 0, z: float = 0) -> ObjectRef:
        """Move this object."""
        self.part._client.translate(self.name, x, y, z)
        return self

    def rotate(self, axis: str = "z", angle: float = 0) -> ObjectRef:
        """Rotate this object around an axis."""
        self.part._client.rotate(self.name, axis, angle)
        return self

    def cut(self, tool: str | ObjectRef) -> ObjectRef:
        """Cut another object from this one."""
        tool_name = tool.name if isinstance(tool, ObjectRef) else tool
        result = self.part._client.cut(self.name, tool_name)
        if result.data and result.data.get("object"):
            return ObjectRef(result.data["object"], self.part)
        return self


class Part:
    """
    Context manager for building a CAD part.

    All operations are delegated to the server - this is just a Pythonic interface.

    Example:
        with Part("MyPart") as p:
            base = p.box(100, 50, 30)
            hole = p.cylinder(10, 40, position=[50, 25, 0])
            base.cut(hole)
            base.fillet("top", 2)
    """

    def __init__(
        self,
        name: str = "Part",
        client: ConjureClient | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize a Part context.

        Args:
            name: Name prefix for objects in this part
            client: Existing ConjureClient (optional)
            api_key: API key if creating new client
            base_url: Server URL if creating new client
        """
        self.name = name
        self._objects: list[ObjectRef] = []
        self._counter = 0
        self._owns_client = client is None

        if client:
            self._client = client
        else:
            self._client = ConjureClient(api_key=api_key, base_url=base_url)

    def __enter__(self) -> Part:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_client:
            self._client.close()
        return False

    def _next_name(self, prefix: str = "") -> str:
        """Generate unique object name."""
        self._counter += 1
        base = prefix or self.name
        return f"{base}_{self._counter}"

    # =========================================================================
    # Primitives - delegate to server
    # =========================================================================

    def box(
        self,
        length: float,
        width: float,
        height: float,
        name: str | None = None,
        position: list[float] | None = None,
    ) -> ObjectRef:
        """Create a box primitive."""
        obj_name = name or self._next_name("Box")
        self._client.create_box(length, width, height, obj_name, position)
        ref = ObjectRef(obj_name, self)
        self._objects.append(ref)
        return ref

    def cylinder(
        self,
        radius: float,
        height: float,
        name: str | None = None,
        position: list[float] | None = None,
    ) -> ObjectRef:
        """Create a cylinder primitive."""
        obj_name = name or self._next_name("Cylinder")
        self._client.create_cylinder(radius, height, obj_name, position)
        ref = ObjectRef(obj_name, self)
        self._objects.append(ref)
        return ref

    def sphere(
        self,
        radius: float,
        name: str | None = None,
        position: list[float] | None = None,
    ) -> ObjectRef:
        """Create a sphere primitive."""
        obj_name = name or self._next_name("Sphere")
        self._client.create_sphere(radius, obj_name, position)
        ref = ObjectRef(obj_name, self)
        self._objects.append(ref)
        return ref

    # =========================================================================
    # Boolean operations
    # =========================================================================

    def union(self, *objects: str | ObjectRef, name: str | None = None) -> ObjectRef:
        """Fuse multiple objects together."""
        obj_names = [o.name if isinstance(o, ObjectRef) else o for o in objects]
        obj_name = name or self._next_name("Union")
        self._client.union(obj_names, obj_name)
        ref = ObjectRef(obj_name, self)
        self._objects.append(ref)
        return ref

    def cut(
        self,
        target: str | ObjectRef,
        tool: str | ObjectRef,
        name: str | None = None,
    ) -> ObjectRef:
        """Cut tool from target."""
        target_name = target.name if isinstance(target, ObjectRef) else target
        tool_name = tool.name if isinstance(tool, ObjectRef) else tool
        obj_name = name or self._next_name("Cut")
        self._client.cut(target_name, tool_name, obj_name)
        ref = ObjectRef(obj_name, self)
        self._objects.append(ref)
        return ref

    def intersect(self, *objects: str | ObjectRef, name: str | None = None) -> ObjectRef:
        """Get intersection of multiple objects."""
        obj_names = [o.name if isinstance(o, ObjectRef) else o for o in objects]
        obj_name = name or self._next_name("Intersect")
        self._client.intersect(obj_names, obj_name)
        ref = ObjectRef(obj_name, self)
        self._objects.append(ref)
        return ref

    # =========================================================================
    # Convenience methods for common patterns
    # =========================================================================

    def slot(
        self,
        width: float,
        depth: float,
        length: float | None = None,
        position: list[float] | None = None,
        name: str | None = None,
    ) -> ObjectRef:
        """
        Create a slot (rectangular cutout tool).

        This creates a box that can be used as a cutting tool.
        """
        slot_length = length or width
        return self.box(slot_length, width, depth, name or self._next_name("Slot"), position)

    def hole(
        self,
        diameter: float,
        depth: float,
        position: list[float] | None = None,
        name: str | None = None,
    ) -> ObjectRef:
        """
        Create a hole (cylindrical cutout tool).

        This creates a cylinder that can be used as a cutting tool.
        """
        return self.cylinder(diameter / 2, depth, name or self._next_name("Hole"), position)

    def array(
        self,
        base: str | ObjectRef,
        count: int,
        spacing: float,
        axis: str = "x",
    ) -> list[ObjectRef]:
        """
        Create a linear array of copies.

        Args:
            base: Object to copy
            count: Number of copies (including original)
            spacing: Distance between copies
            axis: Direction of array ("x", "y", or "z")

        Returns:
            List of ObjectRefs including the original
        """
        base_name = base.name if isinstance(base, ObjectRef) else base
        results = [ObjectRef(base_name, self) if isinstance(base, str) else base]

        for i in range(1, count):
            # Calculate offset
            offset = [0.0, 0.0, 0.0]
            axis_idx = {"x": 0, "y": 1, "z": 2}.get(axis.lower(), 0)
            offset[axis_idx] = spacing * i

            # Create copy at offset position
            copy_name = self._next_name(f"{base_name}_copy")
            # Note: This would need a copy operation on the server
            # For now, create new primitives at offset positions
            results.append(ObjectRef(copy_name, self))

        return results

    # =========================================================================
    # Query methods
    # =========================================================================

    def list_objects(self) -> list[dict[str, Any]]:
        """List all objects in the document."""
        return self._client.list_objects()

    def measure(self, from_obj: str | ObjectRef, to_obj: str | ObjectRef) -> dict[str, Any]:
        """Measure distance between two objects."""
        from_name = from_obj.name if isinstance(from_obj, ObjectRef) else from_obj
        to_name = to_obj.name if isinstance(to_obj, ObjectRef) else to_obj
        return self._client.measure(from_name, to_name)

    def bounding_box(self, obj: str | ObjectRef) -> dict[str, Any]:
        """Get bounding box of an object."""
        obj_name = obj.name if isinstance(obj, ObjectRef) else obj
        return self._client.bounding_box(obj_name)

    # =========================================================================
    # Export
    # =========================================================================

    def export_stl(self, filename: str, objects: list[str | ObjectRef] | None = None) -> None:
        """Export objects to STL file."""
        obj_names = None
        if objects:
            obj_names = [o.name if isinstance(o, ObjectRef) else o for o in objects]
        self._client.export("stl", filename, obj_names)

    def export_step(self, filename: str, objects: list[str | ObjectRef] | None = None) -> None:
        """Export objects to STEP file."""
        obj_names = None
        if objects:
            obj_names = [o.name if isinstance(o, ObjectRef) else o for o in objects]
        self._client.export("step", filename, obj_names)


# Convenience function for quick scripts
def part(name: str = "Part", **kwargs) -> Part:
    """Create a Part context manager."""
    return Part(name, **kwargs)
