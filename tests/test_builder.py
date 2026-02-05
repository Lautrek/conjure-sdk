"""
Unit tests for the Builder Pattern (Part context manager).

These tests use mocks and don't require a live server connection.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest


class TestObjectRef:
    """Tests for ObjectRef class."""

    def test_object_ref_creation(self):
        """Test ObjectRef stores name and part reference."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        assert ref.name == "MyBox"
        assert ref.part is part

    def test_fillet_delegates_to_client(self):
        """Test fillet method calls client correctly."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        result = ref.fillet("top", 2.0)

        mock_client.fillet.assert_called_once_with("MyBox", 2.0, ["top"])
        assert result is ref  # Returns self for chaining

    def test_fillet_with_list_of_edges(self):
        """Test fillet with multiple edges."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        ref.fillet(["edge1", "edge2"], 1.5)

        mock_client.fillet.assert_called_once_with("MyBox", 1.5, ["edge1", "edge2"])

    def test_chamfer_delegates_to_client(self):
        """Test chamfer method calls client correctly."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        result = ref.chamfer("bottom", 1.0)

        mock_client.chamfer.assert_called_once_with("MyBox", 1.0, ["bottom"])
        assert result is ref

    def test_move_delegates_to_client(self):
        """Test move method calls translate correctly."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        result = ref.move(x=10, y=20, z=30)

        mock_client.translate.assert_called_once_with("MyBox", 10, 20, 30)
        assert result is ref

    def test_rotate_delegates_to_client(self):
        """Test rotate method calls client correctly."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        result = ref.rotate(axis="z", angle=45)

        mock_client.rotate.assert_called_once_with("MyBox", "z", 45)
        assert result is ref

    def test_cut_delegates_to_client(self):
        """Test cut method calls client correctly."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        mock_client.cut.return_value = Mock(data={"object": "CutResult"})
        part = Part("TestPart", client=mock_client)
        base = ObjectRef("Base", part)
        tool = ObjectRef("Tool", part)

        result = base.cut(tool)

        mock_client.cut.assert_called_once_with("Base", "Tool")
        assert result.name == "CutResult"

    def test_cut_with_string_tool(self):
        """Test cut accepts string tool name."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        mock_client.cut.return_value = Mock(data=None)
        part = Part("TestPart", client=mock_client)
        base = ObjectRef("Base", part)

        result = base.cut("ToolName")

        mock_client.cut.assert_called_once_with("Base", "ToolName")
        assert result is base  # Returns self when no result data

    def test_method_chaining(self):
        """Test methods can be chained."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        ref = ObjectRef("MyBox", part)

        # Chain multiple operations
        result = ref.move(10, 0, 0).rotate("z", 45).fillet("top", 1.0)

        assert result is ref
        assert mock_client.translate.called
        assert mock_client.rotate.called
        assert mock_client.fillet.called


