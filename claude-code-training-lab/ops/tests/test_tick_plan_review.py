"""#471: a build that posted its plan waits for the owner; it did not fail. Run: pytest ops"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, REPO
from ops.tests.test_agent_tick import add_run, issue, pull, started
from ops.tests.test_tick_hardening import GitHost

PLAN = "agent:plan-review"
WAITS = f"rr-test: ReviewRadar #1 plan waits for your approval: https://github.com/{REPO}/issues/1"
POSTED = "issue-1: plan posted; waiting for the owner"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def marked_failed(host: GitHost) -> bool:
    return any("agent:failed" in call for call in host.gh_calls("issue", "edit"))


def removed(host: GitHost, home: Path) -> bool:
    remove = ["git", "-C", str(agent_tick.REPO_ROOT), "worktree", "remove"]
    return [*remove, str(home / "worktrees" / "issue-1")] in host.calls


# AC1 (M15): the label is known and its issue is never started


def test_plan_review_is_a_skip_label() -> None:
    assert PLAN in agent_tick.SKIP_LABELS


def test_plan_review_label_has_its_color_and_description() -> None:
    assert agent_tick.LABEL_COLORS[PLAN] == (
        "5319E7",
        "The loop posted a plan and waits for the owner's approval",
    )


def test_ready_issue_with_plan_review_is_not_chosen(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:ready", PLAN)])
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_ready_issue_next_to_a_plan_review_issue_is_still_chosen(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:ready", PLAN), issue(2, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #2 only."]


# AC2 (M16): a build that ended with the plan posted is not a failure


def test_plan_posted_removes_the_worktree(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)])
    agent_tick.tick_once(host, home)
    assert removed(host, home)


def test_plan_posted_worktree_is_removed_as_for_a_build_that_handed_over(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)], git={"worktree remove": (1, "has changes")})
    log = agent_tick.tick_once(host, home)
    assert host.git_calls("worktree remove --force") != []
    assert not any("worktree kept" in line for line in log)


def test_plan_posted_writes_the_log_line(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)])
    log = agent_tick.tick_once(host, home)
    assert log.count(POSTED) == 1
    assert "issue-1: ended normally" not in log


def test_plan_posted_sends_one_notification_with_the_exact_text(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)])
    agent_tick.tick_once(host, home)
    assert host.sent.count(WAITS) == 1
    assert not any("failed" in message or "decision" in message for message in host.sent)


def test_plan_posted_writes_no_failure_record(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)])
    agent_tick.tick_once(host, home)
    assert not (home / "failed" / "1").exists()


def test_plan_posted_adds_no_failed_label_and_no_comment(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)])
    agent_tick.tick_once(host, home)
    assert not marked_failed(host)
    assert host.gh_calls("issue", "comment") == []


def test_plan_posted_is_not_started_again_by_the_same_tick(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, "agent:ready", PLAN)])
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_plan_posted_is_told_once_over_two_ticks(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, PLAN)])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert host.sent.count(WAITS) == 1


# AC3 (M17): every other end without a pull request behaves as before


def test_no_pull_request_and_no_plan_review_is_marked_failed(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, "agent:running")])
    log = agent_tick.tick_once(host, home)
    assert marked_failed(host)
    assert host.gh_calls("issue", "comment")[0][5].startswith(MARKER)
    assert "rr-test: ReviewRadar build for issue #1 failed: ended without a pull request" in (
        host.sent
    )
    assert (home / "failed" / "1").exists()
    assert not removed(host, home)
    assert POSTED not in log and WAITS not in host.sent


def test_still_running_with_plan_review_is_marked_failed(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, "agent:running", PLAN)])
    log = agent_tick.tick_once(host, home)
    assert marked_failed(host)
    assert (home / "failed" / "1").exists()
    assert POSTED not in log and WAITS not in host.sent


def test_own_agent_failed_without_plan_review_is_recorded_as_stopped(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, "agent:failed")])
    log = agent_tick.tick_once(host, home)
    assert (home / "failed" / "1").exists()
    assert "issue-1: ended normally" in log
    assert POSTED not in log and WAITS not in host.sent


def test_plan_review_with_a_pull_request_is_a_normal_hand_over(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(prs=[pull(20, "pr:ready-for-review", closes=1)], issues=[issue(1, PLAN)])
    log = agent_tick.tick_once(host, home)
    assert "issue-1: ended normally" in log
    assert POSTED not in log and WAITS not in host.sent
