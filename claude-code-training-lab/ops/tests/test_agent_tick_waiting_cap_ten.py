"""The loop waits once ten items wait for review. Run: uv run pytest ops/tests --no-cov"""

from __future__ import annotations

from pathlib import Path

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, issue, pull, started
from ops.tests.test_tick_notify_cases import NotifyHost, messages


def test_nine_waiting_items_start_the_ready_issue(tmp_path: Path) -> None:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\n")
    host = FakeHost(prs=[pull(n, "pr:ready-for-review") for n in range(20, 29)],
                    issues=[issue(4, "agent:ready")])
    agent_tick.tick_once(host, tmp_path)
    assert started(host) == ["Use the work-queue skill for issue #4 only."]


def test_ten_waiting_items_start_nothing_new(tmp_path: Path) -> None:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\n")
    host = FakeHost(prs=[pull(n, "pr:ready-for-review") for n in range(20, 30)],
                    issues=[issue(4, "agent:ready")])
    agent_tick.tick_once(host, tmp_path)
    assert host.spawned == []


def test_ten_waiting_items_send_the_waiting_message(tmp_path: Path) -> None:
    prs = [pull(n, "pr:ready-for-review") for n in range(20, 30)]
    host = NotifyHost(prs=prs, issues=[issue(1, "agent:ready"), issue(2, "agent:ready")])
    agent_tick.tick_once(host, tmp_path)
    assert messages(host, "waiting") == [
        "ReviewRadar waiting: 10 pull requests open (limit 10), 2 ready issues not started\n"
        + agent_tick.OPEN_PRS_URL
    ]
