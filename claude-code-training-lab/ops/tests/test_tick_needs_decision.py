"""#260: a build that needs the owner's decision is not retried. Run: pytest ops"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, REPO
from ops.tests.test_agent_tick import NOW, add_run, comment, issue, started
from ops.tests.test_tick_hardening import GitHost

OLD = "1111111aaaaaaa"
NEW = "2222222bbbbbbb"
ASK = f"{MARKER}\n<!-- needs-decision -->\nAC2 and AC4 contradict each other."
BEGAN = int(NOW) - 600  # the run started 10 minutes before the tick
AFTER = "2027-01-15T07:55:00Z"  # epoch 1_800_000_000 is 2027-01-15T08:00:00Z
BEFORE = "2027-01-15T07:00:00Z"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def on_main(head: str) -> dict[str, tuple[int, str]]:
    return {"branch --show-current": (0, "main\n"), "rev-parse origin/main": (0, head + "\n")}


def ended(home: Path, exit_text: str = "0", began: bool = True) -> None:
    run = add_run(home, "issue-1", 77, exit_text=exit_text)
    if began:
        (run / "started").write_text(str(BEGAN))


def asking(when: str, body: str = ASK) -> dict[int, list[dict[str, Any]]]:
    return {1: [comment(body, when)]}


def record(home: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((home / "failed" / "1").read_text())
    return data


def write(home: Path, **fields: Any) -> None:
    (home / "failed").mkdir(exist_ok=True)
    data = {"main": OLD, "kind": "decision", "retries": 0, "outcome": ""} | fields
    (home / "failed" / "1").write_text(json.dumps(data))


ASKED = f"rr-test: ReviewRadar #1 needs your decision: https://github.com/{REPO}/issues/1"


# AC1: the record


def test_build_without_pull_request_that_asked_is_recorded_as_decision(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:running")], issue_comments=asking(AFTER), git=on_main(OLD)
    )
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "decision"


def test_build_that_set_agent_failed_itself_and_asked_is_a_decision(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:failed")], issue_comments=asking(AFTER), git=on_main(OLD)
    )
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "decision"


def test_comment_without_the_decision_marker_is_a_plain_stop(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:running")],
        issue_comments=asking(AFTER, f"{MARKER}\nstopped"),
        git=on_main(OLD),
    )
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "stopped"


def test_decision_marker_without_the_loop_marker_does_not_count(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:running")],
        issue_comments=asking(AFTER, "<!-- needs-decision -->"),
        git=on_main(OLD),
    )
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "stopped"


def test_run_without_started_time_uses_the_pid_file_time(home: Path) -> None:
    ended(home, began=False)
    pid_file = home / "runs" / "issue-1" / "pid"
    import os

    os.utime(pid_file, (BEGAN, BEGAN))
    host = GitHost(
        issues=[issue(1, "agent:running")], issue_comments=asking(AFTER), git=on_main(OLD)
    )
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "decision"


# AC4: a marker from an earlier run is ignored


def test_decision_marker_from_an_earlier_run_is_ignored(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:running")], issue_comments=asking(BEFORE), git=on_main(OLD)
    )
    agent_tick.tick_once(host, home)
    assert record(home)["kind"] == "stopped"
    assert ASKED not in host.sent


# AC1: the check runs before the tick's own end comment


def test_decision_is_read_before_the_tick_comments(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:running")], issue_comments=asking(AFTER), git=on_main(OLD)
    )
    agent_tick.tick_once(host, home)
    reads = [
        i for i, c in enumerate(host.calls) if c[:3] == ["gh", "issue", "view"] and "comments" in c
    ]
    posts = [i for i, c in enumerate(host.calls) if c[:3] == ["gh", "issue", "comment"]]
    assert reads and posts and min(reads) < min(posts)


# AC2: no retry, whether main or the parent moved


def test_decision_is_not_retried_when_main_moves(home: Path) -> None:
    write(home)
    host = GitHost(issues=[issue(1, "agent:failed")], git=on_main(NEW))
    agent_tick.tick_once(host, home)
    assert started(host) == []


def test_retry_reason_is_empty_for_a_decision_when_the_parent_moved(home: Path) -> None:
    write(home, parent="aaaaaaa")
    tick = agent_tick.Tick(
        host=GitHost(git=on_main(NEW)),
        home=home,
        settings=agent_tick.read_settings(home / "agent.env"),
    )
    parent = {"number": 9, "headRefOid": "bbbbbbb"}
    assert agent_tick.retry_reason(tick, issue(1, "agent:failed"), parent) == ""


def test_adding_ready_again_restarts_a_decision(home: Path) -> None:
    write(home)
    host = GitHost(issues=[issue(1, "agent:ready")], git=on_main(NEW))
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #1 only."]
    assert not (home / "failed" / "1").exists()


# AC3: one ntfy message per stop


def test_decision_sends_one_message(home: Path) -> None:
    ended(home)
    host = GitHost(
        issues=[issue(1, "agent:running")], issue_comments=asking(AFTER), git=on_main(OLD)
    )
    agent_tick.tick_once(host, home)
    assert host.sent.count(ASKED) == 1
    assert not any("failed" in m for m in host.sent)
