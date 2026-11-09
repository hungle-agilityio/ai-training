"""#329: a pull request merged into an epic branch gets a new one into main. Run: pytest ops"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import FakeHost, issue

EPIC = "epic/312-topics"
OLD_BODY = f"{MARKER}\nStacked on #9 through {EPIC} (merge those first).\nReport: x\nCloses #5"


def merged(number: int = 20, issue_number: int = 5, body: str = OLD_BODY) -> dict[str, Any]:
    return {
        "number": number,
        "state": "MERGED",
        "body": body.replace("#5", f"#{issue_number}"),
        "labels": [{"name": "pr:ready-for-review"}],
        "headRefName": f"task/{issue_number}-x",
        "createdAt": "2026-10-20T00:00:00Z",
    }


def parent(state: str = "MERGED") -> dict[str, Any]:
    return {
        "number": 9,
        "state": state,
        "body": f"{MARKER}\nCloses #4",
        "labels": [],
        "headRefName": "task/4-p",
        "createdAt": "2026-10-19T00:00:00Z",
    }


@dataclass
class RescueHost(FakeHost):
    """FakeHost that answers `pr view`, `pr create`, `git merge-base` and `pr list --head`."""

    base: str = EPIC
    in_main: int = 1  # exit code of `git merge-base --is-ancestor`
    existing: list[dict[str, Any]] = field(default_factory=list)
    created: list[list[str]] = field(default_factory=list)
    bodies: list[str] = field(default_factory=list)
    new_number: int = 77
    create_fails: bool = False

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[0] == "git":
            self.calls.append(args)
            return self.in_main, ""
        if args[1:3] == ["pr", "view"]:
            self.calls.append(args)
            number = int(args[3])
            pr = next(p for p in self.prs if p["number"] == number)
            return 0, json.dumps(pr | {"baseRefName": self.base, "headRefOid": "abc", "title": "T"})
        if args[1:3] == ["pr", "list"] and "--head" in args:
            self.calls.append(args)
            return 0, json.dumps(self.existing)
        if args[1:3] == ["pr", "create"]:
            self.calls.append(args)
            self.created.append(args)
            self.bodies.append(Path(args[args.index("--body-file") + 1]).read_text())
            if self.create_fails:
                return 1, "boom"
            return 0, f"https://github.com/o/r/pull/{self.new_number}\n"
        return super().run(args, cwd)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def host_with(*prs: dict[str, Any], **extra: Any) -> RescueHost:
    return RescueHost(prs=list(prs), issues=[issue(5)], **extra)


def record(home: Path) -> list[str]:
    path = home / "epic-rescued"
    return path.read_text().split() if path.exists() else []


# AC1: a new pull request into main, same title and body without the Stacked line


def test_merged_epic_pull_request_gets_a_new_one_into_main(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1)
    agent_tick.tick_once(host, home)
    assert len(host.created) == 1
    args = host.created[0]
    assert args[args.index("--base") + 1] == "main"
    assert args[args.index("--head") + 1] == "task/5-x"
    assert args[args.index("--title") + 1] == "T"
    assert "Stacked on" not in host.bodies[0]
    assert (
        MARKER in host.bodies[0] and "Closes #5" in host.bodies[0] and "Report: x" in host.bodies[0]
    )


def test_pull_request_merged_into_main_is_not_rescued(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1, base="main")
    agent_tick.tick_once(host, home)
    assert host.created == []


def test_head_already_in_main_needs_nothing(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=0)
    agent_tick.tick_once(host, home)
    assert host.created == [] and record(home) == ["20"]


def test_closed_issue_needs_nothing(home: Path) -> None:
    host = RescueHost(prs=[merged(), parent()], issues=[], in_main=1)
    agent_tick.tick_once(host, home)
    assert host.created == []


def test_pull_request_without_the_marker_is_never_rescued(home: Path) -> None:
    host = host_with(merged(body="Closes #5"), parent(), in_main=1)
    agent_tick.tick_once(host, home)
    assert host.created == []


def test_an_open_pull_request_into_main_for_the_branch_blocks_a_second(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1, existing=[{"number": 50}])
    agent_tick.tick_once(host, home)
    assert host.created == [] and record(home) == ["20"]


# AC2: labels, log, one ntfy message


def test_new_pull_request_gets_the_label_the_issue_review_and_one_message(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1)
    log = agent_tick.tick_once(host, home)
    assert any(c[2:5] == ["edit", "77", "--add-label"] for c in host.gh_calls("pr", "edit"))
    assert any(
        c[:6] == ["gh", "issue", "edit", "5", "--add-label", "agent:review"] for c in host.calls
    )
    assert f"pr-20: merged into {EPIC}; opened PR #77 into main for #5" in log
    sent = [m for m in host.sent if "was merged into" in m]
    assert sent == [f"rr-test: PR #20 was merged into {EPIC}, not main: opened PR #77 for #5"]


def test_label_is_not_added_when_the_old_pull_request_was_not_ready(home: Path) -> None:
    old = merged() | {"labels": []}
    host = host_with(old, parent(), in_main=1)
    agent_tick.tick_once(host, home)
    assert not [c for c in host.gh_calls("pr", "edit") if "pr:ready-for-review" in c]


# AC3: waits for an open parent; a closed one stops the rescue with one message


def test_waits_while_a_stacked_parent_is_open(home: Path) -> None:
    host = host_with(merged(), parent("OPEN"), in_main=1)
    log = agent_tick.tick_once(host, home)
    assert host.created == [] and record(home) == []
    assert f"pr-20: merged into {EPIC}; waits for #9 before opening a pull request into main" in log


def test_parent_closed_without_merge_opens_nothing_and_tells_once(home: Path) -> None:
    host = host_with(merged(), parent("CLOSED"), in_main=1)
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert host.created == []
    assert len([m for m in host.sent if "closed without merge" in m]) == 1


# AC4: once per old pull request; one failure never stops the others


def test_a_rescued_pull_request_is_handled_once(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1)
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert len(host.created) == 1 and record(home) == ["20"]


def test_a_failed_create_is_retried_at_the_next_tick(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1, create_fails=True)
    log = agent_tick.tick_once(host, home)
    assert record(home) == [] and any("not opened" in line for line in log)
    host.create_fails = False
    agent_tick.tick_once(host, home)
    assert record(home) == ["20"]


def test_one_failure_does_not_stop_the_other_rescue(home: Path) -> None:
    second = merged(number=21, issue_number=6)
    host = RescueHost(prs=[merged(), second, parent()], issues=[issue(5), issue(6)], in_main=1)
    original = host.run

    def run(args: Any, cwd: Path | None = None) -> tuple[int, str]:
        if list(args)[1:4] == ["pr", "view", "20"]:
            return 1, "boom"
        return original(args, cwd)

    host.run = run  # type: ignore[method-assign]
    agent_tick.tick_once(host, home)
    assert len(host.created) == 1 and "task/6-x" in host.created[0]


def test_agent_review_set_by_the_rescue_is_not_removed_by_tidy_ended(home: Path) -> None:
    host = RescueHost(
        prs=[merged(), parent()],
        issues=[issue(5, "agent:review")],
        in_main=1,
    )
    agent_tick.tick_once(host, home)
    removed = [c for c in host.calls if c[1:3] == ["issue", "edit"] and "--remove-label" in c]
    assert not [c for c in removed if "agent:review" in c]


# AC5: the new pull request is a normal loop pull request (marker kept)


def test_new_pull_request_body_keeps_the_marker_so_it_is_a_loop_pull_request(home: Path) -> None:
    host = host_with(merged(), parent(), in_main=1)
    agent_tick.tick_once(host, home)
    assert agent_tick.MARKER in host.bodies[0]
