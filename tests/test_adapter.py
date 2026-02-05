"""
Unit tests for the Conjure SDK adapter framework.

Tests cover:
- AdapterResult: ok(), fail(), to_wire(), __bool__
- BaseAdapter: handler registration, execute(), command routing
- BaseEngine: config, get_state()
- Config classes: defaults and inheritance
- ConnectionState enum
- BaseServerClient: message handling, connection state
- AdapterRunner: wiring and delegation
"""

import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add SDK source to path
sdk_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(sdk_src))


class TestAdapterResult:
    """Tests for AdapterResult dataclass."""

    def test_ok_creates_success_result(self):
        """Test ok() creates successful result with data."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.ok(object_id="Box001", volume=1000.0)

        assert result.success is True
        assert result.data == {"object_id": "Box001", "volume": 1000.0}
        assert result.error is None

    def test_ok_creates_success_result_with_no_data(self):
        """Test ok() with no arguments creates empty data dict."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.ok()

        assert result.success is True
        assert result.data == {}
        assert result.error is None

    def test_fail_creates_failed_result_with_error(self):
        """Test fail() creates failed result with error message."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.fail("Object not found")

        assert result.success is False
        assert result.error == "Object not found"
        assert result.data == {}

    def test_fail_creates_failed_result_with_error_and_data(self):
        """Test fail() can include additional error context data."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.fail("Object not found", object_id="Invalid", attempted_name="Box999")

        assert result.success is False
        assert result.error == "Object not found"
        assert result.data == {"object_id": "Invalid", "attempted_name": "Box999"}

    def test_to_wire_success_result(self):
        """Test to_wire() serialization for success result."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.ok(value=42, name="Test")
        wire = result.to_wire()

        assert wire == {
            "success": True,
            "data": {"value": 42, "name": "Test"},
        }
        assert "error" not in wire

    def test_to_wire_failed_result(self):
        """Test to_wire() serialization for failed result with error."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.fail("Something went wrong", detail="Additional info")
        wire = result.to_wire()

        assert wire == {
            "success": False,
            "data": {"detail": "Additional info"},
            "error": "Something went wrong",
        }

    def test_bool_success_result(self):
        """Test __bool__ returns True for successful result."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.ok()

        assert bool(result) is True
        assert result  # Allows use in if statements

    def test_bool_failed_result(self):
        """Test __bool__ returns False for failed result."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult.fail("Error")

        assert bool(result) is False
        assert not result

    def test_default_empty_data_dict(self):
        """Test data defaults to empty dict when not provided."""
        from conjure.adapter.result import AdapterResult

        result = AdapterResult(success=True)

        assert result.data == {}
        assert isinstance(result.data, dict)


