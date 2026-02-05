"""Capability constants shared across clients."""


class Capability:
    """Standard capability identifiers.

    These constants define the standard capability categories that adapters
    can advertise to indicate which types of operations they support.

    CAD Capabilities:
        PRIMITIVES: Basic shape creation (box, cylinder, sphere, etc.)
        BOOLEANS: Boolean operations (union, cut, intersect)
        TRANSFORMS: Geometric transformations (move, rotate, scale)
        QUERIES: Model queries (measure, bounding box, properties)
        EXPORT: Export to file formats (STL, STEP, etc.)
        IMPORT: Import from file formats
        MODIFIERS: Mesh/geometry modifiers
        CURVES: Curve and spline operations
        MATERIALS: Material and texture support
        SKETCHES: 2D sketch operations
        ASSEMBLY: Multi-part assembly support
        SIMULATION: Physics/FEA simulation

    Content Creation Capabilities:
        ANIMATION: Animation support
        PHYSICS: Physics simulation
        GEOMETRY_NODES: Procedural geometry (Blender-specific)
        RENDERING: Rendering and visualization

    EDA Capabilities:
        EDA: Electronic design automation (KiCad)

    Example:
        >>> class MyAdapter(BaseAdapter):
        ...     def get_capabilities(self):
        ...         return [
        ...             Capability.PRIMITIVES,
        ...             Capability.BOOLEANS,
        ...             Capability.TRANSFORMS
        ...         ]
    """

    # Core CAD capabilities
    PRIMITIVES = "primitives"
    BOOLEANS = "booleans"
    TRANSFORMS = "transforms"
    QUERIES = "queries"
    EXPORT = "export"
    IMPORT = "import"
    MODIFIERS = "modifiers"
    CURVES = "curves"
    MATERIALS = "materials"

    # Content creation capabilities
    ANIMATION = "animation"
    PHYSICS = "physics"
    GEOMETRY_NODES = "geometry_nodes"
    RENDERING = "rendering"

    # Engineering capabilities
    SKETCHES = "sketches"
    ASSEMBLY = "assembly"
    SIMULATION = "simulation"

    # EDA capabilities
    EDA = "eda"

    @classmethod
    def all(cls) -> list:
        """Get all defined capability constants.

        Returns:
            List of all capability identifier strings

        Example:
            >>> all_caps = Capability.all()
            >>> Capability.PRIMITIVES in all_caps
            True
        """
        return [value for name, value in vars(cls).items() if not name.startswith("_") and isinstance(value, str)]

    @classmethod
    def validate(cls, capability: str) -> bool:
        """Check if a string is a valid capability identifier.

        Args:
            capability: Capability string to validate

        Returns:
            True if valid, False otherwise

        Example:
            >>> Capability.validate("primitives")
            True
            >>> Capability.validate("invalid")
            False
        """
        return capability in cls.all()
