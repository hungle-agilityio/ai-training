"""Tick hardening: owner pull requests, pull main, plan limit, labels, branches. Run: pytest ops"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import OWNER
from ops.tests.test_agent_tick import NOW, FakeHost, add_run, issue, pull, started


@dataclass
class GitHost(FakeHost):
    """FakeHost whose git answers come from `git`: a text found in the command -> (code, out)."""

    git: dict[str, tuple[int, str]] = field(default_factory=dict)

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[0] == "git":
            self.calls.append(args)
            text = " ".join(args)
            for part, answer in self.git.items():
                if part in text:
                    return answer
            return 0, ""
        return super().run(args, cwd)

    def git_calls(self, part: str) -> list[list[str]]:
        return [c for c in self.calls if c[0] == "git" and part in " ".join(c)]


ON_MAIN = {"branch --show-current": (0, "main\n")}


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def prompt(kind: str, n: int) -> str:
    return f"Use the work-queue skill for {kind} #{n} only."


# AC1: only the owner's pull requests from this repository


def test_fork_pull_request_with_the_marker_is_not_the_loops(home: Path) -> None:
    fork = pull(30, closes=5) | {"isCrossRepository": True, "author": {"login": OWNER}}
    host = GitHost(prs=[fork])
    agent_tick.tick_once(host, home)
    assert host.spawned == []
    assert "--json" in host.gh_calls("pr", "list")[0]
    assert "isCrossRepository" in " ".join(host.gh_calls("pr", "list")[0])


def test_another_logins_pull_request_does_not_hide_a_failed_build(home: Path) -> None:
    stranger = pull(31, closes=1) | {"author": {"login": "stranger"}}
    add_run(home, "issue-1", 77, exit_text="1", log="boom")
    host = GitHost(prs=[stranger], issues=[issue(1, "agent:running")])
    agent_tick.tick_once(host, home)
    assert ["gh", "issue", "edit", "1", "--add-label", "agent:failed", "--remove-label",
            "agent:running", "--repo", agent_tick.REPO] in host.calls


def test_foreign_pull_requests_do_not_count_towards_the_cap(home: Path) -> None:
    foreign = [pull(n, "pr:ready-for-review") | {"author": {"login": "x"}} for n in range(20, 26)]
    host = GitHost(prs=foreign, issues=[issue(4, "agent:ready")])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt("issue", 4)]


# AC2, AC3: pull main


def test_clean_main_checkout_is_fast_forwarded(home: Path) -> None:
    host = GitHost(git=dict(ON_MAIN))
    log = agent_tick.tick_once(host, home)
    assert host.git_calls("fetch origin main")
    assert host.git_calls("merge --ff-only origin/main")
    assert "main checkout: pulled" in log
    assert host.sent == ["rr-test: ReviewRadar queue empty, 0 pull requests waiting"]


@pytest.mark.parametrize(
    ("git", "reason"),
    [
        ({"branch --show-current": (0, "task/9-x\n")}, "the checkout is on task/9-x"),
        (ON_MAIN | {"status --porcelain": (0, " M ops/agent_tick.py\n")},
         "it has tracked changes"),
        (ON_MAIN | {"merge --ff-only": (1, "fatal: Not possible to fast-forward")},
         "the fast-forward failed"),
    ],
    ids=["other-branch", "tracked-changes", "ff-failed"],
)
def test_main_not_pulled_sends_the_reason_once(
    home: Path, git: dict[str, tuple[int, str]], reason: str
) -> None:
    host = GitHost(git=git)
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    sent = [m for m in host.sent if "main checkout" in m]
    assert sent == [f"rr-test: ReviewRadar main checkout not updated: {reason}"]


def test_reason_is_sent_again_after_a_successful_pull(home: Path) -> None:
    host = GitHost(git={"branch --show-current": (0, "task/9-x\n")})
    agent_tick.tick_once(host, home)
    host.git = dict(ON_MAIN)
    agent_tick.tick_once(host, home)
    host.git = {"branch --show-current": (0, "task/9-x\n")}
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "main checkout" in m]) == 2


def test_unreadable_branch_writes_a_log_line_only(home: Path) -> None:
    host = GitHost(git={"branch --show-current": (128, "fatal")})
    log = agent_tick.tick_once(host, home)
    assert "main checkout: the branch could not be read; not updated" in log
    assert not [m for m in host.sent if "main checkout" in m]


# AC4, AC5: plan limit


@pytest.mark.parametrize(
    ("outcome", "text"),
    [("0", "API Error: extra_usage_unavailable"),
     ("1", "You've hit your 5-hour limit · resets 1:50pm")],
)
def test_plan_limit_before_the_hand_over_pauses_whatever_the_exit_code(
    home: Path, outcome: str, text: str
) -> None:
    add_run(home, "issue-1", 77, exit_text=outcome, log=text)
    host = GitHost(issues=[issue(1, "agent:running")])
    agent_tick.tick_once(host, home)
    assert ["gh", "issue", "edit", "1", "--add-label", "agent:ready", "--remove-label",
            "agent:running", "--repo", agent_tick.REPO] in host.calls
    assert float((home / "paused-until").read_text()) == NOW + 3600
    assert not any("agent:failed" in c for c in host.calls)


def test_plan_limit_after_the_hand_over_never_puts_the_issue_back(home: Path) -> None:
    add_run(home, "issue-1", 77, exit_text="1", log="You've hit your 5-hour limit")
    host = GitHost(prs=[pull(40, "pr:ready-for-review", closes=1)],
                   issues=[issue(1, "agent:review")])
    agent_tick.tick_once(host, home)
    assert not any("--add-label" in c and "agent:ready" in c for c in host.gh_calls("issue"))
    assert not (home / "paused-until").exists()


def test_plan_limit_in_a_pull_request_run_pauses(home: Path) -> None:
    add_run(home, "pr-40", 77, exit_text="1", log="usage_limit_exceeded")
    host = GitHost(prs=[pull(40, "pr:changes-requested", closes=1)])
    agent_tick.tick_once(host, home)
    assert (home / "paused-until").exists()


# AC6: agent:ready leaves after the hand-over


def test_handed_over_issue_loses_agent_ready_but_failed_keeps_it(home: Path) -> None:
    host = GitHost(issues=[issue(1, "agent:ready", "agent:review"),
                           issue(2, "agent:ready", "agent:failed")])
    log = agent_tick.tick_once(host, home)
    edits = host.gh_calls("issue", "edit")
    assert ["gh", "issue", "edit", "1", "--remove-label", "agent:ready",
            "--repo", agent_tick.REPO] in edits
    assert not any(c[3] == "2" for c in edits)
    assert "issue-1: handed over, agent:ready removed" in log


# AC7: a kept worktree frees its branch


def test_kept_worktree_branch_is_archived_and_the_run_starts(home: Path) -> None:
    (home / "worktrees" / "issue-5").mkdir(parents=True)
    host = GitHost(issues=[issue(5, "agent:ready")], git={
        "branch --show-current": (0, "task/5-x\n"),
        "branch --list": (0, "task/5-x\nfeat/5-old\n"),
    })
    agent_tick.tick_once(host, home)
    stamp = int(NOW)
    renames = [c[-3:] for c in host.git_calls("branch -m")]
    assert ["-m", "task/5-x", f"archive/task/5-x-{stamp}"] in renames
    assert ["-m", "feat/5-old", f"archive/feat/5-old-{stamp}"] in renames
    assert len(renames) == 2
    assert not host.git_calls("branch -D") and not host.git_calls("branch -d")
    assert started(host) == [prompt("issue", 5)]


# AC8: ntfy when a build does not start


def test_failed_start_is_sent_once_until_the_key_starts(home: Path) -> None:
    host = GitHost(issues=[issue(5, "agent:ready")], git={"worktree add": (1, "fatal: exists")})
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    failed = [m for m in host.sent if "did not start" in m]
    assert failed == ["rr-test: ReviewRadar build for issue #5 did not start: "
                      "worktree add failed"]
    host.git = {}
    agent_tick.tick_once(host, home)
    host.alive_pids.clear()
    for run in (home / "runs").iterdir():
        if run.is_dir() and run.name != "done":
            (run / "exit").write_text("0")
    host.issues = [issue(5, "agent:ready")]
    host.git = {"worktree add": (1, "fatal: exists")}
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "did not start" in m]) == 2
