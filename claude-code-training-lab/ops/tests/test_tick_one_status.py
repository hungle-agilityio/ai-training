"""#146: an open loop issue carries one status label; the tick keeps it so. Run: pytest ops"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, add_run, issue, pull, started
from ops.tests.test_tick_hardening import GitHost

REPO = agent_tick.REPO


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def edits(host: FakeHost) -> list[list[str]]:
    return host.gh_calls("issue", "edit")


# AC1: starting a build swaps agent:ready for agent:running in one call


def test_start_adds_running_and_removes_ready_in_one_call(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host)
    assert edits(host) == [
        [
            "gh",
            "issue",
            "edit",
            "1",
            "--add-label",
            "agent:running",
            "--remove-label",
            "agent:ready",
            "--repo",
            REPO,
        ]
    ]


# AC2: an issue with an open loop pull request is agent:review alone


@pytest.mark.parametrize(
    "labels",
    [
        ("agent:running",),
        ("agent:ready", "agent:running"),
        ("agent:ready",),
        ("agent:running", "agent:ready", "agent:failed"),
    ],
)
def test_issue_with_open_pull_request_becomes_review_only(
    home: Path, labels: tuple[str, ...]
) -> None:
    host = GitHost(prs=[pull(7, "pr:ready-for-review", closes=1)], issues=[issue(1, *labels)])
    log = agent_tick.tick_once(host, home)
    stale = [x for x in ("agent:running", "agent:ready") if x in labels]
    assert edits(host) == [
        [
            "gh",
            "issue",
            "edit",
            "1",
            "--add-label",
            "agent:review",
            "--remove-label",
            ",".join(stale),
            "--repo",
            REPO,
        ]
    ]
    assert "issue-1: has PR #7, agent:review" in log
    assert started(host) == []


def test_issue_already_review_alone_gets_no_call(home: Path) -> None:
    host = GitHost(
        prs=[pull(7, "pr:ready-for-review", closes=1)], issues=[issue(1, "agent:review")]
    )
    log = agent_tick.tick_once(host, home)
    assert edits(host) == []
    assert not any("has PR" in line for line in log)


def test_review_with_stale_ready_is_one_call_not_two(home: Path) -> None:
    host = GitHost(
        prs=[pull(7, "pr:ready-for-review", closes=1)],
        issues=[issue(1, "agent:ready", "agent:review")],
    )
    agent_tick.tick_once(host, home)
    assert len(edits(host)) == 1


def test_closed_pull_request_does_not_make_an_issue_review(home: Path) -> None:
    host = GitHost(prs=[pull(7, state="MERGED", closes=1)], issues=[issue(1, "agent:running")])
    agent_tick.tick_once(host, home)
    assert not any("agent:review" in c and "--add-label" in c for c in edits(host))


# AC3: a build that ends without a pull request is agent:failed alone


def test_failed_build_swaps_running_and_ready_for_failed_in_one_call(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:ready", "agent:running")])
    add_run(home, "issue-1", 4242, exit_text="1")
    agent_tick.tick_once(host, home)
    assert [
        "gh",
        "issue",
        "edit",
        "1",
        "--add-label",
        "agent:failed",
        "--remove-label",
        "agent:running,agent:ready",
        "--repo",
        REPO,
    ] in host.calls


def test_failed_alone_or_unlabelled_issue_is_never_started(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:failed"), issue(2)])
    agent_tick.tick_once(host, home)
    assert started(host) == []


# AC4: the plan limit sends the issue back to agent:ready alone


def test_plan_limit_returns_issue_to_ready_alone(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:running")])
    add_run(home, "issue-1", 4242, exit_text="1", log="You hit your usage_limit")
    agent_tick.tick_once(host, home)
    assert [
        "gh",
        "issue",
        "edit",
        "1",
        "--add-label",
        "agent:ready",
        "--remove-label",
        "agent:running",
        "--repo",
        REPO,
    ] in host.calls
    assert not any("agent:failed" in c for c in host.calls)


# AC5: an old agent:ready + agent:failed issue is left alone


def test_ready_and_failed_together_is_left_alone(home: Path) -> None:
    host = GitHost(issues=[issue(2, "agent:ready", "agent:failed")])
    agent_tick.tick_once(host, home)
    assert edits(host) == []
