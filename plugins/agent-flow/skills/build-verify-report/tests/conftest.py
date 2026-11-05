"""The report's coverage gate comes from the project's settings; the tests use a fixed one."""

import pytest


@pytest.fixture(autouse=True)
def coverage_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOW_COVERAGE_INCLUDE", "app/services.py,app/repositories.py")
    monkeypatch.setenv("FLOW_COVERAGE_FAIL_UNDER", "90")
