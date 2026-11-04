"""#180: the tick keeps a stacked pull request open when its parent is merged. Run: pytest ops"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, REPO
from ops.tests.test_tick_merge import ReviewHost, loop_pr, remark

DELETE = ["gh", "api", "-X", "DELETE", f"repos/{REPO}/git/refs/heads/task/5-x"]


@dataclass
class StackHost(ReviewHost):
    """ReviewHost that also answers branch deletes and base changes."""

    delete: tuple[int, str] = (0, "")
    base_change: tuple[int, str] = (0, "")

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[:4] == ["gh", "api", "-X", "DELETE"]:
            self.calls.append(args)
            return self.delete
        if args[1:3] == ["pr", "edit"] and "--base" in args:
            self.calls.append(args)
            if self.base_change[0] == 0:
                number = int(args[3])
                for pr in self.prs:
                    if pr["number"] == number:
                        pr["baseRefName"] = args[args.index("--base") + 1]
            return self.base_change
        return super().run(args, cwd)

    def deletes(self) -> list[list[str]]:
        return [c for c in self.calls if c[:4] == ["gh", "api", "-X", "DELETE"]]

    def merges(self) -> list[list[str]]:
        return self.gh_calls("pr", "merge")


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def parent() -> dict[str, Any]:
    return loop_pr(remark(101, "lgtm")) | {"baseRefName": "main"}


def stacked(number: int, base: str, head: str, closes: int) -> dict[str, Any]:
    return loop_pr() | {
        "number": number,
        "baseRefName": base,
        "headRefName": head,
        "body": f"{MARKER}\nCloses #{closes}",
        "labels": [{"name": "pr:ready-for-review"}],
    }


def bases(host: StackHost) -> dict[int, str]:
    return {p["number"]: p["baseRefName"] for p in host.prs}


# AC1, AC2: merge the parent without deleting, move the child to main


def test_parent_with_a_stacked_pull_request_merges_without_delete_branch(home: Path) -> None:
    host = StackHost(prs=[parent(), stacked(21, "task/5-x", "task/6-y", 6)])
    agent_tick.tick_once(host, home)
    assert host.merges() == [
        ["gh", "pr", "merge", "20", "--merge", "--match-head-commit", "abc1234def", "--repo", REPO]
    ]


def test_child_gets_base_main_and_stays_open_in_the_same_tick(home: Path) -> None:
    host = StackHost(prs=[parent(), stacked(21, "task/5-x", "task/6-y", 6)])
    agent_tick.tick_once(host, home)
    assert ["gh", "pr", "edit", "21", "--base", "main", "--repo", REPO] in host.calls
    assert bases(host)[21] == "main"
    assert host.gh_calls("pr", "close") == []
    assert host.gh_calls("pr", "merge")[0][3] == "20"
    assert len(host.merges()) == 1  # the child is merged on a later tick, not this one


# AC3: delete the parent's branch once, after the child moved


def test_branch_is_deleted_after_the_child_has_base_main(home: Path) -> None:
    host = StackHost(prs=[parent(), stacked(21, "task/5-x", "task/6-y", 6)])
    agent_tick.tick_once(host, home)
    assert host.deletes() == [DELETE]
    edit = host.calls.index(["gh", "pr", "edit", "21", "--base", "main", "--repo", REPO])
    assert edit < host.calls.index(DELETE)


def test_branch_is_deleted_once_per_branch(home: Path) -> None:
    host = StackHost(prs=[parent(), stacked(21, "task/5-x", "task/6-y", 6)])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert len(host.deletes()) == 1


def test_failed_delete_is_logged_and_retried_without_a_message(home: Path) -> None:
    host = StackHost(prs=[parent(), stacked(21, "task/5-x", "task/6-y", 6)], delete=(1, "HTTP 500"))
    log = agent_tick.tick_once(host, home)
    assert len([line for line in log if "task/5-x" in line and "not deleted" in line]) == 1
    assert [m for m in host.sent if "task/5-x" in m or "delete" in m.lower()] == []
    host.delete = (0, "")
    agent_tick.tick_once(host, home)
    assert len(host.deletes()) == 2


# AC4: a chain moves only the direct child


def test_chain_moves_only_the_direct_child_and_keeps_the_middle_branch(home: Path) -> None:
    middle = stacked(21, "task/5-x", "task/6-y", 6)
    top = stacked(22, "task/6-y", "task/7-z", 7)
    host = StackHost(prs=[parent(), middle, top])
    agent_tick.tick_once(host, home)
    assert bases(host) == {20: "main", 21: "main", 22: "task/6-y"}
    assert host.deletes() == [DELETE]
    assert not any("task/6-y" in " ".join(c) for c in host.deletes())


# AC5: nothing stacked, merge as before


def test_pull_request_with_nothing_stacked_merges_with_delete_branch(home: Path) -> None:
    host = StackHost(prs=[parent()])
    agent_tick.tick_once(host, home)
    assert host.merges() == [
        [
            "gh",
            "pr",
            "merge",
            "20",
            "--merge",
            "--delete-branch",
            "--match-head-commit",
            "abc1234def",
            "--repo",
            REPO,
        ]
    ]
    assert host.deletes() == []


# AC6: a failed base change keeps the branch


def test_failed_base_change_keeps_the_parent_branch_and_retries_next_tick(home: Path) -> None:
    host = StackHost(
        prs=[parent(), stacked(21, "task/5-x", "task/6-y", 6)], base_change=(1, "nope")
    )
    log = agent_tick.tick_once(host, home)
    assert host.deletes() == []
    assert any("pr-21" in line and "base not changed" in line for line in log)
    host.base_change = (0, "")
    host.prs[0]["state"] = "MERGED"
    agent_tick.tick_once(host, home)
    assert bases(host)[21] == "main"
    assert host.deletes() == [DELETE]


# AC7: a closed pull request does not take agent:review while another one closes the issue


def test_closed_pull_request_keeps_agent_review_when_another_open_one_closes_the_issue(
    home: Path,
) -> None:
    closed = loop_pr() | {"number": 18, "state": "CLOSED", "labels": []}
    still_open = loop_pr() | {"number": 19, "labels": [{"name": "pr:ready-for-review"}]}
    host = StackHost(
        prs=[closed, still_open],
        issues=[
            {"number": 5, "labels": [{"name": "agent:review"}], "body": "", "title": "t"},
        ],
    )
    agent_tick.tick_once(host, home)
    assert not [
        c
        for c in host.calls
        if c[1:3] == ["issue", "edit"] and "--remove-label" in c and "agent:review" in c
    ]


def test_closed_pull_request_still_clears_agent_review_when_nothing_else_is_open(
    home: Path,
) -> None:
    closed = loop_pr() | {"number": 18, "state": "CLOSED", "labels": []}
    host = StackHost(
        prs=[closed],
        issues=[
            {"number": 5, "labels": [{"name": "agent:review"}], "body": "", "title": "t"},
        ],
    )
    agent_tick.tick_once(host, home)
    assert [
        "gh",
        "issue",
        "edit",
        "5",
        "--remove-label",
        "agent:review",
        "--repo",
        REPO,
    ] in host.calls
