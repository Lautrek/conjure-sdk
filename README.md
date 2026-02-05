# Conjure Python SDK

[![PyPI](https://img.shields.io/pypi/v/conjure-sdk)](https://pypi.org/project/conjure-sdk/)
[![CI](https://github.com/Lautrek/conjure-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Lautrek/conjure-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official Python SDK for the Conjure CAD platform. Provides both a Build123d-style builder pattern and an imperative API for AI-assisted CAD scripting.

## Installation

```bash
pip install conjure-sdk
```

## Quick Start: Builder Pattern (Recommended)

The builder pattern provides a Pythonic, Build123d-style interface for CAD scripting:

```python
from conjure import Part

with Part("USBHolder") as p:
    # Create base block
    base = p.box(100, 50, 30)

    # Create 4 USB slots
    for i in range(4):
        slot = p.slot(width=12, depth=25, position=[11 + i*22, 25, 5])
        base.cut(slot)

    # Add finishing touches
    base.fillet("top", 2)
    base.chamfer("bottom", 0.5)

    # Export
    p.export_stl("usb_holder.stl")
```

## Builder Pattern Features

### Context Manager

The `Part` context manager handles client lifecycle automatically:

```python
from conjure import Part

# With explicit credentials
with Part("MyPart", api_key="sk-...", base_url="http://localhost:8000") as p:
    base = p.box(50, 30, 20)

# Using environment variables (CONJURE_API_KEY, CONJURE_API_URL)
with Part("MyPart") as p:
    base = p.box(50, 30, 20)
```

### Method Chaining

Operations return `ObjectRef` for fluent chaining:

```python
with Part("ChainedPart") as p:
    base = p.box(100, 50, 30)

    # Chain multiple operations
    base.move(10, 0, 0).rotate("z", 45).fillet("top", 2)

    # Or step by step
    hole = p.cylinder(5, 40, position=[50, 25, 0])
    base.cut(hole).chamfer("edges", 0.5)
```

### Primitives

```python
with Part("Primitives") as p:
    box = p.box(100, 50, 30)
    cylinder = p.cylinder(radius=10, height=50)
    sphere = p.sphere(radius=25)

    # Convenience methods
    slot = p.slot(width=12, depth=25)  # Box for slot cutting
    hole = p.hole(diameter=10, depth=30)  # Cylinder for hole cutting
```

### Boolean Operations

```python
with Part("Booleans") as p:
    base = p.box(100, 50, 30)
    cutter = p.cylinder(10, 50, position=[50, 25, 0])

    # Method on ObjectRef
    base.cut(cutter)

    # Or via Part
    result = p.cut(base, cutter, name="WithHole")

    # Union and intersect
    combined = p.union(obj1, obj2, obj3)
    common = p.intersect(obj1, obj2)
```

### Transforms

```python
with Part("Transforms") as p:
    obj = p.box(50, 30, 20)

    obj.move(x=10, y=20, z=0)
    obj.rotate(axis="z", angle=45)
```

### Queries and Export

```python
with Part("Queries") as p:
    box = p.box(100, 50, 30)
    cyl = p.cylinder(10, 50, position=[0, 100, 0])

    # List all objects
    objects = p.list_objects()

    # Measure distance
    dist = p.measure(box, cyl)

    # Bounding box
    bbox = p.bounding_box(box)

    # Export
    p.export_stl("output.stl", objects=[box])
    p.export_step("output.step")
```

---

## Imperative API

For direct API access, use `ConjureClient`:

```python
from conjure import ConjureClient

# Initialize client with API key
client = ConjureClient(api_key="your-api-key")

# Create a box
result = client.create_box(width=50, height=30, depth=20)
print(f"Created: {result.object_id}")

# Apply fillet
client.fillet(object_id=result.object_id, radius=2)

# Export to STL
client.export(format="stl", filename="my_part.stl")
```

## Features

- Full API coverage for all Conjure operations
- Async support with `conjure.AsyncConjureClient`
- Type hints and IDE autocompletion
- Automatic retry and error handling
- Streaming support for large exports

## API Reference

### Creating Primitives

```python
# Box
client.create_box(width=50, height=30, depth=20, name="MyBox")

# Cylinder
client.create_cylinder(radius=10, height=50, name="MyCylinder")

# Sphere
client.create_sphere(radius=25, name="MySphere")
```

### Boolean Operations

```python
# Union
client.union(objects=["Box1", "Cylinder1"], name="Combined")

# Cut
client.cut(target="Box1", tool="Cylinder1", name="WithHole")

# Intersection
client.intersect(objects=["Box1", "Sphere1"], name="Common")
```

### Transforms

```python
# Translate
client.translate(object_id="Box1", x=10, y=0, z=5)

# Rotate
client.rotate(object_id="Box1", axis="z", angle=45)

# Scale
client.scale(object_id="Box1", factor=2.0)
```

### Queries

```python
# List objects
objects = client.list_objects()

# Measure
distance = client.measure(from_obj="Box1", to_obj="Cylinder1")

# Bounding box
bbox = client.bounding_box(object_id="Box1")
```

## Authentication

```python
# Using environment variable (recommended)
# Set CONJURE_API_KEY in your environment
client = ConjureClient()

# Or pass directly
client = ConjureClient(api_key="sk-...")

# Or use a config file
client = ConjureClient.from_config("~/.conjure/config.yaml")
```

## Async Usage

```python
import asyncio
from conjure import AsyncConjureClient

async def main():
    async with AsyncConjureClient() as client:
        box = await client.create_box(width=50, height=30, depth=20)
        await client.fillet(object_id=box.object_id, radius=2)

asyncio.run(main())
```

## Error Handling

```python
from conjure.exceptions import (
    ConjureAPIError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
)

try:
    client.create_box(width=-10)  # Invalid
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except ConjureAPIError as e:
    print(f"API error: {e}")
```

## Links

- [Conjure FreeCAD](https://github.com/Lautrek/conjure-freecad) - FreeCAD workbench
- [Conjure Blender](https://github.com/Lautrek/conjure-blender) - Blender add-on
- [Conjure Website](https://conjure.lautrek.com)

## License

MIT License - See [LICENSE](LICENSE) file.
