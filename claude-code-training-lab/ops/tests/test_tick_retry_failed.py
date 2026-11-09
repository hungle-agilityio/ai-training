"""#149: the tick retries a failed issue up to 3 times when a retry can help. Run: pytest ops"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, REPO
from ops.tests.test_agent_tick import add_run, issue, started
from ops.tests.test_tick_hardening import GitHost

OLD = "1111111aaaaaaa"
NEW = "2222222bbbbbbb"
FILES = "## Files likely touched\n\n- `ops/x.py`\n"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def on_main(head: str) -> dict[str, tuple[int, str]]:
    return {"branch --show-current": (0, "main\n"), "rev-parse origin/main": (0, head + "\n")}


def record(home: Path, number: int) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((home / "failed" / str(number)).read_text())
    return data


def write(home: Path, number: int, **fields: Any) -> None:
    folder = home / "failed"
    folder.mkdir(exist_ok=True)
    data = {"main": OLD, "kind": "stopped", "retries": 0, "outcome": ""} | fields
    (folder / str(number)).write_text(json.dumps(data))


def failed(number: int) -> dict[str, Any]:
    return issue(number, "agent:failed", body=FILES)


def prompt(n: int) -> str:
    return f"Use the work-queue skill for issue #{n} only."


# AC1: the record of a failed build


@pytest.mark.parametrize(
    ("exit_text", "kind"),
    [
        ("timeout", "transient"),
        ("1", "transient"),
        ("no-artifact", "transient"),
        (None, "transient"),
        ("0", "stopped"),
    ],
    ids=["timeout", "error", "no-artifact", "gone", "no-pull-request"],
)
def test_failed_build_writes_a_record_with_main_and_kind(
    home: Path, exit_text: str | None, kind: str
) -> None:
    add_run(home, "issue-1", 77, exit_text=exit_text, log="boom")
    host = GitHost(issues=[issue(1, "agent:running")], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert record(home, 1) | {"outcome": ""} == {
        "main": OLD,
        "kind": kind,
        "retries": 0,
        "outcome": "",
    }


def test_build_that_set_agent_failed_itself_is_stopped(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = GitHost(issues=[issue(1, "agent:failed")], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert record(home, 1)["kind"] == "stopped"


def test_later_failure_keeps_the_retry_count(home: Path) -> None:
    write(home, 1, retries=2)
    add_run(home, "issue-1", 77, exit_text="timeout")
    host = GitHost(issues=[issue(1, "agent:running")], git=on_main(NEW))
    agent_tick.tick_once(host, home)
    assert record(home, 1)["retries"] == 2
    assert record(home, 1)["main"] == NEW


def test_failed_issue_without_a_record_gets_one_and_waits(home: Path) -> None:
    host = GitHost(issues=[failed(1)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert record(home, 1) == {"main": OLD, "kind": "stopped", "retries": 0, "outcome": ""}
    assert started(host) == []


# AC2, AC3: when and how a failed issue is retried


def test_transient_failure_is_retried_at_the_next_free_slot(home: Path) -> None:
    write(home, 1, kind="transient", outcome="stopped after 45 minutes")
    host = GitHost(issues=[failed(1)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]
    assert [
        "gh",
        "issue",
        "edit",
        "1",
        "--add-label",
        "agent:running",
        "--remove-label",
        "agent:ready,agent:failed",
        "--repo",
        REPO,
    ] in host.calls
    assert [
        "gh",
        "issue",
        "comment",
        "1",
        "--body",
        f"{MARKER}\nRetry 1 of 3: the last build stopped after 45 minutes.",
        "--repo",
        REPO,
    ] in host.calls
    assert "rr-test: ReviewRadar retrying #1 (1 of 3)" in host.sent
    assert record(home, 1)["retries"] == 1


def test_stopped_failure_waits_while_main_has_not_moved(home: Path) -> None:
    write(home, 1)
    host = GitHost(issues=[failed(1)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_stopped_failure_is_retried_when_main_moved(home: Path) -> None:
    write(home, 1, retries=1)
    host = GitHost(issues=[failed(1)], git=on_main(NEW))
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(1)]
    assert [
        "gh",
        "issue",
        "comment",
        "1",
        "--body",
        f"{MARKER}\nRetry 2 of 3: main moved from 1111111 to 2222222.",
        "--repo",
        REPO,
    ] in host.calls


def test_unreadable_main_does_not_retry_a_stopped_failure(home: Path) -> None:
    write(home, 1)
    host = GitHost(issues=[failed(1)], git=on_main("fatal: bad revision"))
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_third_retry_is_the_last(home: Path) -> None:
    write(home, 1, kind="transient", retries=3)
    host = GitHost(issues=[failed(1)], git=on_main(NEW))
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_manual_issue_is_never_retried(home: Path) -> None:
    write(home, 1, kind="transient")
    host = GitHost(issues=[issue(1, "agent:failed", "agent:manual", body=FILES)], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_failed_issue_with_an_open_dependency_waits(home: Path) -> None:
    write(home, 2, kind="transient")
    blocked = issue(2, "agent:failed", body=FILES + "\nDepends on #1\n")
    host = GitHost(issues=[issue(1), blocked], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_ready_issues_go_before_failed_ones(home: Path) -> None:
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    write(home, 1, kind="transient")
    ready = issue(5, "agent:ready", body="## Files likely touched\n\n- `ops/y.py`\n")
    host = GitHost(issues=[failed(1), ready], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt(5)]


def test_failed_issue_sharing_a_file_with_a_running_one_waits(home: Path) -> None:
    write(home, 1, kind="transient")
    host = GitHost(issues=[failed(1), issue(2, "agent:running", body=FILES)], git=on_main(OLD))
    add_run(home, "issue-2", 55)
    host.alive_pids.add(55)
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_retry_needs_the_owners_ready_label(home: Path) -> None:
    write(home, 1, kind="transient")
    host = GitHost(issues=[failed(1)], git=on_main(OLD), labeller={1: "stranger"})
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_retry_archives_old_branches_without_a_kept_worktree(home: Path) -> None:
    write(home, 1, kind="transient")
    git = on_main(OLD) | {"branch --list": (0, "task/1-old\n")}
    host = GitHost(issues=[failed(1)], git=git)
    agent_tick.tick_once(host, home)
    renames = host.git_calls("branch -m task/1-old")
    assert renames and renames[0][-1].startswith("archive/task/1-old-")


# AC4: after the third retry


def test_failure_after_three_retries_notifies_once(home: Path) -> None:
    write(home, 1, kind="transient", retries=3)
    add_run(home, "issue-1", 77, exit_text="1")
    host = GitHost(issues=[issue(1, "agent:running")], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    message = (
        f"rr-test: ReviewRadar #1 failed after 3 retries, needs you: "
        f"https://github.com/{REPO}/issues/1"
    )
    assert host.sent.count(message) == 1
    (home / "worktrees" / "issue-1").rmdir()
    host.clock += 600
    add_run(home, "issue-1", 78, exit_text="1")
    agent_tick.tick_once(host, home)
    assert host.sent.count(message) == 1


# AC5: the plan limit is not a failure


def test_plan_limit_changes_no_record(home: Path) -> None:
    write(home, 1, kind="transient", retries=1, outcome="stopped after 45 minutes")
    before = (home / "failed" / "1").read_text()
    add_run(home, "issue-1", 77, exit_text="1", log="You've hit your 5-hour limit")
    host = GitHost(issues=[issue(1, "agent:running")], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    host.issues = [issue(1, "agent:ready")]
    agent_tick.tick_once(host, home)
    assert (home / "failed" / "1").read_text() == before


# AC6: restarted by hand or closed


def test_restart_by_hand_archives_the_record(home: Path) -> None:
    write(home, 1, retries=2)
    host = GitHost(issues=[issue(1, "agent:ready", body=FILES)], git=on_main(OLD))
    log = agent_tick.tick_once(host, home)
    assert not (home / "failed" / "1").exists()
    assert [p.name.startswith("failed-1-") for p in (home / "archive").iterdir()] == [True]
    assert "issue-1: restarted by hand, failure record archived" in log


def test_closed_issue_archives_the_record(home: Path) -> None:
    write(home, 1)
    host = GitHost(issues=[], git=on_main(OLD))
    agent_tick.tick_once(host, home)
    assert not (home / "failed" / "1").exists()
    assert (home / "archive").exists()
