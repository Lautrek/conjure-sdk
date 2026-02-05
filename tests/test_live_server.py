"""Integration tests against the live Conjure server.

These tests verify the SDK works correctly against the deployed server at
https://conjure.lautrek.com. They require a valid API key set in the
CONJURE_API_KEY environment variable.

Run with:
    export CONJURE_API_KEY="cj_your_key_here"
    pytest tests/test_live_server.py -v

Note: These tests only verify authentication and basic connectivity.
CAD operations require a FreeCAD adapter connection and are not tested here.
"""

import httpx
import pytest
from conftest import requires_live_server

# =============================================================================
# Health & Info Tests (No Auth Required)
# =============================================================================


@pytest.mark.live
def test_health_endpoint(base_url):
    """Test that the health endpoint is accessible."""
    response = httpx.get(f"{base_url}/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"


@pytest.mark.live
def test_info_endpoint(base_url):
    """Test that the info endpoint returns server information."""
    response = httpx.get(f"{base_url}/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data or "name" in data


# =============================================================================
# Authentication Tests
# =============================================================================


@pytest.mark.live
@requires_live_server
def test_valid_api_key_authenticates(api_key, base_url):
    """Test that a valid API key successfully authenticates."""
    response = httpx.get(
        f"{base_url}/api/v1/auth/user",
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "tier" in data


@pytest.mark.live
def test_invalid_api_key_returns_401(base_url, invalid_api_key):
    """Test that an invalid API key returns 401 Unauthorized."""
    response = httpx.get(
        f"{base_url}/api/v1/auth/user",
        headers={"X-API-Key": invalid_api_key},
    )
    assert response.status_code == 401


@pytest.mark.live
def test_missing_api_key_returns_error(base_url):
    """Test that a missing API key returns 401 or 403."""
    response = httpx.get(f"{base_url}/api/v1/auth/user")
    assert response.status_code in (401, 403)


# =============================================================================
# Client Initialization Tests
# =============================================================================


@pytest.mark.live
@requires_live_server
def test_client_initialization(api_key, base_url):
    """Test that the client initializes correctly."""
    from conjure import ConjureClient

    client = ConjureClient(api_key=api_key, base_url=base_url)
    assert client.api_key == api_key
    assert client.base_url == base_url
    client.close()


@pytest.mark.live
def test_client_requires_api_key(base_url):
    """Test that client raises error without API key."""
    # Clear env var temporarily
    import os

    from conjure import ConjureClient
    from conjure.exceptions import AuthenticationError

    old_key = os.environ.pop("CONJURE_API_KEY", None)

    try:
        with pytest.raises(AuthenticationError):
            ConjureClient(base_url=base_url)
    finally:
        if old_key:
            os.environ["CONJURE_API_KEY"] = old_key


@pytest.mark.live
def test_client_requires_base_url(api_key):
    """Test that client raises error without base URL."""
    # Clear env var temporarily
    import os

    from conjure import ConjureClient

    old_url = os.environ.pop("CONJURE_API_URL", None)

    try:
        with pytest.raises(ValueError, match="base_url required"):
            ConjureClient(api_key=api_key)
    finally:
        if old_url:
            os.environ["CONJURE_API_URL"] = old_url


# =============================================================================
# Context Manager Tests
# =============================================================================


@pytest.mark.live
@requires_live_server
def test_client_context_manager(api_key, base_url):
    """Test that the client works as a context manager."""
    from conjure import ConjureClient

    with ConjureClient(api_key=api_key, base_url=base_url) as client:
        assert client is not None
        # Client should be usable inside context


# =============================================================================
# Async Client Tests
# =============================================================================


@pytest.mark.live
@pytest.mark.asyncio
@requires_live_server
async def test_async_client_initialization(api_key, base_url):
    """Test that the async client initializes correctly."""
    from conjure import AsyncConjureClient

    async with AsyncConjureClient(api_key=api_key, base_url=base_url) as client:
        assert client.api_key == api_key
        assert client.base_url == base_url


# =============================================================================
# Usage Endpoint Tests
# =============================================================================


@pytest.mark.live
@requires_live_server
def test_usage_endpoint(api_key, base_url):
    """Test that the usage endpoint returns rate limit info."""
    response = httpx.get(
        f"{base_url}/api/v1/usage",
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    data = response.json()
    # Should have usage information
    assert "operations_used" in data or "usage" in data or "rate_limit" in data


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.live
def test_not_found_returns_404(api_key, base_url):
    """Test that non-existent endpoints return 404."""
    response = httpx.get(
        f"{base_url}/api/v1/nonexistent-endpoint",
        headers={"X-API-Key": api_key} if api_key else {},
    )
    assert response.status_code == 404
