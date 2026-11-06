"""A new pull request waits for the issue build that opened it. Run: uv run pytest ops/tests"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, add_run, home, pull, started

__all__ = ["home"]


def test_pull_request_waits_while_its_issue_build_runs(
    home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    add_run(home, "issue-5", 77)
    host = FakeHost(prs=[pull(20, closes=5)], alive_pids={77})
    agent_tick.tick_once(host, home)
    assert "pr-20" not in started(host)
    assert not any(c[3:5] == ["worktree", "add"] for c in host.calls if c[0] == "git")
    assert not (home / "start-failed" / "pr-20").exists()
    assert not any("did not start" in sent for sent in host.sent)
    assert "pr-20: waits for issue-5 to end" in capsys.readouterr().out


def test_pull_request_starts_once_its_issue_build_ended(home: Path) -> None:
    host = FakeHost(prs=[pull(20, closes=5)])
    agent_tick.tick_once(host, home)
    assert any("pull request #20" in arg for args in host.spawned for arg in args)


def test_other_start_failures_still_raise_the_alarm(home: Path) -> None:
    host = FakeHost(prs=[pull(20, closes=5)], fail="worktree add")
    agent_tick.tick_once(host, home)
    assert (home / "start-failed" / "pr-20").exists()
    assert any("pull request #20 did not start" in sent for sent in host.sent)
