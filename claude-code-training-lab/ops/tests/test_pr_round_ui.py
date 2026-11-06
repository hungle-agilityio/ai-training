"""A pull request round of a needs-ui issue tells the stop hook to ask for fresh screenshots."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import issue, pull
from ops.tests.test_tick_hardening import GitHost

HEAD = "42c3146aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def round_data(home: Path, key: str) -> dict[str, object]:
    path = home / "worktrees" / key / agent_tick.APP_DIR / "out" / "pr-round.json"
    data: dict[str, object] = json.loads(path.read_text())
    return data


def test_a_round_for_a_needs_ui_issue_records_ui(home: Path) -> None:
    host = GitHost(
        prs=[pull(275, closes=242)],
        issues=[issue(242, "agent:review", "needs-ui")],
        git={"rev-parse HEAD": (0, HEAD + "\n")},
    )
    agent_tick.tick_once(host, home)
    assert round_data(home, "pr-275") == {"head": HEAD, "pr": 275, "ui": True}


def test_a_round_for_an_issue_without_needs_ui_records_no_ui(home: Path) -> None:
    host = GitHost(
        prs=[pull(275, closes=242)],
        issues=[issue(242, "agent:review")],
        git={"rev-parse HEAD": (0, HEAD + "\n")},
    )
    agent_tick.tick_once(host, home)
    assert round_data(home, "pr-275") == {"head": HEAD, "pr": 275}


def test_a_pull_request_without_closes_records_no_ui(home: Path) -> None:
    host = GitHost(prs=[pull(275)], git={"rev-parse HEAD": (0, HEAD + "\n")})
    agent_tick.tick_once(host, home)
    assert "ui" not in round_data(home, "pr-275")
