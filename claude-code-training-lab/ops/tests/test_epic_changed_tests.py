"""#380: the epic pull request shows every test the tasks changed. Run: pytest ops/tests"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_epic_branch import epic_issue
from ops.tests.test_epic_pull_request import BRANCH, EPIC, Host, merged_task, task, the_epic_pr

HEADING = "## Tests changed by the tasks"
EARLIER = "reviews/tests/integration/test_compare_page.py"
NEW = "reviews/tests/integration/test_compare_topics.py"
CODE = "reviews/compare_views.py"


@dataclass
class FilesHost(Host):
    """Host that answers the changed files of each pull request."""

    files: dict[int, list[dict[str, str]]] = field(default_factory=dict)
    unreadable: set[int] = field(default_factory=set)

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[:2] == ["gh", "api"] and "/files" in args[2]:
            self.calls.append(args)
            number = int(args[2].split("/pulls/")[1].split("/")[0])
            if number in self.unreadable:
                return 1, "boom"
            return 0, json.dumps(self.files.get(number, []))
        return super().run(args, cwd)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def changed(path: str, status: str = "modified") -> dict[str, str]:
    return {"filename": f"claude-code-training-lab/{path}", "status": status}


def host_for(*prs: dict[str, Any], **kw: Any) -> FilesHost:
    host = FilesHost(branches={BRANCH}, **kw)
    host.prs = list(prs)
    host.issues = [epic_issue(), task(5), task(6)]
    return host


def two() -> tuple[dict[str, Any], dict[str, Any]]:
    return merged_task(20, 5), merged_task(21, 6)


def tick(host: FilesHost, home: Path) -> list[str]:
    return agent_tick.tick_once(host, home)


# AC2: every test a task changed, read from GitHub


def test_a_changed_test_is_listed_with_its_task_and_pull_request(home: Path) -> None:
    host = host_for(*two(), files={21: [changed(EARLIER), changed(CODE)]})
    tick(host, home)
    body = host.bodies[0]
    assert HEADING in body
    assert f"- `claude-code-training-lab/{EARLIER}`: changed by #6 in PR #21" in body
    assert CODE not in body


def test_a_removed_test_is_listed_too(home: Path) -> None:
    host = host_for(*two(), files={20: [changed(EARLIER, "removed")]})
    tick(host, home)
    assert f"{EARLIER}`: removed by #5 in PR #20" in host.bodies[0]


def test_a_new_test_is_not_listed(home: Path) -> None:
    host = host_for(*two(), files={20: [changed(NEW, "added")]})
    tick(host, home)
    assert HEADING not in host.bodies[0]


def test_no_change_means_no_section(home: Path) -> None:
    host = host_for(*two())
    tick(host, home)
    assert HEADING not in host.bodies[0]


def test_the_closes_lines_stay_last(home: Path) -> None:
    host = host_for(*two(), files={20: [changed(EARLIER)]})
    tick(host, home)
    assert host.bodies[0].rstrip().endswith(f"Closes #5\nCloses #6\nCloses #{EPIC}")


# AC3: a task merged while the epic pull request is open


def test_a_task_merged_later_adds_its_lines(home: Path) -> None:
    host = host_for(*two(), the_epic_pr(), files={21: [changed(EARLIER)]})
    tick(host, home)
    assert f"{EARLIER}`: changed by #6 in PR #21" in host.edits[0]
    assert host.edits[0].rstrip().endswith(f"Closes #5\nCloses #6\nCloses #{EPIC}")


def test_the_lines_are_added_once(home: Path) -> None:
    host = host_for(*two(), the_epic_pr(), files={21: [changed(EARLIER)]})
    tick(host, home)
    tick(host, home)
    assert len(host.edits) == 1
    assert host.prs[-1]["body"].count(EARLIER) == 1


# AC4: unreadable files open nothing


def test_unreadable_files_keep_the_pull_request_closed(home: Path) -> None:
    host = host_for(*two(), unreadable={20})
    log = tick(host, home)
    assert host.created == []
    assert any(line.startswith(f"epic #{EPIC}: files of PR #20 not read") for line in log)
    host.unreadable = set()
    tick(host, home)
    assert len(host.created) == 1
