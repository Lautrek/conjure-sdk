#!/usr/bin/env python3
"""Validation script for the Conjure SDK adapter framework.

This script validates that all components of the adapter framework
are correctly implemented and importable.
"""

import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all framework components can be imported."""
    print("Testing imports...")

    # Adapter package
    from conjure.adapter import (
        AdapterResult,
        AdapterRunner,
        BaseAdapter,
        BaseEngine,
        BaseEngineConfig,
        BaseServerClient,
        ConnectionState,
        ServerClientConfig,
        SocketEngineConfig,
    )

    # Protocol package
    from conjure.protocol import (
        Capability,
        CommandEnvelope,
        CommandResponse,
        HeartbeatPayload,
        RegistrationPayload,
    )

    # Transport package
    from conjure.transport import SocketClientMixin, SocketServerMixin

    print("✓ All imports successful")


def test_adapter_result():
    """Test AdapterResult functionality."""
    print("\nTesting AdapterResult...")
    from conjure.adapter import AdapterResult

    # Test success case
    result = AdapterResult.ok(object_id="Box001", volume=1000.0)
    assert result.success
    assert result.data["object_id"] == "Box001"
    assert result.error is None

    # Test failure case
    result = AdapterResult.fail("Test error", code=404)
    assert not result.success
    assert result.error == "Test error"

    # Test wire serialization
    result = AdapterResult.ok(value=42)
    wire = result.to_wire()
    assert wire["success"] is True
    assert wire["data"]["value"] == 42

    # Test boolean context
    assert AdapterResult.ok()
    assert not AdapterResult.fail("error")

    print("✓ AdapterResult tests passed")


def test_base_adapter():
    """Test BaseAdapter functionality."""
    print("\nTesting BaseAdapter...")
    import asyncio

    from conjure.adapter import AdapterResult, BaseAdapter

    class TestAdapter(BaseAdapter):
        def __init__(self):
            super().__init__()
            self.register_handlers_by_prefix("_cmd_")

        def _cmd_test_sync(self, params):
            return AdapterResult.ok(message="sync")

        async def _cmd_test_async(self, params):
            return AdapterResult.ok(message="async")

        def health_check(self):
            return True

        def get_capabilities(self):
            return ["primitives"]

    adapter = TestAdapter()

    # Test handler registration
    assert "test_sync" in adapter.get_supported_commands()
    assert "test_async" in adapter.get_supported_commands()

    # Test sync handler
    result = asyncio.run(adapter.execute("test_sync", {}))
    assert result.success
    assert result.data["message"] == "sync"

    # Test async handler
    result = asyncio.run(adapter.execute("test_async", {}))
    assert result.success
    assert result.data["message"] == "async"

    # Test unknown command
    result = asyncio.run(adapter.execute("unknown", {}))
    assert not result.success

    # Test capabilities
    assert adapter.health_check()
    assert adapter.get_capabilities() == ["primitives"]

    # Test registration payload
    payload = adapter.get_registration_payload()
    assert "capabilities" in payload
    assert "commands" in payload

    print("✓ BaseAdapter tests passed")


def test_protocol_types():
    """Test protocol message types."""
    print("\nTesting protocol types...")
    from conjure.protocol import (
        Capability,
        CommandEnvelope,
        CommandResponse,
        HeartbeatPayload,
        RegistrationPayload,
    )

    # Test CommandEnvelope
    envelope = CommandEnvelope.from_wire({"type": "create_box", "params": {"width": 10}, "request_id": "req_123"})
    assert envelope.type == "create_box"
    assert envelope.params["width"] == 10
    assert envelope.request_id == "req_123"

    # Test CommandResponse
    response = CommandResponse(success=True, data={"value": 42}, request_id="req_123")
    wire = response.to_wire()
    assert wire["success"] is True
    assert wire["request_id"] == "req_123"

    # Test RegistrationPayload
    reg = RegistrationPayload(adapter_type="test", capabilities=["primitives"], commands=["create_box"])
    wire = reg.to_wire()
    assert wire["type"] == "adapter_registration"
    assert wire["adapter_type"] == "test"

    # Test HeartbeatPayload
    hb = HeartbeatPayload(adapter_id="adapter_001", status="available")
    wire = hb.to_wire()
    assert wire["type"] == "heartbeat"
    assert wire["adapter_id"] == "adapter_001"

    # Test Capability constants
    assert Capability.PRIMITIVES == "primitives"
    assert Capability.BOOLEANS == "booleans"
    assert Capability.validate("primitives")
    assert not Capability.validate("invalid")

    print("✓ Protocol types tests passed")


def test_configuration():
    """Test configuration dataclasses."""
    print("\nTesting configuration...")
    from conjure.adapter import (
        BaseEngineConfig,
        ServerClientConfig,
        SocketEngineConfig,
    )

    # Test BaseEngineConfig
    config = BaseEngineConfig(timeout=60.0)
    assert config.timeout == 60.0

    # Test SocketEngineConfig
    config = SocketEngineConfig(host="localhost", port=9876, timeout=30.0)
    assert config.host == "localhost"
    assert config.port == 9876
    assert config.timeout == 30.0

    # Test ServerClientConfig
    config = ServerClientConfig(server_url="wss://example.com", api_key="test_key", adapter_type="test")
    assert config.server_url == "wss://example.com"
    assert config.api_key == "test_key"

    print("✓ Configuration tests passed")


def test_transport_mixins():
    """Test transport mixin interfaces."""
    print("\nTesting transport mixins...")
    from conjure.transport import SocketClientMixin, SocketServerMixin

    # Test SocketClientMixin attributes
    class TestClient(SocketClientMixin):
        pass

    client = TestClient()
    assert hasattr(client, "socket_connect")
    assert hasattr(client, "socket_send")
    assert hasattr(client, "socket_receive")
    assert hasattr(client, "socket_execute")
    assert hasattr(client, "socket_health_check")
    assert client._socket_host == "localhost"
    assert client._socket_port == 9876

    # Test SocketServerMixin attributes
    class TestServer(SocketServerMixin):
        pass

    server = TestServer()
    assert hasattr(server, "server_init")
    assert hasattr(server, "server_start")
    assert hasattr(server, "server_stop")
    assert hasattr(server, "server_process_queue")

    print("✓ Transport mixin tests passed")


def test_connection_state():
    """Test ConnectionState enum."""
    print("\nTesting ConnectionState...")
    from conjure.adapter import ConnectionState

    assert ConnectionState.DISCONNECTED == "disconnected"
    assert ConnectionState.CONNECTING == "connecting"
    assert ConnectionState.CONNECTED == "connected"
    assert ConnectionState.RECONNECTING == "reconnecting"

    print("✓ ConnectionState tests passed")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Conjure SDK Adapter Framework Validation")
    print("=" * 60)

    try:
        test_imports()
        test_adapter_result()
        test_base_adapter()
        test_protocol_types()
        test_configuration()
        test_transport_mixins()
        test_connection_state()

        print("\n" + "=" * 60)
        print("✓ ALL VALIDATION TESTS PASSED")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n✗ VALIDATION FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