class TestBaseAdapter:
    """Tests for BaseAdapter abstract class."""

    def test_register_handler_explicit(self):
        """Test register_handler() explicitly registers a handler."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["test"]

        adapter = TestAdapter()
        mock_handler = Mock(return_value=AdapterResult.ok())

        adapter.register_handler("test_command", mock_handler)

        assert "test_command" in adapter._handlers
        assert adapter._handlers["test_command"] is mock_handler

    def test_register_handlers_by_prefix_auto_discovery(self):
        """Test register_handlers_by_prefix() auto-discovers methods."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_create_box(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def _cmd_create_cylinder(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["primitives"]

        adapter = TestAdapter()

        assert "create_box" in adapter._handlers
        assert "create_cylinder" in adapter._handlers
        assert adapter._handlers["create_box"] == adapter._cmd_create_box
        assert adapter._handlers["create_cylinder"] == adapter._cmd_create_cylinder

    def test_register_handlers_by_prefix_with_custom_prefix(self):
        """Test register_handlers_by_prefix() with custom prefix."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_handle_")

            def _handle_custom_action(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()

        assert "custom_action" in adapter._handlers
        assert adapter._handlers["custom_action"] == adapter._handle_custom_action

    @pytest.mark.asyncio
    async def test_execute_with_sync_handler(self):
        """Test execute() with synchronous handler."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_create_box(self, params: Dict) -> AdapterResult:
                width = params.get("width", 1.0)
                return AdapterResult.ok(object_id="Box001", width=width)

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["primitives"]

        adapter = TestAdapter()
        result = await adapter.execute("create_box", {"width": 10.0})

        assert result.success is True
        assert result.data["object_id"] == "Box001"
        assert result.data["width"] == 10.0

    @pytest.mark.asyncio
    async def test_execute_with_async_handler(self):
        """Test execute() with asynchronous handler."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            async def _cmd_async_operation(self, params: Dict) -> AdapterResult:
                # Simulate async work
                await AsyncMock()()
                return AdapterResult.ok(result="async_complete")

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["async"]

        adapter = TestAdapter()
        result = await adapter.execute("async_operation", {})

        assert result.success is True
        assert result.data["result"] == "async_complete"

    @pytest.mark.asyncio
    async def test_execute_with_unknown_command(self):
        """Test execute() with unknown command returns fail result."""
        from conjure.adapter.base_adapter import BaseAdapter

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        result = await adapter.execute("nonexistent_command", {})

        assert result.success is False
        assert "Unknown command" in result.error
        assert "nonexistent_command" in result.error

    @pytest.mark.asyncio
    async def test_execute_wraps_dict_returns_in_adapter_result(self):
        """Test execute() wraps dict returns in AdapterResult."""
        from conjure.adapter.base_adapter import BaseAdapter

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_legacy_handler(self, params: Dict) -> Dict[str, Any]:
                # Legacy handler that returns dict instead of AdapterResult
                return {"object_id": "Legacy001", "type": "Box"}

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        result = await adapter.execute("legacy_handler", {})

        assert result.success is True
        assert result.data["object_id"] == "Legacy001"
        assert result.data["type"] == "Box"

    @pytest.mark.asyncio
    async def test_execute_handles_handler_exceptions(self):
        """Test execute() catches and wraps handler exceptions."""
        from conjure.adapter.base_adapter import BaseAdapter

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_failing_handler(self, params: Dict):
                raise ValueError("Something went wrong")

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        result = await adapter.execute("failing_handler", {})

        assert result.success is False
        assert "Something went wrong" in result.error

    @pytest.mark.asyncio
    async def test_execute_handles_dict_with_status_error(self):
        """Test execute() handles handler returning dict with status=error."""
        from conjure.adapter.base_adapter import BaseAdapter

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_error_dict_handler(self, params: Dict) -> Dict[str, Any]:
                # Legacy error response format
                return {"status": "error", "error": "Operation failed"}

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        result = await adapter.execute("error_dict_handler", {})

        assert result.success is False
        assert "Operation failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_handles_handler_with_no_return(self):
        """Test execute() handles handler that returns None."""
        from conjure.adapter.base_adapter import BaseAdapter

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_no_return_handler(self, params: Dict):
                # Handler with no return value
                pass

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        result = await adapter.execute("no_return_handler", {})

        assert result.success is True
        assert result.data == {}

    def test_get_supported_commands_returns_registered_commands(self):
        """Test get_supported_commands() returns list of registered commands."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_create_box(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def _cmd_create_cylinder(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def _cmd_boolean_union(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["primitives", "booleans"]

        adapter = TestAdapter()
        commands = adapter.get_supported_commands()

        assert isinstance(commands, list)
        assert "create_box" in commands
        assert "create_cylinder" in commands
        assert "boolean_union" in commands
        assert len(commands) == 3

    def test_get_registration_payload_structure(self):
        """Test get_registration_payload() returns correct structure."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_test_command(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok()

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["primitives", "transforms"]

        adapter = TestAdapter()
        payload = adapter.get_registration_payload()

        assert "capabilities" in payload
        assert "commands" in payload
        assert payload["capabilities"] == ["primitives", "transforms"]
        assert "test_command" in payload["commands"]


class TestBaseEngine:
    """Tests for BaseEngine abstract class."""

    def test_engine_with_default_config(self):
        """Test BaseEngine uses default config when none provided."""
        from conjure.adapter.base_engine import BaseEngine

        class TestEngine(BaseEngine):
            def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
                return {"success": True}

            def health_check(self) -> bool:
                return True

        engine = TestEngine()

        assert engine.config is not None
        assert engine.config.timeout == 30.0

    def test_engine_with_custom_config(self):
        """Test BaseEngine accepts custom config."""
        from conjure.adapter.base_engine import BaseEngine
        from conjure.adapter.config import BaseEngineConfig

        class TestEngine(BaseEngine):
            def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
                return {"success": True}

            def health_check(self) -> bool:
                return True

        custom_config = BaseEngineConfig(timeout=60.0)
        engine = TestEngine(custom_config)

        assert engine.config is custom_config
        assert engine.config.timeout == 60.0

    def test_get_state_delegates_to_execute(self):
        """Test get_state() default implementation calls execute()."""
        from conjure.adapter.base_engine import BaseEngine

        class TestEngine(BaseEngine):
            def __init__(self):
                super().__init__()
                self.execute_called = False
                self.execute_params = None

            def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
                self.execute_called = True
                self.execute_params = command
                return {"objects": [{"name": "Box001"}]}

            def health_check(self) -> bool:
                return True

        engine = TestEngine()
        state = engine.get_state(verbose=True)

        assert engine.execute_called is True
        assert engine.execute_params == {"type": "get_state", "params": {"verbose": True}}
        assert state["objects"][0]["name"] == "Box001"

    def test_get_state_default_verbose_false(self):
        """Test get_state() defaults verbose to False."""
        from conjure.adapter.base_engine import BaseEngine

        class TestEngine(BaseEngine):
            def __init__(self):
                super().__init__()
                self.execute_params = None

            def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
                self.execute_params = command
                return {}

            def health_check(self) -> bool:
                return True

        engine = TestEngine()
        engine.get_state()

        assert engine.execute_params["params"]["verbose"] is False


class TestConfigClasses:
    """Tests for configuration dataclasses."""

    def test_base_engine_config_defaults(self):
        """Test BaseEngineConfig default values."""
        from conjure.adapter.config import BaseEngineConfig

        config = BaseEngineConfig()

        assert config.timeout == 30.0

    def test_base_engine_config_custom_values(self):
        """Test BaseEngineConfig with custom values."""
        from conjure.adapter.config import BaseEngineConfig

        config = BaseEngineConfig(timeout=45.5)

        assert config.timeout == 45.5

    def test_socket_engine_config_defaults(self):
        """Test SocketEngineConfig default values."""
        from conjure.adapter.config import SocketEngineConfig

        config = SocketEngineConfig()

        assert config.host == "localhost"
        assert config.port == 9876
        assert config.recv_buffer_size == 8192
        assert config.timeout == 30.0  # Inherited from BaseEngineConfig

    def test_socket_engine_config_inherits_from_base(self):
        """Test SocketEngineConfig inherits from BaseEngineConfig."""
        from conjure.adapter.config import BaseEngineConfig, SocketEngineConfig

        config = SocketEngineConfig(timeout=60.0, host="192.168.1.100", port=5000)

        assert isinstance(config, BaseEngineConfig)
        assert config.timeout == 60.0
        assert config.host == "192.168.1.100"
        assert config.port == 5000

    def test_socket_engine_config_custom_recv_buffer(self):
        """Test SocketEngineConfig with custom recv_buffer_size."""
        from conjure.adapter.config import SocketEngineConfig

        config = SocketEngineConfig(recv_buffer_size=16384)

        assert config.recv_buffer_size == 16384

    def test_server_client_config_defaults(self):
        """Test ServerClientConfig default values."""
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()

        assert config.server_url == "wss://conjure.lautrek.com/api/v1/adapter/ws"
        assert config.api_key is None
        assert config.adapter_id is None
        assert config.adapter_type == "generic"
        assert config.reconnect_delay == 5.0
        assert config.max_reconnect_attempts == 10
        assert config.heartbeat_interval == 30.0

    def test_server_client_config_custom_values(self):
        """Test ServerClientConfig with custom values."""
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig(
            server_url="wss://custom.example.com/ws",
            api_key="sk_test_123",
            adapter_id="adapter-001",
            adapter_type="freecad",
            reconnect_delay=10.0,
            max_reconnect_attempts=5,
            heartbeat_interval=60.0,
        )

        assert config.server_url == "wss://custom.example.com/ws"
        assert config.api_key == "sk_test_123"
        assert config.adapter_id == "adapter-001"
        assert config.adapter_type == "freecad"
        assert config.reconnect_delay == 10.0
        assert config.max_reconnect_attempts == 5
        assert config.heartbeat_interval == 60.0


class TestConnectionState:
    """Tests for ConnectionState enum."""

    def test_connection_state_enum_values(self):
        """Test ConnectionState enum has all expected values."""
        from conjure.adapter.base_server_client import ConnectionState

        assert ConnectionState.DISCONNECTED == "disconnected"
        assert ConnectionState.CONNECTING == "connecting"
        assert ConnectionState.CONNECTED == "connected"
        assert ConnectionState.RECONNECTING == "reconnecting"

    def test_connection_state_enum_members(self):
        """Test ConnectionState enum members are accessible."""
        from conjure.adapter.base_server_client import ConnectionState

        states = list(ConnectionState)

        assert ConnectionState.DISCONNECTED in states
        assert ConnectionState.CONNECTING in states
        assert ConnectionState.CONNECTED in states
        assert ConnectionState.RECONNECTING in states
        assert len(states) == 4


class TestBaseServerClient:
    """Tests for BaseServerClient WebSocket client."""

    def test_initial_state_is_disconnected(self):
        """Test client starts in DISCONNECTED state."""
        from conjure.adapter.base_server_client import BaseServerClient, ConnectionState
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()
        client = BaseServerClient(config)

        assert client.state == ConnectionState.DISCONNECTED
        assert client.is_connected is False

    def test_is_connected_property_requires_connected_state_and_ws(self):
        """Test is_connected property checks both state and websocket."""
        from conjure.adapter.base_server_client import BaseServerClient, ConnectionState
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()
        client = BaseServerClient(config)

        # Set state to CONNECTED but no websocket
        client._state = ConnectionState.CONNECTED
        assert client.is_connected is False

        # Add websocket
        client._ws = Mock()
        assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_handle_execute_command_routes_to_adapter(self):
        """Test _handle_execute_command routes to adapter."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.base_server_client import BaseServerClient
        from conjure.adapter.config import ServerClientConfig
        from conjure.adapter.result import AdapterResult

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        config = ServerClientConfig()
        adapter = TestAdapter()
        adapter.execute = AsyncMock(return_value=AdapterResult.ok(result="success"))
        client = BaseServerClient(config, adapter=adapter)

        message = {
            "type": "execute_command",
            "request_id": "req-123",
            "command_type": "create_box",
            "params": {"width": 10},
        }

        response = await client._handle_execute_command(message)

        adapter.execute.assert_called_once_with("create_box", {"width": 10})
        assert response["type"] == "command_result"
        assert response["request_id"] == "req-123"
        assert response["success"] is True
        assert response["data"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_handle_execute_command_without_adapter(self):
        """Test _handle_execute_command returns error when no adapter configured."""
        from conjure.adapter.base_server_client import BaseServerClient
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()
        client = BaseServerClient(config, adapter=None)

        message = {
            "type": "execute_command",
            "request_id": "req-456",
            "command_type": "create_box",
            "params": {},
        }

        response = await client._handle_execute_command(message)

        assert response["type"] == "command_result"
        assert response["request_id"] == "req-456"
        assert response["success"] is False
        assert "No adapter configured" in response["error"]

    @pytest.mark.asyncio
    async def test_handle_health_check_returns_adapter_health(self):
        """Test _handle_health_check returns adapter health status."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.base_server_client import BaseServerClient
        from conjure.adapter.config import ServerClientConfig

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        config = ServerClientConfig()
        adapter = TestAdapter()
        client = BaseServerClient(config, adapter=adapter)

        message = {"type": "health_check", "request_id": "health-789"}

        response = await client._handle_health_check(message)

        assert response["type"] == "health_check_response"
        assert response["request_id"] == "health-789"
        assert response["adapter_healthy"] is True

    @pytest.mark.asyncio
    async def test_handle_health_check_without_adapter(self):
        """Test _handle_health_check returns False when no adapter."""
        from conjure.adapter.base_server_client import BaseServerClient
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()
        client = BaseServerClient(config, adapter=None)

        message = {"type": "health_check", "request_id": "health-000"}

        response = await client._handle_health_check(message)

        assert response["adapter_healthy"] is False

    @pytest.mark.asyncio
    async def test_handle_disconnect_changes_state(self):
        """Test _handle_disconnect changes state to DISCONNECTED."""
        from conjure.adapter.base_server_client import BaseServerClient, ConnectionState
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()
        client = BaseServerClient(config)
        client._state = ConnectionState.CONNECTED
        client._ws = Mock()
        client._ws.close = AsyncMock()

        message = {"type": "disconnect"}

        result = await client._handle_disconnect(message)

        assert result is None
        assert client.state == ConnectionState.DISCONNECTED
        assert client._ws is None

    def test_state_property_returns_connection_state(self):
        """Test state property returns current connection state."""
        from conjure.adapter.base_server_client import BaseServerClient, ConnectionState
        from conjure.adapter.config import ServerClientConfig

        config = ServerClientConfig()
        client = BaseServerClient(config)

        assert client.state == ConnectionState.DISCONNECTED

        client._state = ConnectionState.CONNECTING
        assert client.state == ConnectionState.CONNECTING

        client._state = ConnectionState.CONNECTED
        assert client.state == ConnectionState.CONNECTED


class TestAdapterRunner:
    """Tests for AdapterRunner convenience class."""

    def test_runner_constructor_wires_adapter_and_config(self):
        """Test AdapterRunner constructor creates config and client."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.runner import AdapterRunner

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        runner = AdapterRunner(
            adapter,
            server_url="wss://test.example.com/ws",
            api_key="sk_test_key",
            adapter_type="test_type",
            adapter_id="test-id-001",
        )

        assert runner.adapter is adapter
        assert runner.config.server_url == "wss://test.example.com/ws"
        assert runner.config.api_key == "sk_test_key"
        assert runner.config.adapter_type == "test_type"
        assert runner.config.adapter_id == "test-id-001"
        assert runner._client is not None

    def test_runner_uses_default_server_url(self):
        """Test AdapterRunner uses default server URL when not provided."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.runner import AdapterRunner

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        runner = AdapterRunner(adapter)

        assert runner.config.server_url == "wss://conjure.lautrek.com/api/v1/adapter/ws"

    def test_runner_is_connected_property_delegates_to_client(self):
        """Test is_connected property delegates to internal client."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.base_server_client import ConnectionState
        from conjure.adapter.runner import AdapterRunner

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        runner = AdapterRunner(adapter)

        # Initially disconnected
        assert runner.is_connected is False

        # Simulate connection
        runner._client._state = ConnectionState.CONNECTED
        runner._client._ws = Mock()
        assert runner.is_connected is True

    def test_runner_state_property_delegates_to_client(self):
        """Test state property delegates to internal client."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.base_server_client import ConnectionState
        from conjure.adapter.runner import AdapterRunner

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        runner = AdapterRunner(adapter)

        assert runner.state == ConnectionState.DISCONNECTED

        runner._client._state = ConnectionState.CONNECTING
        assert runner.state == ConnectionState.CONNECTING

    @pytest.mark.asyncio
    async def test_runner_run_delegates_to_client(self):
        """Test run() method delegates to internal client."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.runner import AdapterRunner

        class TestAdapter(BaseAdapter):
            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = TestAdapter()
        runner = AdapterRunner(adapter)

        # Mock the client's run method to avoid actual connection
        runner._client.run = AsyncMock()
        runner._client.disconnect = AsyncMock()

        await runner.run()

        runner._client.run.assert_called_once()
        runner._client.disconnect.assert_called_once()


class TestIntegrationPatterns:
    """Test common usage patterns and integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_adapter_lifecycle(self):
        """Test creating adapter, registering handlers, executing commands."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class CADAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                self.register_handlers_by_prefix("_cmd_")

            def _cmd_create_box(self, params: Dict) -> AdapterResult:
                width = params.get("width", 1.0)
                height = params.get("height", 1.0)
                depth = params.get("depth", 1.0)
                return AdapterResult.ok(object_id="Box001", width=width, height=height, depth=depth)

            def _cmd_list_objects(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok(objects=[{"name": "Box001", "type": "Box"}])

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return ["primitives", "queries"]

        adapter = CADAdapter()

        # Execute commands
        result1 = await adapter.execute("create_box", {"width": 10, "height": 20, "depth": 30})
        assert result1.success
        assert result1.data["width"] == 10

        result2 = await adapter.execute("list_objects", {})
        assert result2.success
        assert len(result2.data["objects"]) == 1

        # Get registration payload
        payload = adapter.get_registration_payload()
        assert "create_box" in payload["commands"]
        assert "list_objects" in payload["commands"]
        assert "primitives" in payload["capabilities"]

    def test_adapter_with_mixed_handler_registration(self):
        """Test adapter using both auto-discovery and explicit registration."""
        from conjure.adapter.base_adapter import BaseAdapter
        from conjure.adapter.result import AdapterResult

        class MixedAdapter(BaseAdapter):
            def __init__(self):
                super().__init__()
                # Auto-discover with prefix
                self.register_handlers_by_prefix("_cmd_")
                # Explicit registration
                self.register_handler("custom_operation", self.custom_handler)

            def _cmd_auto_discovered(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok(method="auto")

            def custom_handler(self, params: Dict) -> AdapterResult:
                return AdapterResult.ok(method="explicit")

            def health_check(self) -> bool:
                return True

            def get_capabilities(self) -> List[str]:
                return []

        adapter = MixedAdapter()
        commands = adapter.get_supported_commands()

        assert "auto_discovered" in commands
        assert "custom_operation" in commands

    def test_engine_config_inheritance_pattern(self):
        """Test creating custom engine config that inherits from base."""
        from conjure.adapter.config import BaseEngineConfig

        # Simulate a custom config for a new transport type
        class HTTPEngineConfig(BaseEngineConfig):
            url: str = "http://localhost:8080"
            headers: Dict[str, str] = None

        config = HTTPEngineConfig()
        assert config.timeout == 30.0  # Inherited
        assert config.url == "http://localhost:8080"  # Custom field
