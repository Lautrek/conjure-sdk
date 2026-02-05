"""Pytest configuration and fixtures for SDK testing."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Check for live server credentials
CONJURE_API_KEY = os.environ.get("CONJURE_API_KEY")
CONJURE_BASE_URL = os.environ.get("CONJURE_BASE_URL", "https://conjure.lautrek.com")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "live: tests requiring live server connection")


# Skip decorator for tests requiring live server
requires_live_server = pytest.mark.skipif(
    not CONJURE_API_KEY,
    reason="CONJURE_API_KEY environment variable not set",
)


@pytest.fixture
def api_key():
    """Provide API key for tests."""
    if not CONJURE_API_KEY:
        pytest.skip("CONJURE_API_KEY not set")
    return CONJURE_API_KEY


@pytest.fixture
def base_url():
    """Provide base URL for tests."""
    return CONJURE_BASE_URL


@pytest.fixture
def client(api_key, base_url):
    """Create a sync client for testing."""
    from conjure import ConjureClient

    with ConjureClient(api_key=api_key, base_url=base_url) as c:
        yield c


@pytest.fixture
async def async_client(api_key, base_url):
    """Create an async client for testing."""
    from conjure import AsyncConjureClient

    async with AsyncConjureClient(api_key=api_key, base_url=base_url) as c:
        yield c


@pytest.fixture
def invalid_api_key():
    """Provide an invalid API key for error testing."""
    return "cj_invalid_key_for_testing_12345"