class TestPart:
    """Tests for Part context manager."""

    def test_part_with_provided_client(self):
        """Test Part uses provided client."""
        from conjure.builder import Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        assert part._client is mock_client
        assert part._owns_client is False

    def test_part_context_manager_does_not_close_provided_client(self):
        """Test Part doesn't close client it doesn't own."""
        from conjure.builder import Part

        mock_client = Mock()

        with Part("TestPart", client=mock_client):
            pass

        mock_client.close.assert_not_called()

    def test_part_generates_unique_names(self):
        """Test Part generates unique object names."""
        from conjure.builder import Part

        mock_client = Mock()
        part = Part("MyPart", client=mock_client)

        name1 = part._next_name("Box")
        name2 = part._next_name("Box")
        name3 = part._next_name("Cylinder")

        assert name1 == "Box_1"
        assert name2 == "Box_2"
        assert name3 == "Cylinder_3"

    def test_box_creates_object_ref(self):
        """Test box method creates ObjectRef and calls client."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        mock_client.create_box.return_value = Mock(data={"object": "Box_1"})
        part = Part("TestPart", client=mock_client)

        result = part.box(100, 50, 30)

        mock_client.create_box.assert_called_once_with(100, 50, 30, "Box_1", None)
        assert isinstance(result, ObjectRef)
        assert result.name == "Box_1"
        assert result in part._objects

    def test_box_with_custom_name_and_position(self):
        """Test box with explicit name and position."""
        from conjure.builder import Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        part.box(100, 50, 30, name="MyBox", position=[10, 20, 30])

        mock_client.create_box.assert_called_once_with(100, 50, 30, "MyBox", [10, 20, 30])

    def test_cylinder_creates_object_ref(self):
        """Test cylinder method creates ObjectRef."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        result = part.cylinder(10, 50)

        mock_client.create_cylinder.assert_called_once_with(10, 50, "Cylinder_1", None)
        assert isinstance(result, ObjectRef)
        assert result.name == "Cylinder_1"

    def test_sphere_creates_object_ref(self):
        """Test sphere method creates ObjectRef."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        result = part.sphere(25)

        mock_client.create_sphere.assert_called_once_with(25, "Sphere_1", None)
        assert isinstance(result, ObjectRef)

    def test_union_combines_objects(self):
        """Test union method fuses multiple objects."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        obj1 = ObjectRef("Obj1", part)
        obj2 = ObjectRef("Obj2", part)

        result = part.union(obj1, obj2, "String3")

        mock_client.union.assert_called_once_with(["Obj1", "Obj2", "String3"], "Union_1")
        assert isinstance(result, ObjectRef)

    def test_cut_subtracts_objects(self):
        """Test cut method subtracts tool from target."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        target = ObjectRef("Target", part)
        tool = ObjectRef("Tool", part)

        part.cut(target, tool)

        mock_client.cut.assert_called_once_with("Target", "Tool", "Cut_1")

    def test_intersect_finds_common_volume(self):
        """Test intersect method finds intersection."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        obj1 = ObjectRef("Obj1", part)
        obj2 = ObjectRef("Obj2", part)

        part.intersect(obj1, obj2)

        mock_client.intersect.assert_called_once_with(["Obj1", "Obj2"], "Intersect_1")

    def test_slot_creates_box_cutout(self):
        """Test slot is a convenience for box."""
        from conjure.builder import Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        part.slot(width=12, depth=20, length=30, position=[0, 0, 0])

        # slot creates a box: length x width x depth
        mock_client.create_box.assert_called_once_with(30, 12, 20, "Slot_1", [0, 0, 0])

    def test_hole_creates_cylinder_cutout(self):
        """Test hole creates cylinder with diameter conversion."""
        from conjure.builder import Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        part.hole(diameter=10, depth=20, position=[5, 5, 0])

        # hole converts diameter to radius: 10/2 = 5
        mock_client.create_cylinder.assert_called_once_with(5.0, 20, "Hole_1", [5, 5, 0])

    def test_list_objects_delegates_to_client(self):
        """Test list_objects calls client."""
        from conjure.builder import Part

        mock_client = Mock()
        mock_client.list_objects.return_value = [{"name": "Box1"}, {"name": "Cyl1"}]
        part = Part("TestPart", client=mock_client)

        result = part.list_objects()

        mock_client.list_objects.assert_called_once()
        assert len(result) == 2

    def test_measure_delegates_to_client(self):
        """Test measure calls client."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        mock_client.measure.return_value = {"distance": 25.5}
        part = Part("TestPart", client=mock_client)
        obj1 = ObjectRef("Obj1", part)
        obj2 = ObjectRef("Obj2", part)

        result = part.measure(obj1, obj2)

        mock_client.measure.assert_called_once_with("Obj1", "Obj2")
        assert result["distance"] == 25.5

    def test_export_stl_delegates_to_client(self):
        """Test STL export calls client."""
        from conjure.builder import ObjectRef, Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)
        obj1 = ObjectRef("Obj1", part)

        part.export_stl("output.stl", [obj1])

        mock_client.export.assert_called_once_with("stl", "output.stl", ["Obj1"])

    def test_export_step_delegates_to_client(self):
        """Test STEP export calls client."""
        from conjure.builder import Part

        mock_client = Mock()
        part = Part("TestPart", client=mock_client)

        part.export_step("output.step")

        mock_client.export.assert_called_once_with("step", "output.step", None)


class TestPartFunction:
    """Tests for the part() convenience function."""

    def test_part_function_returns_part(self):
        """Test part() creates a Part instance."""
        from conjure.builder import Part, part

        with patch("conjure.builder.ConjureClient"):
            p = part("MyPart", api_key="test", base_url="http://test")

            assert isinstance(p, Part)
            assert p.name == "MyPart"


class TestIntegrationPatterns:
    """Test common usage patterns."""

    def test_build123d_style_workflow(self):
        """Test typical Build123d-style workflow."""
        from conjure.builder import Part

        mock_client = Mock()
        mock_client.create_box.return_value = Mock(data={})
        mock_client.create_cylinder.return_value = Mock(data={})
        mock_client.cut.return_value = Mock(data={"object": "Result"})

        with Part("Holder", client=mock_client) as p:
            # Create base
            base = p.box(100, 50, 30)

            # Create holes
            for i in range(4):
                hole = p.cylinder(5, 40, position=[20 + i * 20, 25, 0])
                base.cut(hole)

            # Add finishing
            base.fillet("top", 2)

        # Verify operations were called
        assert mock_client.create_box.call_count == 1
        assert mock_client.create_cylinder.call_count == 4
        assert mock_client.cut.call_count == 4
        assert mock_client.fillet.call_count == 1

    def test_slot_array_pattern(self):
        """Test creating array of slots."""
        from conjure.builder import Part

        mock_client = Mock()
        mock_client.create_box.return_value = Mock(data={})
        mock_client.cut.return_value = Mock(data={})

        with Part("SlotHolder", client=mock_client) as p:
            base = p.box(100, 50, 30)

            # Create 4 slots
            for i in range(4):
                slot = p.slot(12, 25, position=[10 + i * 22, 25, 5])
                base.cut(slot)

        # 1 base box + 4 slot boxes = 5 create_box calls
        assert mock_client.create_box.call_count == 5

    def test_objects_tracked_in_part(self):
        """Test all created objects are tracked."""
        from conjure.builder import Part

        mock_client = Mock()

        with Part("TrackedPart", client=mock_client) as p:
            p.box(10, 10, 10)
            p.cylinder(5, 20)
            p.sphere(15)

        assert len(p._objects) == 3
        assert p._objects[0].name == "Box_1"
        assert p._objects[1].name == "Cylinder_2"
        assert p._objects[2].name == "Sphere_3"
