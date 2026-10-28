"""Tests of the loop tick, with gh, git, claude and the clock faked. Run: uv run pytest ops/tests"""

from __future__ import annotations

import json
import os
import signal
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, OWNER

NOW = 1_800_000_000.0


def issue(number: int, *labels: str, body: str = "", created: str = "") -> dict[str, Any]:
    return {
        "number": number,
        "body": body,
        "labels": [{"name": name} for name in labels],
        "createdAt": created or f"2026-10-{number:02d}T00:00:00Z",
    }


def pull(number: int, *labels: str, state: str = "OPEN", closes: int = 0,
         comments: list[dict[str, Any]] | None = None, checks: str = "SUCCESS",
         marker: bool = True) -> dict[str, Any]:
    body = (MARKER + "\n" if marker else "") + (f"Closes #{closes}" if closes else "")
    return {
        "number": number,
        "state": state,
        "body": body,
        "labels": [{"name": name} for name in labels],
        "headRefName": f"task/{closes or number}-x",
        "commits": [{"committedDate": "2026-10-20T10:00:00Z"}],
        "comments": comments or [],
        "statusCheckRollup": [{"conclusion": checks}],
    }


def comment(body: str, when: str = "2026-10-21T00:00:00Z", login: str = OWNER) -> dict[str, Any]:
    return {"author": {"login": login}, "body": body, "createdAt": when}


