"""#143: the tick tidies ended pull requests itself and says which ready issues wait, and why."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, issue, pull, started


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


@dataclass
class WaitingHost(FakeHost):
    """Adds closed issues and the state reason of an issue."""

    closed: list[dict[str, Any]] = field(default_factory=list)
    reasons: dict[int, str] = field(default_factory=dict)

    def answer(self, args: list[str]) -> Any:
        if args[:2] == ["issue", "list"] and "closed" in args:
            return self.closed
        if args[:2] == ["issue", "view"] and "stateReason" in args:
            number = int(args[2])
            return {"stateReason": self.reasons[number]} if number in self.reasons else {}
        return super().answer(args)


def files(*paths: str) -> str:
    return "## Files likely touched\n\n" + "\n".join(f"- `{path}`" for path in paths) + "\n"


def depends(*numbers: int) -> str:
    return "Depends on " + ", ".join(f"#{n}" for n in numbers) + "\n" + files("a.py")


def blocked(host: FakeHost) -> list[str]:
    """The AC4 messages; the limit and queue-empty messages are other rules."""
    return [m for m in host.sent if "ready issues blocked" in m]


def removed(host: FakeHost, *start: str) -> list[list[str]]:
    return [c for c in host.gh_calls(*start) if "--remove-label" in c]


# AC1


@pytest.mark.parametrize("state", ["MERGED", "CLOSED"])
def test_ended_pull_request_loses_pr_labels_and_its_issue_loses_agent_review(
    home: Path, state: str
) -> None:
    host = WaitingHost(
        prs=[pull(20, "pr:ready-for-review", "pr:blocked", state=state, closes=6)],
        issues=[issue(6, "agent:review")],
    )
    log = agent_tick.tick_once(host, home)
    pr_edit = removed(host, "pr", "edit")[0]
    assert pr_edit[3] == "20"
    assert pr_edit[pr_edit.index("--remove-label") + 1] == "pr:blocked,pr:ready-for-review"
    issue_edit = removed(host, "issue", "edit")[0]
    assert issue_edit[3:6] == ["6", "--remove-label", "agent:review"]
    assert "pr-20: tidied, labels removed" in log
    assert host.spawned == []


def test_ended_pull_request_without_labels_is_left_alone(home: Path) -> None:
    host = WaitingHost(prs=[pull(20, state="MERGED", closes=7)], issues=[issue(7)])
    log = agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "edit") == []
    assert not any("tidied" in line for line in log)


# AC2


def test_two_merged_pull_requests_do_not_take_the_slots(home: Path) -> None:
    host = WaitingHost(
        prs=[
            pull(20, "pr:ready-for-review", state="MERGED", closes=1),
            pull(21, "pr:ready-for-review", state="MERGED", closes=2),
        ],
        issues=[
            issue(1, "agent:review"),
            issue(2, "agent:review"),
            issue(8, "agent:ready", body=files("a.py"), created="2026-10-08T00:00:00Z"),
            issue(9, "agent:ready", body=files("b.py"), created="2026-10-09T00:00:00Z"),
        ],
    )
    agent_tick.tick_once(host, home)
    assert started(host) == [
        "Use the work-queue skill for issue #8 only.",
        "Use the work-queue skill for issue #9 only.",
    ]


# AC3


def test_dependency_closed_as_completed_counts_as_done(home: Path) -> None:
    host = WaitingHost(issues=[issue(5, "agent:ready", body=depends(4))], reasons={4: "COMPLETED"})
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #5 only."]


def test_dependency_with_unreadable_reason_counts_as_done(home: Path) -> None:
    host = WaitingHost(issues=[issue(5, "agent:ready", body=depends(4))])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #5 only."]


def test_dependency_closed_as_not_planned_does_not_start_the_issue(home: Path) -> None:
    host = WaitingHost(
        issues=[issue(5, "agent:ready", body=depends(4))], reasons={4: "NOT_PLANNED"}
    )
    agent_tick.tick_once(host, home)
    assert host.spawned == []


# AC4, AC8


def test_message_names_the_pull_request_to_review(home: Path) -> None:
    host = WaitingHost(
        prs=[pull(30, "pr:ready-for-review", closes=4)],
        issues=[issue(4, "agent:review"), issue(5, "agent:ready", body=depends(4))],
    )
    log = agent_tick.tick_once(host, home)
    assert blocked(host) == [
        "rr-test: ReviewRadar waiting: 1 ready issues blocked\n#5 waits for #4: review PR #30"
    ]
    assert "#5 waits for #4: review PR #30" in log


def test_message_says_building_no_pull_request_and_not_planned(home: Path) -> None:
    host = WaitingHost(
        issues=[
            issue(2, "agent:running", body=files("z.py")),
            issue(3, "agent:ready", body="Depends on #2\n" + files("a.py")),
            issue(6, "agent:ready", body="Depends on #7\n" + files("b.py")),
            issue(7, body=files("c.py")),
            issue(9, "agent:ready", body="Depends on #1\n" + files("d.py")),
        ],
        reasons={1: "NOT_PLANNED"},
    )
    agent_tick.tick_once(host, home)
    assert blocked(host) == [
        "rr-test: ReviewRadar waiting: 3 ready issues blocked\n"
        "#3 waits for #2: building\n"
        "#6 waits for #7: no pull request yet\n"
        "#9 waits for #1: closed as not planned, remove the dependency or reopen it"
    ]


def test_message_has_one_line_per_blocking_issue_ordered_by_number(home: Path) -> None:
    host = WaitingHost(
        issues=[
            issue(2, body=files("z.py")),
            issue(3, body=files("z.py")),
            issue(5, "agent:ready", body="Depends on #3, #2\n" + files("a.py")),
        ],
    )
    agent_tick.tick_once(host, home)
    assert blocked(host)[0].splitlines()[1:] == [
        "#5 waits for #2: no pull request yet",
        "#5 waits for #3: no pull request yet",
    ]


def test_message_for_a_shared_file(home: Path) -> None:
    host = WaitingHost(
        issues=[
            issue(1, "agent:review", body=files("reviews/services.py")),
            issue(2, "agent:ready", body=files("reviews/services.py")),
        ],
    )
    log = agent_tick.tick_once(host, home)
    line = "#2 waits for #1, which also touches reviews/services.py"
    assert blocked(host) == [f"rr-test: ReviewRadar waiting: 1 ready issues blocked\n{line}"]
    assert line in log


def test_issue_not_labelled_ready_by_the_owner_is_not_in_the_message(home: Path) -> None:
    host = WaitingHost(
        issues=[issue(4, body=files("z.py")), issue(5, "agent:ready", body=depends(4))],
        labeller={5: "someone-else"},
    )
    agent_tick.tick_once(host, home)
    assert blocked(host) == []


@pytest.mark.parametrize("label", ["agent:failed", "agent:manual", "agent:review"])
def test_skipped_issue_is_not_in_the_message(home: Path, label: str) -> None:
    host = WaitingHost(issues=[issue(4), issue(5, "agent:ready", label, body=depends(4))])
    agent_tick.tick_once(host, home)
    assert blocked(host) == []


# AC5


def test_message_is_sent_again_only_when_its_text_changes(home: Path) -> None:
    def tick(pr_number: int) -> WaitingHost:
        host = WaitingHost(
            prs=[pull(pr_number, "pr:ready-for-review", closes=4)],
            issues=[issue(4, "agent:review"), issue(5, "agent:ready", body=depends(4))],
        )
        agent_tick.tick_once(host, home)
        return host

    assert len(blocked(tick(30))) == 1
    assert blocked(tick(30)) == []
    assert "review PR #31" in blocked(tick(31))[0]


def test_message_is_sent_while_a_build_runs(home: Path) -> None:
    run = home / "runs" / "issue-9"
    run.mkdir(parents=True)
    (run / "pid").write_text("77")
    (home / "worktrees" / "issue-9").mkdir(parents=True)
    host = WaitingHost(
        issues=[
            issue(9, "agent:running", body=files("z.py")),
            issue(5, "agent:ready", body="Depends on #9\n" + files("a.py")),
        ],
        alive_pids={77},
    )
    agent_tick.tick_once(host, home)
    assert blocked(host) == [
        "rr-test: ReviewRadar waiting: 1 ready issues blocked\n#5 waits for #9: building"
    ]


def test_nothing_blocked_removes_last_blocked_and_sends_nothing(home: Path) -> None:
    (home / "last-blocked").write_text("old text")
    host = WaitingHost(issues=[issue(5, "agent:ready", body=files("a.py"))])
    agent_tick.tick_once(host, home)
    assert not (home / "last-blocked").exists()
    assert blocked(host) == []


# AC7


def test_closed_issue_loses_agent_ready(home: Path) -> None:
    host = WaitingHost(closed=[issue(3, "agent:ready") | {"state": "CLOSED"}])
    log = agent_tick.tick_once(host, home)
    edit = removed(host, "issue", "edit")[0]
    assert edit[3:6] == ["3", "--remove-label", "agent:ready"]
    assert "issue-3: closed, agent:ready removed" in log


def test_open_issue_keeps_agent_ready(home: Path) -> None:
    host = WaitingHost(
        issues=[issue(3, "agent:ready", body=files("a.py"))],
        closed=[issue(3, "agent:ready") | {"state": "OPEN"}],
    )
    log = agent_tick.tick_once(host, home)
    assert "issue-3: closed, agent:ready removed" not in log
