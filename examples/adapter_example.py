"""Example demonstrating the Conjure SDK adapter framework.

This shows how to build a custom CAD adapter using the framework.
"""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conjure.adapter import AdapterResult, AdapterRunner, BaseAdapter
from conjure.protocol import Capability


class ExampleAdapter(BaseAdapter):
    """Example adapter demonstrating the framework patterns."""

    def __init__(self):
        super().__init__()
        # Auto-register all methods starting with _cmd_
        self.register_handlers_by_prefix("_cmd_")
        print("Initialized ExampleAdapter")

    # Command handlers

    def _cmd_create_box(self, params):
        """Create a box primitive."""
        width = params.get("width", 1.0)
        height = params.get("height", 1.0)
        depth = params.get("depth", 1.0)
        name = params.get("name", "Box001")

        print(f"Creating box: {name} ({width}x{height}x{depth})")

        return AdapterResult.ok(
            object_id=name,
            type="box",
            dimensions={"width": width, "height": height, "depth": depth},
        )

    def _cmd_create_cylinder(self, params):
        """Create a cylinder primitive."""
        radius = params.get("radius", 1.0)
        height = params.get("height", 2.0)
        name = params.get("name", "Cylinder001")

        print(f"Creating cylinder: {name} (r={radius}, h={height})")

        return AdapterResult.ok(
            object_id=name,
            type="cylinder",
            dimensions={"radius": radius, "height": height},
        )

    async def _cmd_async_operation(self, params):
        """Example async command handler."""
        print("Running async operation...")
        await asyncio.sleep(0.1)
        return AdapterResult.ok(message="Async operation completed")

    # Required abstract methods

    def health_check(self) -> bool:
        """Check if CAD application is available."""
        # In a real adapter, this would check if the CAD app is running
        return True

    def get_capabilities(self) -> list:
        """Return supported capabilities."""
        return [
            Capability.PRIMITIVES,
            Capability.BOOLEANS,
            Capability.TRANSFORMS,
        ]


async def demo_local_execution():
    """Demonstrate local command execution without server connection."""
    print("\n=== Local Execution Demo ===\n")

    adapter = ExampleAdapter()

    # Execute commands locally
    result = await adapter.execute("create_box", {"width": 10, "height": 20, "depth": 30})
    print(f"Result: {result.to_wire()}")

    result = await adapter.execute("create_cylinder", {"radius": 5, "height": 15})
    print(f"Result: {result.to_wire()}")

    # Test async handler
    result = await adapter.execute("async_operation", {})
    print(f"Result: {result.to_wire()}")

    # Test error handling
    result = await adapter.execute("unknown_command", {})
    print(f"Result: {result.to_wire()}")

    # Show capabilities
    print(f"\nCapabilities: {adapter.get_capabilities()}")
    print(f"Commands: {adapter.get_supported_commands()}")


async def demo_server_connection():
    """Demonstrate server connection (requires server to be running)."""
    print("\n=== Server Connection Demo ===\n")
    print("Note: This requires the Conjure server to be running.")
    print("Skipping in this example - see commented code below.\n")

    # Uncomment to actually connect to server:
    # adapter = ExampleAdapter()
    # runner = AdapterRunner(
    #     adapter,
    #     server_url="ws://localhost:8000/api/v1/adapter/ws",
    #     api_key="test_key",
    #     adapter_type="example"
    # )
    # await runner.run()


if __name__ == "__main__":
    print("Conjure SDK Adapter Framework Example")
    print("=" * 50)

    # Run local demo
    asyncio.run(demo_local_execution())

    # Optionally run server demo
    # asyncio.run(demo_server_connection())
