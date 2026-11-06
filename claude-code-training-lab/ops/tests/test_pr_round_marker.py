"""A pull request round records its start head; the stop hook then asks for a fresh report."""

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


def round_file(home: Path, key: str) -> Path:
    return home / "worktrees" / key / agent_tick.APP_DIR / "out" / "pr-round.json"


def test_a_pull_request_round_writes_its_start_head(home: Path) -> None:
    host = GitHost(prs=[pull(275, closes=242)], git={"rev-parse HEAD": (0, HEAD + "\n")})
    agent_tick.tick_once(host, home)
    data = json.loads(round_file(home, "pr-275").read_text())
    assert data == {"head": HEAD, "pr": 275}


def test_an_unknown_head_writes_nothing_and_says_so(home: Path) -> None:
    host = GitHost(prs=[pull(275, closes=242)], git={"rev-parse HEAD": (1, "fatal")})
    log = agent_tick.tick_once(host, home)
    assert not round_file(home, "pr-275").exists()
    assert "pr-275: start head unknown; the report check is skipped" in log


def test_an_issue_build_writes_no_round_file(home: Path) -> None:
    body = "## Files likely touched\n\n- `reviews/x.py`\n"
    host = GitHost(issues=[issue(5, "agent:ready", body=body)], git={"rev-parse HEAD": (0, HEAD)})
    agent_tick.tick_once(host, home)
    assert not round_file(home, "issue-5").exists()
