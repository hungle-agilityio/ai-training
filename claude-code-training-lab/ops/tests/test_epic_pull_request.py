"""#366: one pull request per epic from its branch into main. Run: pytest ops/tests"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import issue, started
from ops.tests.test_epic_branch import EpicHost, epic_issue, epic_pr
from ops.tests.test_tick_merge import remark

EPIC = 236
BRANCH = "epic/236-reply-to-reviews"
LINK = "https://claude.ai/artifact/abc"
NEW_PR = 30
RED = [{"status": "COMPLETED", "conclusion": "FAILURE"}]


@dataclass
class Host(EpicHost):
    """EpicHost that keeps the text of `gh pr create` and `gh pr edit --body-file`."""

    created: list[list[str]] = field(default_factory=list)
    bodies: list[str] = field(default_factory=list)
    edits: list[str] = field(default_factory=list)
    fail_create: bool = False

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        args = list(args)
        if args[:3] == ["gh", "pr", "create"]:
            self.calls.append(args)
            if self.fail_create:
                return 1, "boom"
            self.created.append(args)
            self.bodies.append(Path(args[args.index("--body-file") + 1]).read_text())
            return 0, f"https://github.com/o/r/pull/{NEW_PR}\n"
        if args[:3] == ["gh", "pr", "edit"] and "--body-file" in args:
            self.calls.append(args)
            text = Path(args[args.index("--body-file") + 1]).read_text()
            self.edits.append(text)
            next(p for p in self.prs if p["number"] == int(args[3]))["body"] = text
            return 0, ""
        return super().run(args, cwd)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def task(number: int, *labels: str) -> Any:
    return issue(number, *(labels or ("agent:in-epic",)), body=f"Part of the epic #{EPIC}\n")


def merged_task(number: int, closes: int) -> dict[str, Any]:
    body = f"{MARKER}\nReport: {LINK}{closes}\nCloses #{closes}"
    pr = epic_pr(number=number, closes=closes)
    return pr | {"state": "MERGED", "baseRefName": BRANCH, "body": body}


def the_epic_pr(*comments: dict[str, Any], **kw: Any) -> dict[str, Any]:
    body = f"{MARKER}\n| task |\nCloses #5\nCloses #{EPIC}"
    pr = epic_pr(number=NEW_PR, **kw)
    return pr | {"headRefName": BRANCH, "body": body, "comments": list(comments)}


def host_for(*prs: dict[str, Any], tasks: tuple[Any, ...] = (), **kw: Any) -> Host:
    kw.setdefault("branches", {BRANCH})
    host = Host(**kw)
    host.prs = list(prs)
    host.issues = [epic_issue(), *(tasks or (task(5), task(6)))]
    return host


def two_merged() -> tuple[dict[str, Any], dict[str, Any]]:
    return merged_task(20, 5), merged_task(21, 6)


def tick(host: Host, home: Path) -> list[str]:
    return agent_tick.tick_once(host, home)


# AC1: when every task is in the epic branch


def test_the_epic_pull_request_opens_when_every_task_is_in(home: Path) -> None:
    host = host_for(*two_merged())
    tick(host, home)
    args = host.created[0]
    assert args[3:9] == ["--base", "main", "--head", BRANCH, "--title", "[EPIC] reply to reviews"]
    body = host.bodies[0]
    assert body.startswith(MARKER)
    assert f"| #5 | #20 | {LINK}5 |" in body
    assert f"| #6 | #21 | {LINK}6 |" in body
    assert body.rstrip().endswith(f"Closes #5\nCloses #6\nCloses #{EPIC}")
    wanted = f"rr-test: Epic #{EPIC} is ready for your review: PR #{NEW_PR}"
    assert host.sent.count(wanted) == 1


def test_it_is_not_opened_twice(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr())
    tick(host, home)
    assert host.created == []


def test_a_pull_request_of_the_owner_counts_as_open(home: Path) -> None:
    host = host_for(*two_merged(), open_on_branch='[{"number": 77}]')
    tick(host, home)
    assert host.created == []


@pytest.mark.parametrize(
    "tasks",
    [(task(5), task(6, "agent:review")), (task(5, "agent:ready"), task(6, "agent:failed"))],
    ids=["one-open", "none-in"],
)
def test_it_waits_for_every_task(home: Path, tasks: tuple[Any, ...]) -> None:
    host = host_for(tasks=tasks)
    tick(host, home)
    assert host.created == []


def test_an_epic_with_no_open_task_opens_nothing(home: Path) -> None:
    host = host_for()
    host.issues = [epic_issue()]
    tick(host, home)
    assert host.created == []


def test_a_task_closed_as_not_planned_is_ignored(home: Path) -> None:
    closed = task(6, "agent:review") | {"closed": True}
    host = host_for(merged_task(20, 5), tasks=(task(5), closed))
    tick(host, home)
    assert len(host.created) == 1
    assert "Closes #6" not in host.bodies[0]


def test_main_is_merged_into_the_branch_before_it_opens(home: Path) -> None:
    host = host_for(*two_merged(), in_branch=set())
    tick(host, home)
    assert any(p[2] == f"HEAD:refs/heads/{BRANCH}" for p in host.pushes)
    assert len(host.created) == 1


def test_a_conflict_with_main_keeps_it_closed(home: Path) -> None:
    host = host_for(*two_merged(), in_branch=set(), conflicts={"origin/main"})
    log = tick(host, home)
    assert host.created == []
    assert f"epic #{EPIC}: pull request waits, {BRANCH} does not have main" in log


def test_a_failed_create_is_logged_and_sends_nothing(home: Path) -> None:
    host = host_for(*two_merged(), fail_create=True)
    log = tick(host, home)
    assert any(line.startswith(f"epic #{EPIC}: pull request not opened") for line in log)
    assert not [m for m in host.sent if "ready for your review" in m]


# AC2: no run for it; the label comes with green checks


def test_an_unlabelled_epic_pull_request_starts_no_run(home: Path) -> None:
    review = remark(7, f"{MARKER}\n<!-- epic-review -->\n## Epic review\n\nNo findings.")
    host = host_for(*two_merged(), the_epic_pr(review, labels=()))
    tick(host, home)
    assert started(host) == []


def test_green_checks_label_it_ready_even_without_a_report_link(home: Path) -> None:
    review = remark(7, f"{MARKER}\n<!-- epic-review -->\n## Epic review\n\nNo findings.")
    host = host_for(*two_merged(), the_epic_pr(review, labels=()))
    tick(host, home)
    assert any("pr:ready-for-review" in c for c in host.gh_calls("pr", "edit", str(NEW_PR)))


def test_red_checks_do_not_label_it(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=(), checks=RED))
    tick(host, home)
    assert not any("pr:ready-for-review" in c for c in host.gh_calls("pr", "edit", str(NEW_PR)))


# AC3: the owner's approval merges it


def test_the_approval_comment_merges_it_and_deletes_the_branch(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(remark(1, "/merge")))
    tick(host, home)
    merge = host.gh_calls("pr", "merge")[0]
    assert merge[3:6] == [str(NEW_PR), "--merge", "--delete-branch"]


def test_no_approval_no_merge(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr())
    tick(host, home)
    assert host.gh_calls("pr", "merge") == []


# AC4: any other comment is a change request on the epic branch


def test_another_comment_starts_a_run_on_the_epic_branch(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(remark(1, "rename the heading")))
    tick(host, home)
    assert started(host) == [f"Use the work-queue skill for pull request #{NEW_PR} only."]
    assert any(c[3:6] == ["worktree", "add", "-B"] and BRANCH in c for c in host.calls)


# AC5: a task that arrives later


def test_a_task_merged_later_gets_its_closes_line(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr())
    tick(host, home)
    assert host.edits[0].rstrip().endswith(f"Closes #5\nCloses #6\nCloses #{EPIC}")


def test_the_line_is_added_once(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr())
    tick(host, home)
    tick(host, home)
    assert len(host.edits) == 1


def test_a_task_not_in_the_branch_gets_no_line(home: Path) -> None:
    host = host_for(merged_task(20, 5), the_epic_pr(), tasks=(task(5), task(6, "agent:running")))
    tick(host, home)
    assert host.edits == []


# AC6: main keeps moving into the branch while the pull request is open


def test_main_still_goes_into_the_branch(home: Path) -> None:
    host = host_for(the_epic_pr(), in_branch=set())
    tick(host, home)
    assert any(p[2] == f"HEAD:refs/heads/{BRANCH}" for p in host.pushes)


def test_a_conflict_with_main_is_reported_once_per_hour(home: Path) -> None:
    host = host_for(the_epic_pr(), in_branch=set(), conflicts={"origin/main"})
    tick(host, home)
    tick(host, home)
    assert len([m for m in host.sent if "does not merge with main" in m]) == 1


# The first Closes line of the epic pull request is not its issue


def test_the_issue_of_the_epic_pull_request_is_the_epic() -> None:
    assert agent_tick.closes(the_epic_pr()) == EPIC


def test_the_first_task_does_not_get_agent_review_from_it(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr())
    tick(host, home)
    calls = [json.dumps(c) for c in host.gh_calls("issue", "edit")]
    assert not any('"--add-label", "agent:review"' in c for c in calls)
