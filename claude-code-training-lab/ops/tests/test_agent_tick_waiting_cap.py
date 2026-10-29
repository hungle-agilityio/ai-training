"""The loop waits once five items wait for review. Run: uv run pytest ops/tests --no-cov"""

from __future__ import annotations

from pathlib import Path

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, issue, pull, started


def test_waiting_cap_is_five() -> None:
    assert agent_tick.WAITING_CAP == 5


def test_four_waiting_items_still_start_a_ready_issue(tmp_path: Path) -> None:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\n")
    host = FakeHost(prs=[pull(n, "pr:ready-for-review") for n in (20, 21, 22)],
                    issues=[issue(3, "agent:running"), issue(4, "agent:ready")])
    agent_tick.tick_once(host, tmp_path)
    assert started(host) == ["Use the work-queue skill for issue #4 only."]


def test_five_waiting_items_start_nothing_new(tmp_path: Path) -> None:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\n")
    host = FakeHost(prs=[pull(n, "pr:ready-for-review") for n in (20, 21, 22, 23)],
                    issues=[issue(3, "agent:running"), issue(4, "agent:ready")])
    agent_tick.tick_once(host, tmp_path)
    assert host.spawned == []