@dataclass
class FakeHost:
    """gh answers from the lists below; every other command succeeds."""

    prs: list[dict[str, Any]] = field(default_factory=list)
    issues: list[dict[str, Any]] = field(default_factory=list)
    labeller: dict[int, str] = field(default_factory=dict)
    issue_comments: dict[int, list[dict[str, Any]]] = field(default_factory=dict)
    labels: list[str] = field(default_factory=lambda: ["agent:running", "agent:failed"])
    alive_pids: set[int] = field(default_factory=set)
    fail: str = ""
    clock: float = NOW
    calls: list[list[str]] = field(default_factory=list)
    spawned: list[list[str]] = field(default_factory=list)
    sent: list[str] = field(default_factory=list)

    def now(self) -> float:
        return self.clock

    def run(self, args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        self.calls.append(args)
        if self.fail and self.fail in " ".join(args):
            return 1, "boom"
        if args[0] != "gh":
            return 0, ""
        if args[1] == "api":
            if "--repo" in args:
                return 1, "unknown flag: --repo"
            number = int(args[2].split("/")[-2])
            return 0, f"someone\n{self.labeller.get(number, OWNER)}\n"
        return 0, json.dumps(self.answer(args[1:]))

    def answer(self, args: list[str]) -> Any:
        if args[:2] == ["pr", "list"]:
            return self.prs
        if args[:2] == ["label", "list"]:
            return [{"name": name} for name in self.labels]
        if args[:2] == ["issue", "list"]:
            if "agent:review" in args:
                return [i for i in self.issues if "agent:review" in agent_tick.names(i)]
            return [i for i in self.issues if not i.get("closed")]
        if args[:2] == ["issue", "view"]:
            number = int(args[2])
            found = next((i for i in self.issues if i["number"] == number), issue(number))
            return {"labels": found["labels"], "comments": self.issue_comments.get(number, [])}
        return {}

    def spawn(self, args: Sequence[str], log: Path) -> int:
        self.spawned.append(list(args))
        pid = 1000 + len(self.spawned)
        self.alive_pids.add(pid)
        return pid

    def alive(self, pid: int) -> bool:
        return pid in self.alive_pids

    def notify(self, topic: str, message: str) -> None:
        self.sent.append(f"{topic}: {message}")

    def gh_calls(self, *start: str) -> list[list[str]]:
        return [c for c in self.calls if c[0] == "gh" and c[1 : 1 + len(start)] == list(start)]


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def started(host: FakeHost) -> list[str]:
    return [args[-1] for args in host.spawned]


def add_run(home: Path, key: str, pid: int, exit_text: str | None = None, log: str = "",
            alone: bool = False) -> Path:
    run = home / "runs" / key
    run.mkdir(parents=True)
    (run / "pid").write_text(str(pid))
    (run / "log.txt").write_text(log)
    if exit_text is not None:
        (run / "exit").write_text(exit_text)
    if alone:
        (run / "alone").touch()
    (home / "worktrees" / key).mkdir(parents=True)
    return run


# AC1: one tick at a time


def test_tick_exits_when_a_young_lock_exists(home: Path) -> None:
    (home / "tick.lock").mkdir()
    os.utime(home / "tick.lock", (NOW - 60, NOW - 60))
    host = FakeHost(issues=[issue(1, "agent:ready")])
    log = agent_tick.tick_once(host, home)
    assert log == ["another tick is running; nothing done"]
    assert host.calls == [] and (home / "tick.lock").exists()


def test_tick_takes_over_a_lock_older_than_15_minutes(home: Path) -> None:
    (home / "tick.lock").mkdir()
    os.utime(home / "tick.lock", (NOW - 16 * 60, NOW - 16 * 60))
    host = FakeHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #1 only."]
    assert not (home / "tick.lock").exists()


def test_lock_is_removed_when_the_tick_fails(home: Path) -> None:
    host = FakeHost(fail="pr list")
    with pytest.raises(RuntimeError):
        agent_tick.tick_once(host, home)
    assert not (home / "tick.lock").exists()


# AC2: settings


def test_settings_default_to_one_build_and_no_topic(tmp_path: Path) -> None:
    assert agent_tick.read_settings(tmp_path / "missing.env") == agent_tick.Settings(1, "")


def test_settings_read_quoted_values_and_comments(tmp_path: Path) -> None:
    env = tmp_path / "agent.env"
    env.write_text("# loop\nAGENT_CONCURRENCY='3'\nNTFY_TOPIC=\"topic\"\n")
    assert agent_tick.read_settings(env) == agent_tick.Settings(3, "topic")


@pytest.mark.parametrize("value", ["0", "4", "two", "1.5", ""])
def test_bad_concurrency_stops_the_tick_with_a_message(tmp_path: Path, value: str) -> None:
    env = tmp_path / "agent.env"
    env.write_text(f"AGENT_CONCURRENCY={value}\n")
    with pytest.raises(SystemExit, match="must be 1, 2 or 3"):
        agent_tick.read_settings(env)


def test_no_topic_sends_nothing(home: Path) -> None:
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\n")
    host = FakeHost()
    agent_tick.tick_once(host, home)
    assert host.sent == []


# AC3: free slots


def test_two_slots_start_two_issues(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready"), issue(2, "agent:ready"),
                            issue(3, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == [
        "Use the work-queue skill for issue #1 only.",
        "Use the work-queue skill for issue #2 only.",
    ]


def test_a_live_build_takes_a_slot(home: Path) -> None:
    add_run(home, "issue-9", 77)
    host = FakeHost(issues=[issue(1, "agent:ready"), issue(2, "agent:ready")], alive_pids={77})
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #1 only."]


def test_no_free_slot_starts_nothing(home: Path) -> None:
    add_run(home, "issue-8", 77)
    add_run(home, "issue-9", 78)
    host = FakeHost(issues=[issue(1, "agent:ready")], alive_pids={77, 78})
    agent_tick.tick_once(host, home)
    assert host.spawned == [] and host.sent == []


# AC4: pull requests first


def test_pull_request_with_owner_redo_goes_before_issues(home: Path) -> None:
    redo = comment("/redo rename the button")
    host = FakeHost(prs=[pull(20, "pr:ready-for-review", closes=5, comments=[redo])],
                    issues=[issue(1, "agent:ready"), issue(2, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == [
        "Use the work-queue skill for pull request #20 only.",
        "Use the work-queue skill for issue #1 only.",
    ]


def test_redo_on_the_issue_counts(home: Path) -> None:
    host = FakeHost(prs=[pull(20, "pr:ready-for-review", closes=5)],
                    issue_comments={5: [comment("/redo add a test")]})
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for pull request #20 only."]


@pytest.mark.parametrize(
    "redo",
    [
        comment("/redo older", when="2026-10-19T00:00:00Z"),
        comment(f"{MARKER}\n/redo from the loop"),
        comment("/redo by someone else", login="stranger"),
        comment("please /redo this"),
    ],
)
def test_redo_that_does_not_count_is_ignored(home: Path, redo: dict[str, Any]) -> None:
    host = FakeHost(prs=[pull(20, "pr:ready-for-review", closes=5, comments=[redo])])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_blocked_pull_request_without_new_redo_is_not_taken(home: Path) -> None:
    host = FakeHost(prs=[pull(20, "pr:blocked", checks="FAILURE")])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_blocked_pull_request_with_new_redo_is_taken(home: Path) -> None:
    host = FakeHost(prs=[pull(20, "pr:blocked", comments=[comment("/redo go on")])])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for pull request #20 only."]


@pytest.mark.parametrize(
    "pr",
    [
        pull(20),
        pull(20, "pr:ready-for-review", checks="FAILURE"),
        pull(20, "pr:ready-for-review", state="MERGED"),
        pull(20, state="CLOSED", closes=6),
    ],
    ids=["no-status-label", "ready-but-ci-red", "merged-with-label", "closed-issue-in-review"],
)
def test_pull_request_that_needs_a_run_is_taken(home: Path, pr: dict[str, Any]) -> None:
    host = FakeHost(prs=[pr], issues=[issue(6, "agent:review")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for pull request #20 only."]


@pytest.mark.parametrize(
    "pr",
    [
        pull(20, "pr:ready-for-review"),
        pull(20, "pr:ci-failed", checks="FAILURE"),
        pull(20, state="MERGED", closes=7),
        pull(20, marker=False),
    ],
    ids=["ready-green", "ci-failed", "merged-tidy", "not-the-loops"],
)
def test_pull_request_that_needs_nothing_is_left_alone(home: Path, pr: dict[str, Any]) -> None:
    host = FakeHost(prs=[pr])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_pull_request_already_building_is_not_taken_again(home: Path) -> None:
    add_run(home, "pr-20", 77)
    host = FakeHost(prs=[pull(20)], alive_pids={77})
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_pull_request_run_checks_out_its_branch(home: Path) -> None:
    host = FakeHost(prs=[pull(20, closes=5)])
    agent_tick.tick_once(host, home)
    add = next(c for c in host.calls if c[3:5] == ["worktree", "add"])
    assert add[5:] == ["-B", "task/5-x", str(home / "worktrees" / "pr-20"), "origin/task/5-x"]
    assert host.gh_calls("issue", "edit") == []


# AC5: picking a new issue


def test_oldest_issue_is_picked_first(home: Path) -> None:
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\n")
    host = FakeHost(issues=[issue(2, "agent:ready", created="2026-10-01T00:00:00Z"),
                            issue(1, "agent:ready", created="2026-10-05T00:00:00Z")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #2 only."]


@pytest.mark.parametrize("label", sorted(agent_tick.SKIP_LABELS))
def test_issue_with_a_skip_label_is_not_taken(home: Path, label: str) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready", label)])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_issue_waits_for_an_open_dependency(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready", body="Depends on #2"), issue(2)])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_issue_with_a_closed_dependency_is_taken(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready", body="Depends on #2")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #1 only."]


def test_ready_label_added_by_someone_else_is_skipped(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready"), issue(2, "agent:ready")],
                    labeller={1: "stranger"})
    log = agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #2 only."]
    assert f"issue-1: agent:ready was not added by {OWNER}; skipped" in log


def test_no_issue_when_waiting_pull_requests_and_running_issues_reach_three(home: Path) -> None:
    host = FakeHost(prs=[pull(20, "pr:ready-for-review"), pull(21, "pr:ready-for-review")],
                    issues=[issue(3, "agent:running"), issue(4, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_cap_counts_the_issue_claimed_in_this_tick(home: Path) -> None:
    host = FakeHost(prs=[pull(20, "pr:ready-for-review"), pull(21, "pr:ready-for-review")],
                    issues=[issue(4, "agent:ready"), issue(5, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #4 only."]


# AC6: runs alone


@pytest.mark.parametrize(
    "item",
    [issue(1, "agent:ready", "risk:high"),
     issue(1, "agent:ready", body="Touches reviews/migrations/0004.py"),
     issue(1, "agent:ready", body="Change reviews/models.py")],
    ids=["risk-high", "migrations", "models"],
)
def test_risky_issue_runs_alone(home: Path, item: dict[str, Any]) -> None:
    host = FakeHost(issues=[item, issue(2, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #1 only."]
    assert (home / "runs" / "issue-1" / "alone").exists()


def test_risky_issue_waits_while_another_build_runs(home: Path) -> None:
    add_run(home, "issue-9", 77)
    host = FakeHost(issues=[issue(1, "agent:ready", "risk:high"), issue(2, "agent:ready")],
                    alive_pids={77})
    agent_tick.tick_once(host, home)
    assert host.spawned == []


def test_no_new_issue_while_a_risky_build_runs_but_pull_requests_go_on(home: Path) -> None:
    add_run(home, "issue-9", 77, alone=True)
    host = FakeHost(prs=[pull(20)], issues=[issue(2, "agent:ready")], alive_pids={77})
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for pull request #20 only."]


# AC7: claim


def test_issue_is_labelled_running_before_the_build_starts(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready")], labels=[])
    agent_tick.tick_once(host, home)
    names = [c[1:4] for c in host.calls if c[0] == "gh"]
    assert ["label", "create", "agent:running"] in names
    assert host.gh_calls("issue", "edit") == [
        ["gh", "issue", "edit", "1", "--add-label", "agent:running", "--repo", agent_tick.REPO]
    ]


# AC8, AC9: worktree and the build


def test_issue_build_gets_a_detached_worktree_synced_and_a_claude_run(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    worktree = home / "worktrees" / "issue-1"
    assert ["git", "-C", str(agent_tick.REPO_ROOT), "worktree", "add", "--detach",
            str(worktree), "origin/main"] in host.calls
    assert ["uv", "sync", "--frozen"] in host.calls
    wrapper = host.spawned[0]
    assert wrapper[2:] == ["run", str(home / "runs" / "issue-1"),
                           str(worktree / "claude-code-training-lab"),
                           "Use the work-queue skill for issue #1 only."]
    assert (home / "runs" / "issue-1" / "pid").read_text() == "1001"


def test_worktree_left_from_a_failed_build_is_moved_aside(home: Path) -> None:
    (home / "worktrees" / "issue-1").mkdir(parents=True)
    host = FakeHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    aside = str(home / "worktrees" / f"issue-1-{int(NOW)}")
    assert any(c[3:5] == ["worktree", "move"] and c[-1] == aside for c in host.calls)


def test_failed_sync_neither_claims_nor_starts(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready")], fail="uv sync")
    log = agent_tick.tick_once(host, home)
    assert host.spawned == [] and host.gh_calls("issue", "edit") == []
    assert any("not started" in line for line in log)


def test_build_runs_claude_in_loop_mode_with_a_time_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, Any] = {}

    class Child:
        pid = 4242

        def wait(self, timeout: float) -> int:
            seen["timeout"] = timeout
            return 0

    def popen(args: list[str], **kwargs: Any) -> Child:
        seen["args"], seen["kwargs"] = args, kwargs
        return Child()

    monkeypatch.setattr(subprocess, "Popen", popen)
    assert agent_tick.run_build(tmp_path, tmp_path / "lab", "Use it for issue #1 only.") == "0"
    assert seen["args"] == ["claude", "-p", "Use it for issue #1 only.", "--max-turns", "80"]
    assert seen["kwargs"]["env"]["REVIEWRADAR_LOOP"] == "1"
    assert seen["kwargs"]["cwd"] == tmp_path / "lab"
    assert seen["kwargs"]["stdin"] == subprocess.DEVNULL
    assert seen["timeout"] == 45 * 60
    assert "dangerously" not in " ".join(seen["args"])
    assert (tmp_path / "exit").read_text() == "0"


def test_build_is_stopped_after_45_minutes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    killed: list[int] = []

    class Child:
        pid = 4242

        def wait(self, timeout: float) -> int:
            raise subprocess.TimeoutExpired("claude", timeout)

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: Child())
    monkeypatch.setattr(os, "killpg", lambda pid, sig: killed.append(sig))
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "timeout"
    assert killed == [signal.SIGTERM, signal.SIGKILL]
    assert (tmp_path / "exit").read_text() == "timeout"


# AC10: after a build


def test_normal_end_removes_the_worktree_and_archives_the_run(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = FakeHost()
    agent_tick.tick_once(host, home)
    assert ["git", "-C", str(agent_tick.REPO_ROOT), "worktree", "remove",
            str(home / "worktrees" / "issue-1")] in host.calls
    assert not (home / "runs" / "issue-1").exists()
    assert (home / "runs" / "done" / f"issue-1-{int(NOW)}" / "log.txt").exists()


@pytest.mark.parametrize("outcome,reason", [("0", "ended without a pull request"),
                                            ("timeout", "stopped after 45 minutes"),
                                            ("1", "ended with error 1"),
                                            (None, "stopped with no exit code")])
def test_failed_build_marks_the_issue_failed(home: Path, outcome: str | None,
                                             reason: str) -> None:
    log = "\n".join(f"line {n}" for n in range(30))
    add_run(home, "issue-1", 77, exit_text=outcome, log=log)
    host = FakeHost(issues=[issue(1, "agent:ready", "agent:running")])
    agent_tick.tick_once(host, home)
    assert ["gh", "issue", "edit", "1", "--add-label", "agent:failed", "--remove-label",
            "agent:running", "--repo", agent_tick.REPO] in host.calls
    body = host.gh_calls("issue", "comment")[0][5]
    assert body.startswith(MARKER) and reason in body
    assert "line 10\n" in body and "line 9\n" not in body
    assert not any(c[3:5] == ["worktree", "remove"] for c in host.calls)
    assert host.sent[0] == f"rr-test: ReviewRadar build for issue #1 failed: {reason}"


def test_normal_end_after_handing_over_is_not_marked(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="0")
    host = FakeHost(prs=[pull(20, "pr:ready-for-review", closes=1)],
                    issues=[issue(1, "agent:review")])
    log = agent_tick.tick_once(host, home)
    assert "issue-1: ended normally" in log
    assert host.gh_calls("issue", "comment") == []


def test_failed_build_that_already_opened_a_pull_request_is_not_marked(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="timeout")
    host = FakeHost(prs=[pull(20, "pr:ready-for-review", closes=1)],
                    issues=[issue(1, "agent:running")])
    agent_tick.tick_once(host, home)
    assert host.gh_calls("issue", "comment") == []
    assert any(c[3:5] == ["worktree", "remove"] for c in host.calls)


def test_failed_pull_request_build_keeps_its_worktree_and_notifies(home: Path) -> None:
    add_run(home, "pr-20", 77, exit_text="1")
    host = FakeHost(prs=[pull(20, "pr:ready-for-review")])
    agent_tick.tick_once(host, home)
    assert host.gh_calls("issue", "edit") == []
    assert host.sent[0] == "rr-test: ReviewRadar build for pull request #20 ended with error 1"


def test_plan_limit_puts_the_issue_back_and_pauses(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="1", log="Claude usage limit reached|1800003600")
    host = FakeHost(issues=[issue(1, "agent:ready", "agent:running"), issue(2, "agent:ready")])
    log = agent_tick.tick_once(host, home)
    assert ["gh", "issue", "edit", "1", "--add-label", "agent:ready", "--remove-label",
            "agent:running", "--repo", agent_tick.REPO] in host.calls
    assert not any("agent:failed" in c for c in host.calls)
    assert any(c[3:5] == ["worktree", "remove"] for c in host.calls)
    assert float((home / "paused-until").read_text()) == NOW + 3600
    assert host.spawned == [] and "paused after the plan limit; no build started" in log
    assert host.sent == ["rr-test: ReviewRadar loop paused 60 minutes: plan limit reached "
                         "(issue-1)"]


def test_live_build_is_not_touched(home: Path) -> None:
    add_run(home, "issue-1", 77)
    host = FakeHost(alive_pids={77})
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "issue-1" / "pid").exists()
    assert not any(c[3:5] == ["worktree", "remove"] for c in host.calls)


# AC11: pause


def test_pause_in_the_future_starts_nothing_but_still_tidies(home: Path) -> None:
    (home / "paused-until").write_text(str(int(NOW + 60)))
    add_run(home, "issue-5", 77, exit_text="0")
    host = FakeHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert host.spawned == []
    assert any(c[3:5] == ["worktree", "remove"] for c in host.calls)


def test_pause_in_the_past_is_over(home: Path) -> None:
    (home / "paused-until").write_text(str(int(NOW - 1)))
    host = FakeHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for issue #1 only."]


# AC12: queue empty


def test_queue_empty_is_sent_once_until_something_changes(home: Path) -> None:
    host = FakeHost(prs=[pull(20, "pr:ready-for-review")])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert host.sent == ["rr-test: ReviewRadar queue empty, 1 pull requests waiting"]
    host.prs.append(pull(21, "pr:ready-for-review"))
    agent_tick.tick_once(host, home)
    assert host.sent[-1] == "rr-test: ReviewRadar queue empty, 2 pull requests waiting"


def test_queue_empty_is_sent_again_after_a_build(home: Path) -> None:
    host = FakeHost()
    agent_tick.tick_once(host, home)
    host.issues = [issue(1, "agent:ready")]
    agent_tick.tick_once(host, home)
    host.issues, host.alive_pids = [], set()
    (home / "runs" / "issue-1" / "exit").write_text("0")
    agent_tick.tick_once(host, home)
    assert host.sent == ["rr-test: ReviewRadar queue empty, 0 pull requests waiting"] * 2


def test_no_queue_empty_while_a_build_runs(home: Path) -> None:
    add_run(home, "issue-1", 77)
    host = FakeHost(alive_pids={77})
    agent_tick.tick_once(host, home)
    assert host.sent == []


def test_main_runs_the_wrapper(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[Path, Path, str]] = []
    def run_build(run: Path, folder: Path, prompt: str) -> str:
        calls.append((run, folder, prompt))
        return "0"

    monkeypatch.setattr(agent_tick, "run_build", run_build)
    assert agent_tick.main(["run", str(tmp_path), str(tmp_path), "prompt"]) == 0
    assert calls == [(tmp_path, tmp_path, "prompt")]
