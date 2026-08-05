import os
from collections.abc import Generator

import pytest

from search_trends.core.config import get_settings

TEST_ADMIN_TOKEN = "test-admin-token-123456789"

# Force a known admin token before any application module is imported (some modules
# build a Settings-dependent app at import time), so collection never depends on
# ADMIN_TOKEN exported in the shell or sourced from .env.
os.environ["ADMIN_TOKEN"] = TEST_ADMIN_TOKEN
get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    monkeypatch.setenv("ADMIN_TOKEN", TEST_ADMIN_TOKEN)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def admin_token() -> str:
    return TEST_ADMIN_TOKEN
