"""#164: the tick has no pull request limit. Run: uv run pytest ops"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, issue, pull, started


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def body(path: str) -> str:
    return f"## Files likely touched\n\n- `{path}`\n"


# AC1: no limit on open pull requests


def test_ready_issues_start_with_many_open_pull_requests(home: Path) -> None:
    prs = [pull(n, "pr:ready-for-review", closes=100 + n) for n in range(20, 45)]
    host = FakeHost(
        prs=prs,
        issues=[
            issue(4, "agent:ready", body=body("a.py")),
            issue(5, "agent:ready", body=body("b.py")),
        ],
    )
    agent_tick.tick_once(host, home)
    assert started(host) == [
        "Use the work-queue skill for issue #4 only.",
        "Use the work-queue skill for issue #5 only.",
    ]


def test_the_limit_is_gone_from_the_code() -> None:
    assert not hasattr(agent_tick, "WAITING_CAP")


def test_blocked_message_is_sent_with_many_open_pull_requests(home: Path) -> None:
    prs = [pull(100 + n, "pr:ready-for-review", closes=50 + n) for n in range(12)]
    host = FakeHost(
        prs=prs, issues=[issue(4, "agent:running"), issue(5, "agent:ready", body="Depends on #4\n")]
    )
    agent_tick.tick_once(host, home)
    assert len(host.sent) == 1
    assert host.sent[0].startswith("rr-test: ReviewRadar waiting: 1 ready issues blocked")
    assert "limit" not in host.sent[0]


# AC2: queue empty only when no ready issue is left


def test_no_ready_issue_left_sends_queue_empty(home: Path) -> None:
    prs = [pull(n, "pr:ready-for-review", closes=100 + n) for n in range(20, 32)]
    host = FakeHost(prs=prs, issues=[issue(1, "agent:review")])
    agent_tick.tick_once(host, home)
    assert host.sent == ["rr-test: ReviewRadar queue empty, 12 pull requests waiting"]


def test_ready_issue_held_by_a_skip_label_does_not_block_queue_empty(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready", "agent:review")])
    agent_tick.tick_once(host, home)
    assert host.sent == ["rr-test: ReviewRadar queue empty, 0 pull requests waiting"]


# AC3: up to 100 pull requests are read


def test_pull_request_list_reads_one_hundred(home: Path) -> None:
    host = FakeHost()
    agent_tick.tick_once(host, home)
    call = host.gh_calls("pr", "list")[0]
    assert call[call.index("--limit") + 1] == "100"
