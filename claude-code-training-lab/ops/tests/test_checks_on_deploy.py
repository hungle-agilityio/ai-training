"""A release moves `deploy`, and Render deploys it only after Checks ran on that push."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_checks_run_on_a_push_to_deploy() -> None:
    text = (ROOT / ".github" / "workflows" / "checks.yml").read_text()

    assert "branches: [main, deploy]" in text
    assert "pull_request:" in text
