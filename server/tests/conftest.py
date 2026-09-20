"""Keep the test suite deterministic and independent of developer API keys."""

import pytest

from app.core.settings import settings


@pytest.fixture(autouse=True)
def force_demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "api_key", None)
    monkeypatch.setattr(settings, "demo_mode", True)