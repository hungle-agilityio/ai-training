"""#263: the tick keeps one branch per epic (spec epic-branch AC1 to AC6). Run: pytest ops"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick, epic_branch
from ops.agent_tick import MARKER, REPO
from ops.tests.test_tick_merge import ReviewHost, loop_pr

BRANCH = "epic/236-reply-to-reviews"


@dataclass
class EpicHost(ReviewHost):
    """ReviewHost whose git answers come from the fields below."""

    branches: set[str] = field(default_factory=set)
    in_branch: set[str] = field(default_factory=lambda: {"origin/main"})
    conflicts: set[str] = field(default_factory=set)
    epic_state: str = "OPEN"
    broken: set[str] = field(default_factory=set)
    open_on_branch: str = "[]"
    pushes: list[list[str]] = field(default_factory=list)
    comments: list[list[str]] = field(default_factory=list)
    deletes: list[list[str]] = field(default_factory=list)

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[:2] == ["gh", "api"] and "DELETE" in args:
            self.calls.append(args)
            self.deletes.append(args)
            return 0, ""
        if args[:3] == ["gh", "pr", "comment"]:
            self.calls.append(args)
            self.comments.append(args)
            return 0, ""
        if args[:3] == ["gh", "pr", "list"] and "--base" in args:
            self.calls.append(args)
            return 0, self.open_on_branch
        if args[:3] == ["gh", "issue", "view"] and "state" in args:
            self.calls.append(args)
            return 0, json.dumps({"state": self.epic_state})
        if args[0] != "git":
            return super().run(args, cwd)
        self.calls.append(args)
        git = args[3:]
        if self.fail and self.fail in " ".join(git):
            return 1, "boom"
        if git[:3] == ["rev-parse", "--verify", "--quiet"]:
            return (
                (0, "") if git[3].removeprefix("refs/remotes/origin/") in self.branches else (1, "")
            )
        if git[:1] == ["push"]:
            self.pushes.append(git)
            if git[2].endswith(f"refs/heads/{BRANCH}"):
                self.branches.add(BRANCH)
            return 0, ""
        if git[:1] == ["for-each-ref"]:
            return 0, "".join(f"origin/{b}\n" for b in sorted(self.branches))
        if git[:2] == ["merge-base", "--is-ancestor"]:
            return (0, "") if git[2] in self.in_branch else (1, "")
        if git[:1] == ["merge"] and "--abort" not in git:
            commit = git[-1]
            if commit in self.broken:
                return 128, "fatal: Committer identity unknown"
            if commit in self.conflicts:
                return 1, "CONFLICT"
            self.in_branch.add(commit)
            return 0, ""
        return super().run(args, cwd) if args[0] != "git" else (0, "")


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def epic_issue(number: int = 236, title: str = "Epic: reply to reviews") -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "body": "An epic.",
        "createdAt": "2026-11-01T00:00:00Z",
        "labels": [{"name": "epic"}],
    }


def task_issue(number: int = 5, epic: int = 236) -> dict[str, Any]:
    return {
        "number": number,
        "title": "Task",
        "body": f"Do it.\n\nPart of the epic #{epic}\n",
        "createdAt": "2026-11-01T00:00:00Z",
        "labels": [{"name": "agent:review"}],
    }


def epic_pr(
    number: int = 20, closes: int = 5, oid: str = "abc1234def", **kw: Any
) -> dict[str, Any]:
    pr = loop_pr(**kw) | {"number": number, "headRefOid": oid, "headRefName": f"task/{closes}-x"}
    pr["body"] = f"{MARKER}\nCloses #{closes}"
    pr["baseRefName"] = "main"
    return pr


def host_for(*prs: dict[str, Any], **kw: Any) -> EpicHost:
    host = EpicHost(**kw)
    host.prs = list(prs)
    host.issues = [epic_issue(), task_issue(5), task_issue(6)]
    return host


def tick(host: EpicHost, home: Path) -> list[str]:
    return agent_tick.tick_once(host, home)


def merges(host: EpicHost) -> list[list[str]]:
    return [
        c[3:] for c in host.calls if c[0] == "git" and c[3:4] == ["merge"] and "--abort" not in c
    ]


# Slug and body


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Epic: reply to reviews", "reply-to-reviews"),
        ("  EPIC :  Fix: the (big) one!! ", "fix-the-big-one"),
        ("Epic: " + "word " * 20, "word-word-word-word-word-word-word-word"),
    ],
)
def test_slug_is_lowercase_dashed_and_short(title: str, expected: str) -> None:
    assert epic_branch.slug(title) == expected
    assert len(epic_branch.slug(title)) <= 40


def test_slug_never_ends_with_a_dash_after_the_cut() -> None:
    assert not epic_branch.slug("Epic: " + "a" * 39 + " b").endswith("-")


def test_epic_number_reads_the_first_part_of_line() -> None:
    body = "x\nPart of the epic #12\nPart of the epic #13"
    assert epic_branch.epic_number(body) == 12
    assert epic_branch.epic_number("no epic here") is None


# AC1


def test_a_ready_pull_request_into_main_makes_no_branch(home: Path) -> None:
    host = host_for(epic_pr())
    tick(host, home)
    assert host.pushes == []


@pytest.mark.parametrize(
    "pr",
    [
        epic_pr(labels=("pr:changes-requested",)),
        epic_pr(checks=[{"status": "COMPLETED", "conclusion": "FAILURE"}]),
        epic_pr(checks=[{"status": "IN_PROGRESS", "conclusion": ""}]),
        epic_pr(checks=[]),
        epic_pr() | {"isDraft": True},
        epic_pr(closes=99),
    ],
)
def test_no_branch_until_a_task_pull_request_is_green_and_ready(home: Path, pr: Any) -> None:
    host = host_for(pr)
    tick(host, home)
    assert host.pushes == []


def test_no_branch_for_a_task_without_an_epic_line(home: Path) -> None:
    host = host_for(epic_pr())
    host.issues = [epic_issue(), task_issue(5) | {"body": "No epic line"}]
    tick(host, home)
    assert host.pushes == []


# AC2


def test_a_ready_pull_request_is_never_merged_locally(home: Path) -> None:
    host = host_for(epic_pr(), branches={BRANCH})
    tick(host, home)
    assert merges(host) == []
    assert host.pushes == []


def test_pull_request_already_in_the_branch_is_not_merged_again(home: Path) -> None:
    host = host_for(epic_pr(), branches={BRANCH}, in_branch={"origin/main", "abc1234def"})
    tick(host, home)
    assert merges(host) == []
    assert host.pushes == []


def test_red_pull_request_is_not_merged(home: Path) -> None:
    red = epic_pr(checks=[{"status": "COMPLETED", "conclusion": "FAILURE"}])
    host = host_for(red, branches={BRANCH})
    tick(host, home)
    assert merges(host) == []


# AC3


def test_main_is_merged_into_the_branch_when_it_moved(home: Path) -> None:
    host = host_for(branches={BRANCH}, in_branch=set())
    tick(host, home)
    assert any(m[-1] == "origin/main" and "--no-ff" in m for m in merges(host))
    assert len(host.pushes) == 1


def test_main_already_in_the_branch_pushes_nothing(home: Path) -> None:
    host = host_for(branches={BRANCH})
    tick(host, home)
    assert host.pushes == []


# AC4


def test_main_conflict_sends_one_message_per_hour(home: Path) -> None:
    host = host_for(epic_pr(), branches={BRANCH}, in_branch=set(), conflicts={"origin/main"})
    tick(host, home)
    tick(host, home)
    assert len([m for m in host.sent if BRANCH in m]) == 1
    host.clock += 3601
    tick(host, home)
    assert len([m for m in host.sent if BRANCH in m]) == 2
    assert host.pushes == []
    assert merges(host)[0][-1] == "origin/main"
    assert all(m[-1] == "origin/main" for m in merges(host))


# AC5


def test_one_log_line_per_epic(home: Path) -> None:
    host = host_for(epic_pr(), branches={BRANCH})
    log = tick(host, home)
    assert [line for line in log if line.startswith("epic #")] == [
        f"epic #236: branch {BRANCH}, up to date with main"
    ]


def test_log_line_names_a_main_conflict(home: Path) -> None:
    host = host_for(branches={BRANCH}, in_branch=set(), conflicts={"origin/main"})
    log = tick(host, home)
    assert f"epic #236: branch {BRANCH}, conflict with main" in log


# AC6


def test_branch_of_a_closed_epic_is_deleted_everywhere(home: Path) -> None:
    host = host_for(branches={BRANCH}, epic_state="CLOSED")
    host.issues = [task_issue(5)]
    tick(host, home)
    assert host.deletes == [["gh", "api", "-X", "DELETE", f"repos/{REPO}/git/refs/heads/{BRANCH}"]]
    assert any(c[0] == "git" and c[3:5] == ["branch", "-D"] and c[5] == BRANCH for c in host.calls)


def test_branch_stays_while_a_pull_request_is_based_on_it(home: Path) -> None:
    child = epic_pr(number=30, closes=6) | {"baseRefName": BRANCH}
    host = host_for(child, branches={BRANCH}, epic_state="CLOSED")
    host.issues = [task_issue(5)]
    tick(host, home)
    assert host.deletes == []


def test_branch_stays_when_the_epic_is_still_open(home: Path) -> None:
    host = host_for(branches={BRANCH}, epic_state="OPEN")
    host.issues = [task_issue(5)]
    tick(host, home)
    assert host.deletes == []


def test_open_epic_keeps_its_branch(home: Path) -> None:
    host = host_for(branches={BRANCH})
    tick(host, home)
    assert host.deletes == []


def test_a_merge_failure_that_is_no_conflict_posts_and_sends_nothing(home: Path) -> None:
    host = host_for(epic_pr(), branches={BRANCH}, broken={"abc1234def"})
    tick(host, home)
    assert host.comments == []
    assert not [m for m in host.sent if BRANCH in m]


def test_a_main_merge_failure_that_is_no_conflict_sends_nothing(home: Path) -> None:
    host = host_for(branches={BRANCH}, in_branch=set(), broken={"origin/main"})
    tick(host, home)
    assert not [m for m in host.sent if BRANCH in m]


def test_branch_stays_while_a_pull_request_of_the_owner_is_based_on_it(home: Path) -> None:
    host = host_for(branches={BRANCH}, epic_state="CLOSED", open_on_branch='[{"number": 77}]')
    host.issues = [task_issue(5)]
    tick(host, home)
    assert host.deletes == []


def test_an_unreadable_reminder_file_does_not_stop_the_tick(home: Path) -> None:
    (home / "epic-conflict-236").write_text("not a number")
    host = host_for(branches={BRANCH}, in_branch=set(), conflicts={"origin/main"})
    tick(host, home)
    assert len([m for m in host.sent if BRANCH in m]) == 1


def test_a_git_failure_is_logged_and_the_tick_goes_on(home: Path) -> None:
    host = host_for(epic_pr(), branches={BRANCH}, fail="fetch origin --prune")
    log = tick(host, home)
    assert any("epic branches: git fetch failed" in line for line in log)
