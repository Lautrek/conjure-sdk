#!/usr/bin/env python3
"""
USB Holder Example - Build123d-Style Scripting with Conjure SDK

This example demonstrates the Pythonic builder pattern for CAD scripting.
All CAD operations are delegated to the server - this is just an adaptive layer.

Usage:
    # Set environment variables
    export CONJURE_API_KEY="your-api-key"
    export CONJURE_API_URL="http://localhost:8000"  # or your server URL

    # Run the script
    python usb_holder.py
"""

from conjure import Part


def create_usb_holder():
    """Create a USB holder with slots for 4 USB drives."""

    with Part("USBHolder") as p:
        # Create the base block
        # 100mm wide, 50mm deep, 30mm tall
        base = p.box(100, 50, 30, name="Base")

        # Create 4 USB slots (12mm wide, 25mm deep)
        slot_width = 12
        slot_depth = 25
        slot_spacing = 22
        start_x = 11  # Center the slots

        for i in range(4):
            slot = p.slot(
                width=slot_width,
                depth=slot_depth,
                length=slot_width,
                position=[start_x + i * slot_spacing, 25, 5],
                name=f"Slot_{i + 1}",
            )
            base.cut(slot)

        # Add cable routing hole at the back
        cable_hole = p.hole(
            diameter=8,
            depth=50,  # Goes through
            position=[50, 5, 15],
            name="CableHole",
        )
        base.cut(cable_hole)

        # Fillet the top edges for a nicer look
        base.fillet("top", 2)

        # Chamfer the bottom edges for better adhesion when printing
        base.chamfer("bottom", 0.5)

        # Print summary
        print("USB Holder created successfully!")
        print(f"Objects in part: {len(p._objects)}")

        # List all objects
        objects = p.list_objects()
        for obj in objects:
            print(f"  - {obj.get('name', 'Unknown')}")

        # Export to STL
        p.export_stl("usb_holder.stl")
        print("Exported to usb_holder.stl")

        return base


def create_phone_stand():
    """Create a simple phone stand."""

    with Part("PhoneStand") as p:
        # Base
        base = p.box(80, 60, 10, name="Base")

        # Back support at an angle (simplified as box for now)
        back = p.box(80, 10, 100, name="BackSupport", position=[0, 50, 10])

        # Fuse them together
        stand = p.union(base, back, name="Stand")

        # Add phone rest slot
        rest_slot = p.slot(width=5, depth=15, length=60, position=[10, 20, 5], name="RestSlot")
        stand.cut(rest_slot)

        # Round the top edges
        stand.fillet("top", 3)

        print("Phone Stand created!")
        p.export_stl("phone_stand.stl")

        return stand


def create_cable_organizer():
    """Create a cable organizer with multiple channels."""

    with Part("CableOrganizer") as p:
        # Main body
        body = p.box(120, 40, 25, name="Body")

        # Create 6 cable channels (8mm diameter)
        for i in range(6):
            channel = p.cylinder(
                radius=4,
                height=50,  # Through the part
                position=[15 + i * 18, 20, 12.5],
                name=f"Channel_{i + 1}",
            )
            # Rotate channel to be horizontal
            channel.rotate("x", 90)
            body.cut(channel)

        # Mounting holes
        for x in [10, 110]:
            hole = p.hole(diameter=4, depth=30, position=[x, 20, 0], name="MountHole")
            body.cut(hole)

        # Fillet all edges
        body.fillet("all", 2)

        print("Cable Organizer created!")
        p.export_stl("cable_organizer.stl")

        return body


if __name__ == "__main__":
    import os

    # Check for required environment variables
    if not os.environ.get("CONJURE_API_KEY"):
        print("Warning: CONJURE_API_KEY not set")
        print("Set it with: export CONJURE_API_KEY='your-api-key'")
        print()
        print("Running in demo mode (operations will fail without server)")
        print()

    # Create the USB holder
    try:
        create_usb_holder()
    except Exception as e:
        print(f"Error creating USB holder: {e}")
        print("Make sure the Conjure server is running and credentials are set.")
