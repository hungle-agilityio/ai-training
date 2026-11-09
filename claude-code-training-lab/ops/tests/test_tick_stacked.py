"""#165: the tick starts a task on its parent's green pull request. Run: pytest ops"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, OWNER, REPO
from ops.tests.test_agent_tick import issue, pull, started
from ops.tests.test_tick_hardening import GitHost
from ops.tests.test_tick_merge import ReviewHost, loop_pr, remark
from ops.tests.test_tick_waiting import WaitingHost

FILES = "## Files likely touched\n\n- `ops/x.py`\n"
OLD = "1111111aaaaaaa"
NEW = "2222222bbbbbbb"
HEAD = "abc1234def5678"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def parent_pr(number: int = 30, closes: int = 4, *labels: str, **fields: Any) -> dict[str, Any]:
    found = pull(number, *(labels or ("pr:ready-for-review",)), closes=closes)
    found |= {
        "headRefName": f"task/{closes}-parent",
        "headRefOid": HEAD,
        "title": "Parent work",
        "isDraft": False,
        "baseRefName": "main",
    }
    return found | fields


def child(number: int = 5, *labels: str, depends: str = "Depends on #4\n") -> dict[str, Any]:
    return issue(number, *(labels or ("agent:ready",)), body=depends + "\n" + FILES)


def prompt(n: int = 5, q: int = 30, branch: str = "task/4-parent") -> str:
    return (
        f"Use the work-queue skill for issue #{n} only. Stacked on pull request #{q}: "
        f"branch from origin/{branch} and open the pull request into {branch} "
        "as a draft (`gh pr create --draft`)."
    )


def tick(
    home: Path,
    prs: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    git: dict[str, tuple[int, str]] | None = None,
) -> GitHost:
    host = GitHost(prs=prs, issues=issues, git=git or {})
    agent_tick.tick_once(host, home)
    return host


PARENT_ISSUE = issue(4, "agent:review", body=FILES.replace("x.py", "p.py"))


# AC1: when a task starts stacked


def test_child_starts_on_the_green_pull_request_of_its_one_unmerged_dependency(
    home: Path,
) -> None:
    host = tick(home, [parent_pr()], [PARENT_ISSUE, child()])
    assert started(host) == [prompt()]


@pytest.mark.parametrize(
    "parent",
    [
        parent_pr(labels=[{"name": "pr:changes-requested"}]),
        parent_pr(isDraft=True),
        parent_pr(statusCheckRollup=[{"conclusion": "FAILURE"}]),
        parent_pr(statusCheckRollup=[]),
        parent_pr(state="CLOSED"),
        parent_pr(body="no marker"),
        parent_pr(headRefOid=""),
    ],
    ids=["not-ready", "draft", "red", "no-checks", "closed", "not-the-loops", "no-head"],
)
def test_parent_pull_request_that_does_not_qualify_keeps_the_child_waiting(
    home: Path, parent: dict[str, Any]
) -> None:
    host = tick(home, [parent], [PARENT_ISSUE, child()])
    assert [p for p in started(host) if "issue #5" in p] == []


def test_running_check_keeps_the_child_waiting(home: Path) -> None:
    running = parent_pr(statusCheckRollup=[{"status": "IN_PROGRESS"}])
    assert started(tick(home, [running], [PARENT_ISSUE, child()])) == []


def test_two_unmet_dependencies_keep_the_child_waiting(home: Path) -> None:
    other = issue(3, "agent:running", body=FILES.replace("x.py", "q.py"))
    host = tick(home, [parent_pr()], [PARENT_ISSUE, other, child(depends="Depends on #3, #4\n")])
    assert started(host) == []


def test_parent_closed_as_not_planned_does_not_stack(home: Path) -> None:
    host = WaitingHost(prs=[parent_pr()], issues=[child()], reasons={4: "NOT_PLANNED"})
    agent_tick.tick_once(host, home)
    assert [p for p in started(host) if "issue #5" in p] == []


def test_manual_child_does_not_start_stacked(home: Path) -> None:
    host = tick(home, [parent_pr()], [PARENT_ISSUE, child(5, "agent:ready", "agent:manual")])
    assert started(host) == []


def test_blocked_message_does_not_list_a_child_that_can_start(home: Path) -> None:
    host = tick(home, [parent_pr()], [PARENT_ISSUE, child()])
    assert [m for m in host.sent if "ready issues blocked" in m] == []


# AC2: the worktree, the prompt, the message and the record


def test_worktree_is_detached_at_the_parent_branch_after_a_fetch(home: Path) -> None:
    host = tick(home, [parent_pr()], [PARENT_ISSUE, child()])
    fetch = host.git_calls("fetch origin main task/4-parent")
    add = host.git_calls("worktree add --detach")
    assert fetch and add and add[0][-1] == "origin/task/4-parent"
    assert host.calls.index(fetch[0]) < host.calls.index(add[0])


def test_start_message_names_the_parent_pull_request(home: Path) -> None:
    host = tick(home, [parent_pr()], [PARENT_ISSUE, child()])
    assert "rr-test: ReviewRadar started #5 on top of PR #30: Parent work" in host.sent


def test_record_holds_the_parent_pull_request_branch_and_head(home: Path) -> None:
    tick(home, [parent_pr()], [PARENT_ISSUE, child()])
    data = json.loads((home / "stacked" / "5").read_text())
    assert data == {"pr": 30, "branch": "task/4-parent", "head": HEAD}


def test_a_normal_start_has_no_stacked_record_and_the_plain_prompt(home: Path) -> None:
    (home / "stacked").mkdir()
    (home / "stacked" / "5").write_text("{}")
    host = tick(home, [], [issue(5, "agent:ready", body=FILES)])
    assert started(host) == ["Use the work-queue skill for issue #5 only."]
    assert not (home / "stacked" / "5").exists()


# AC3: the files of the parent do not hold the child


def test_files_of_the_parent_are_ignored_for_the_child(home: Path) -> None:
    shared = issue(4, "agent:review", body=FILES)
    host = tick(home, [parent_pr()], [shared, child()])
    assert started(host) == [prompt()]


def test_file_shared_with_another_running_issue_still_holds_the_child(home: Path) -> None:
    other = issue(9, "agent:running", body=FILES)
    host = tick(home, [parent_pr()], [PARENT_ISSUE | {"body": FILES}, other, child()])
    assert started(host) == []


def test_files_of_the_parents_parent_are_ignored_in_a_chain(home: Path) -> None:
    grand = issue(3, "agent:review", body=FILES)
    mid = issue(4, "agent:review", body=FILES.replace("x.py", "y.py") + "Depends on #3\n")
    grand_pr = parent_pr(29, 3)
    mid_pr = parent_pr(30, 4, baseRefName="task/3-parent", headRefName="task/4-parent")
    host = tick(home, [grand_pr, mid_pr], [grand, mid, child(depends="Depends on #4\n")])
    assert started(host) == [prompt()]


# AC4: a green child can be the parent of the next issue


def test_a_stacked_green_pull_request_can_be_a_parent(home: Path) -> None:
    mid = parent_pr(30, 4, baseRefName="task/3-parent")
    host = tick(home, [mid], [PARENT_ISSUE, child()])
    assert started(host) == [prompt()]


# AC5: no merge into a branch that is not main


def merge_host(*, base: str, comments: tuple[dict[str, Any], ...]) -> ReviewHost:
    pr = loop_pr(*comments) | {"baseRefName": base}
    parent = parent_pr(30, 4, headRefName="task/4-parent")
    return ReviewHost(prs=[pr, parent], issues=[issue(5, "agent:review")])


def test_pull_request_based_on_another_branch_is_never_merged(home: Path) -> None:
    host = merge_host(base="task/4-parent", comments=(remark(1, "lgtm"),))
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "merge") == []
    assert "rr-test: ReviewRadar PR #20 not merged: it waits for its parent PR #30" in host.sent


def test_the_waiting_message_comes_once_per_approval_and_the_approval_stays_valid(
    home: Path,
) -> None:
    host = merge_host(base="task/4-parent", comments=(remark(1, "lgtm"),))
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "waits for its parent PR #30" in m]) == 1
    assert not any("reactions" in " ".join(c) for c in host.calls)


def test_a_new_approval_gets_its_own_message(home: Path) -> None:
    host = merge_host(base="task/4-parent", comments=(remark(1, "lgtm"),))
    agent_tick.tick_once(host, home)
    host.prs[0]["comments"].append(remark(2, "ok", when="2026-10-22T00:00:00Z"))
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "waits for its parent PR #30" in m]) == 2


def test_approval_merges_once_the_base_is_main(home: Path) -> None:
    host = merge_host(base="main", comments=(remark(1, "lgtm"),))
    agent_tick.tick_once(host, home)
    assert len(host.gh_calls("pr", "merge")) == 1


# AC6, AC7: when the parent is merged or closed


def based_on_parent(number: int = 31, *labels: str) -> dict[str, Any]:
    found = pull(number, *(labels or ("pr:ready-for-review",)), closes=5)
    return found | {"baseRefName": "task/4-parent", "headRefName": "task/5-child"}


def test_merged_parent_retargets_each_open_child_to_main(home: Path) -> None:
    merged = parent_pr(30, 4, state="MERGED")
    host = tick(home, [merged, based_on_parent()], [issue(5, "agent:review")])
    assert ["gh", "pr", "edit", "31", "--base", "main", "--repo", REPO] in host.calls


def test_child_already_on_main_is_left_alone(home: Path) -> None:
    merged = parent_pr(30, 4, state="MERGED")
    done = based_on_parent() | {"baseRefName": "main"}
    host = tick(home, [merged, done], [issue(5, "agent:review")])
    assert not [c for c in host.gh_calls("pr", "edit") if "--base" in c]


def test_closed_parent_blocks_the_child_with_a_comment_and_one_message(home: Path) -> None:
    closed = parent_pr(30, 4, state="CLOSED")
    child_pr = based_on_parent(31, "pr:changes-requested")
    host = tick(home, [closed, child_pr], [issue(5, "agent:review")])
    assert [
        "gh",
        "pr",
        "edit",
        "31",
        "--add-label",
        "pr:blocked",
        "--remove-label",
        "pr:changes-requested",
        "--repo",
        REPO,
    ] in host.calls
    body = (
        f"{MARKER}\nThe parent pull request #30 was closed without merge. "
        "This pull request is built on it and is not merged."
    )
    assert ["gh", "pr", "comment", "31", "--body", body, "--repo", REPO] in host.calls
    assert host.sent.count("rr-test: ReviewRadar PR #31 blocked: its parent PR #30 was closed") == 1


def test_closed_parent_is_announced_once(home: Path) -> None:
    closed = parent_pr(30, 4, state="CLOSED")
    host = tick(home, [closed, based_on_parent(31)], [issue(5, "agent:review")])
    agent_tick.tick_once(host, home)
    assert len(host.gh_calls("pr", "comment")) == 1
    assert len([m for m in host.sent if "blocked: its parent" in m]) == 1


# AC8: a change to the parent does nothing to the child


def test_parent_changes_do_not_start_a_run_on_the_child(home: Path) -> None:
    changed = parent_pr(30, 4, "pr:changes-requested")
    host = tick(home, [changed, based_on_parent()], [issue(5, "agent:review")])
    assert [p for p in started(host) if "#31" in p] == []


# AC9: a stopped failure is retried when the parent moved


def write_failed(home: Path, **fields: Any) -> None:
    folder = home / "failed"
    folder.mkdir(exist_ok=True)
    data = {"main": OLD, "kind": "stopped", "retries": 0, "outcome": "", "parent": OLD} | fields
    (folder / "5").write_text(json.dumps(data))


def failed_child() -> dict[str, Any]:
    return child(5, "agent:failed")


ON_MAIN = {"branch --show-current": (0, "main\n"), "rev-parse origin/main": (0, OLD + "\n")}


def test_failure_of_a_stacked_build_records_the_parent_head(home: Path) -> None:
    from ops.tests.test_agent_tick import add_run

    (home / "stacked").mkdir()
    (home / "stacked" / "5").write_text(json.dumps({"pr": 30, "branch": "b", "head": HEAD}))
    add_run(home, "issue-5", 77, exit_text="timeout", log="boom")
    tick(home, [], [issue(5, "agent:running")], ON_MAIN)
    assert json.loads((home / "failed" / "5").read_text())["parent"] == HEAD


def test_stopped_failure_is_retried_stacked_when_the_parent_head_moved(home: Path) -> None:
    write_failed(home, parent=OLD)
    host = tick(home, [parent_pr(headRefOid=NEW)], [PARENT_ISSUE, failed_child()], ON_MAIN)
    assert started(host) == [prompt()]
    comment = [
        "gh",
        "issue",
        "comment",
        "5",
        "--body",
        f"{MARKER}\nRetry 1 of 3: the parent pull request #30 moved from {OLD[:7]} to {NEW[:7]}.",
        "--repo",
        REPO,
    ]
    assert comment in host.calls
    assert json.loads((home / "failed" / "5").read_text())["parent"] == NEW


def test_stopped_failure_waits_while_the_parent_head_is_the_same(home: Path) -> None:
    write_failed(home, parent=HEAD)
    host = tick(home, [parent_pr()], [PARENT_ISSUE, failed_child()], ON_MAIN)
    assert started(host) == []


def test_retry_starts_from_main_when_the_parent_is_closed_and_main_moved(home: Path) -> None:
    write_failed(home, parent=OLD, main=NEW)
    host = tick(home, [], [failed_child()], ON_MAIN)
    assert started(host) == ["Use the work-queue skill for issue #5 only."]
    assert host.git_calls("worktree add --detach")[0][-1] == "origin/main"


def test_owner_constant_is_unchanged() -> None:
    assert OWNER == "hungle-agilityio"


# Review round 1: no merge on the tick that retargets, and one message for a blocked child


@pytest.mark.parametrize("fail", ["", "pr edit"], ids=["edit-ok", "edit-fails"])
def test_approved_child_of_a_merged_parent_is_not_merged_on_the_retarget_tick(
    home: Path, fail: str
) -> None:
    child_pr = loop_pr(remark(1, "lgtm")) | {"baseRefName": "task/4-parent"}
    merged = parent_pr(30, 4, state="MERGED", headRefName="task/4-parent")
    host = ReviewHost(prs=[child_pr, merged], issues=[issue(5, "agent:review")], fail=fail)
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "merge") == []
    assert any(c[:5] == ["gh", "pr", "edit", "20", "--base"] for c in host.calls)


def test_blocked_child_is_not_announced_again_as_needing_you(home: Path) -> None:
    closed = parent_pr(30, 4, state="CLOSED")
    host = tick(home, [closed, based_on_parent(31)], [issue(5, "agent:review")])
    host.prs[1]["labels"] = [{"name": "pr:blocked"}]
    agent_tick.tick_once(host, home)
    assert not [m for m in host.sent if "needs you" in m]


def test_failed_label_call_is_tried_again_at_the_next_tick(home: Path) -> None:
    closed = parent_pr(30, 4, state="CLOSED")
    host = GitHost(
        prs=[closed, based_on_parent(31)],
        issues=[issue(5, "agent:review")],
        fail="--add-label pr:blocked",
    )
    agent_tick.tick_once(host, home)
    assert not [m for m in host.sent if "blocked: its parent" in m]
    host.fail = ""
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "blocked: its parent" in m]) == 1
