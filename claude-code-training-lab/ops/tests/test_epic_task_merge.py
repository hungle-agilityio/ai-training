"""#364: the tick merges task pull requests into their epic branch. Run: pytest ops/tests"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import add_run, issue, started
from ops.tests.test_epic_branch import EpicHost, epic_issue, epic_pr, merges
from ops.tests.test_tick_hardening import GitHost
from ops.tests.test_tick_merge import remark

EPIC = 236
BRANCH = "epic/236-reply-to-reviews"
OTHER = "epic/237-other"
REF = f"--quiet refs/remotes/origin/{BRANCH}"
REPORT = "https://claude.ai/artifact/abc"
NO_BRANCH = {REF: (1, "")}
RED = [{"status": "COMPLETED", "conclusion": "FAILURE"}]


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def task(number: int, *labels: str, depends: tuple[int, ...] = (), epic: int = EPIC) -> Any:
    lines = [f"Part of the epic #{epic}", *[f"Depends on #{m}" for m in depends]]
    body = "\n".join(lines) + f"\n\n## Files likely touched\n\n- `reviews/t{number}.py`\n"
    return issue(number, *(labels or ("agent:ready",)), body=body)


def ready_issue() -> Any:
    return issue(EPIC, "epic", body="The epic.") | {"title": "Epic: reply to reviews"}


def start_tick(
    home: Path, issues: list[dict[str, Any]], git: dict[str, tuple[int, str]] | None = None
) -> tuple[GitHost, list[str]]:
    host = GitHost(prs=[], issues=issues, git=git or {})
    return host, agent_tick.tick_once(host, home)


def task_pr(number: int = 20, closes: int = 5, base: str = BRANCH, **kw: Any) -> dict[str, Any]:
    body = f"{MARKER}\nReport: {REPORT}\nCloses #{closes}"
    return epic_pr(number=number, closes=closes, **kw) | {"baseRefName": base, "body": body}


def host_for(*prs: dict[str, Any], **kw: Any) -> EpicHost:
    host = EpicHost(branches={BRANCH}, **kw)
    host.prs = list(prs)
    host.issues = [epic_issue(), task(5, "agent:review"), task(6, "agent:review")]
    return host


@dataclass
class RescueHost(EpicHost):
    """EpicHost that answers `gh pr view` with the pull request."""

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        if list(args)[:3] == ["gh", "pr", "view"]:
            self.calls.append(list(args))
            return 0, json.dumps(self.prs[0])
        return super().run(args, cwd)


def merged_numbers(host: EpicHost) -> list[str]:
    return [c[3] for c in host.gh_calls("pr", "merge")]


def task_labels(host: EpicHost) -> list[list[str]]:
    return [c for c in host.gh_calls("issue", "edit") if "agent:in-epic" in c]


# AC1: the first task creates the epic branch


def test_the_first_task_creates_the_epic_branch_before_its_build(home: Path) -> None:
    host, log = start_tick(home, [ready_issue(), task(5)], NO_BRANCH)
    calls = [" ".join(c) for c in host.calls if c[0] == "git"]
    push = next(i for i, c in enumerate(calls) if f"origin/main:refs/heads/{BRANCH}" in c)
    add = next(i for i, c in enumerate(calls) if "worktree add" in c and "issue-5" in c)
    assert push < add
    assert f"epic #{EPIC}: branch {BRANCH} created" in log


def test_a_task_that_waits_creates_no_branch(home: Path) -> None:
    issues = [ready_issue(), task(4, "agent:running"), task(5, depends=(4,))]
    host, _ = start_tick(home, issues, NO_BRANCH)
    assert host.git_calls("refs/heads/" + BRANCH) == []


def test_a_failed_creation_starts_nothing_and_is_logged(home: Path) -> None:
    git = {**NO_BRANCH, "push origin": (1, "denied")}
    host, log = start_tick(home, [ready_issue(), task(5)], git)
    assert started(host) == []
    assert f"epic #{EPIC}: {BRANCH} not created (denied)" in log


# AC2: every task starts from the epic branch and opens a normal pull request


def test_a_task_without_dependencies_starts_on_the_epic_branch(home: Path) -> None:
    host, _ = start_tick(home, [ready_issue(), task(5)])
    adds = [" ".join(c) for c in host.git_calls("worktree add")]
    assert any(f"origin/{BRANCH}" in c and "issue-5" in c for c in adds)
    prompt = started(host)[0]
    assert f"open a normal pull request into {BRANCH} (not a draft" in prompt
    assert "--draft" not in prompt
    assert "no `Stacked on` line" in prompt


# AC3: a dependency inside the epic is met by agent:in-epic


def test_a_dependency_in_the_epic_with_in_epic_is_met(home: Path) -> None:
    issues = [ready_issue(), task(4, "agent:in-epic"), task(5, depends=(4,))]
    host, _ = start_tick(home, issues)
    assert len(started(host)) == 1


def test_a_dependency_in_the_epic_without_in_epic_waits(home: Path) -> None:
    issues = [ready_issue(), task(4, "agent:running"), task(5, depends=(4,))]
    host, log = start_tick(home, issues)
    assert started(host) == []
    assert "#5 waits for #4: building" in log


def test_an_open_dependency_outside_the_epic_waits_even_with_the_label(home: Path) -> None:
    outside = task(4, "agent:in-epic", epic=999)
    host, _ = start_tick(home, [ready_issue(), outside, task(5, depends=(4,))])
    assert started(host) == []


# AC4: the older guards leave these pull requests alone


def test_a_pull_request_into_the_epic_branch_is_not_made_a_draft(home: Path) -> None:
    host = host_for(task_pr(labels=()))
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "ready") == []


def test_its_base_is_never_moved_to_main(home: Path) -> None:
    host = host_for(task_pr(), merge=(1, "no"))
    agent_tick.tick_once(host, home)
    assert not any("--base" in c for c in host.gh_calls("pr", "edit"))


def test_a_merged_task_is_not_rescued_into_main(home: Path) -> None:
    merged = task_pr() | {"state": "MERGED"}
    host = RescueHost(branches={BRANCH}, prs=[merged])
    host.issues = [epic_issue(), task(5, "agent:review"), task(6, "agent:running")]
    agent_tick.tick_once(host, home)
    assert any(c[:4] == ["gh", "pr", "view", "20"] for c in host.calls)
    assert host.gh_calls("pr", "create") == []
    assert (home / "epic-rescued").read_text() == "20"


# AC5: the conditions of the merge


def test_a_green_reported_task_is_merged_without_an_owner_comment(home: Path) -> None:
    host = host_for(task_pr())
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "merge")[0][:8] == [
        "gh", "pr", "merge", "20", "--merge", "--delete-branch",
        "--match-head-commit", "abc1234def",
    ]  # fmt: skip


@pytest.mark.parametrize(
    "pr",
    [
        task_pr() | {"isDraft": True},
        task_pr(labels=("pr:changes-requested",)),
        task_pr(checks=[]),
        task_pr(checks=RED),
        task_pr(checks=[{"status": "IN_PROGRESS", "conclusion": ""}]),
        task_pr() | {"body": f"{MARKER}\nCloses #5"},
        task_pr(state="BLOCKED"),
        task_pr(base="main"),
        task_pr(base=OTHER),
    ],
    ids=["draft", "label", "no-check", "red", "running", "no-report", "blocked", "main", "closed"],
)
def test_a_task_that_misses_a_condition_is_not_merged(home: Path, pr: dict[str, Any]) -> None:
    host = host_for(pr)
    agent_tick.tick_once(host, home)
    assert merged_numbers(host) == []


def test_an_open_change_request_stops_the_merge(home: Path) -> None:
    host = host_for(task_pr() | {"comments": [remark(1, "rename this")]})
    agent_tick.tick_once(host, home)
    assert merged_numbers(host) == []


def test_a_run_going_stops_the_merge(home: Path) -> None:
    host = host_for(task_pr())
    add_run(home, "pr-20", 42)
    host.alive_pids.add(42)
    agent_tick.tick_once(host, home)
    assert merged_numbers(host) == []


def test_a_behind_task_is_updated_and_merged_later(home: Path) -> None:
    host = host_for(task_pr(state="BEHIND"))
    log = agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "update-branch")
    assert merged_numbers(host) == []
    assert f"pr-20: behind {BRANCH}; branch updated" in log


@pytest.mark.parametrize(
    ("status", "update"), [("BEHIND", (1, "merge conflict")), ("DIRTY", (0, ""))]
)
def test_a_conflict_posts_one_redo_per_head(
    home: Path, status: str, update: tuple[int, str]
) -> None:
    host = host_for(task_pr(state=status), update=update)
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert [c[3:6] for c in host.comments] == [
        ["20", "--body", f"/redo merge origin/{BRANCH} into this branch and fix the conflict"]
    ]
    host.prs[0]["headRefOid"] = "second22"
    agent_tick.tick_once(host, home)
    assert len(host.comments) == 2
    assert merged_numbers(host) == []


def test_no_local_merge_into_the_epic_branch(home: Path) -> None:
    host = host_for(task_pr())
    agent_tick.tick_once(host, home)
    assert merges(host) == []


# AC6: after the merge


def test_the_issue_gets_in_epic_and_stays_open(home: Path) -> None:
    host = host_for(task_pr())
    log = agent_tick.tick_once(host, home)
    assert task_labels(host)[0][3:8] == [
        "5", "--add-label", "agent:in-epic",
        "--remove-label", "agent:review,agent:running,agent:ready",
    ]  # fmt: skip
    assert host.gh_calls("issue", "close") == []
    assert f"pr-20: merged into {BRANCH}; #5 agent:in-epic" in log


def test_one_message_and_no_main_announcement(home: Path) -> None:
    host = host_for(task_pr())
    agent_tick.tick_once(host, home)
    host.prs[0]["state"] = "MERGED"
    agent_tick.tick_once(host, home)
    wanted = f"rr-test: PR #20 merged into {BRANCH} (#5)"
    assert [m for m in host.sent if "merged" in m] == [wanted]


def test_a_merge_by_hand_is_settled_once_at_the_next_tick(home: Path) -> None:
    host = host_for(task_pr() | {"state": "MERGED"})
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert merged_numbers(host) == []
    assert len(task_labels(host)) == 1


def test_a_failed_label_is_tried_again_and_sends_nothing(home: Path) -> None:
    host = host_for(task_pr() | {"state": "MERGED"})
    host.fail = "--add-label agent:in-epic"
    log = agent_tick.tick_once(host, home)
    assert any("agent:in-epic not set" in line for line in log)
    assert [m for m in host.sent if "merged" in m] == []
    host.fail = ""
    agent_tick.tick_once(host, home)
    assert len([m for m in host.sent if "merged" in m]) == 1


def test_a_task_set_ready_again_keeps_its_label(home: Path) -> None:
    host = host_for(task_pr() | {"state": "MERGED"})
    agent_tick.tick_once(host, home)
    host.issues[1] = task(5)
    agent_tick.tick_once(host, home)
    assert len(task_labels(host)) == 1


# AC7: one merge per epic branch and tick


def test_only_one_task_is_merged_into_a_branch_per_tick(home: Path) -> None:
    host = host_for(task_pr(21, 6, oid="b2"), task_pr(20, 5))
    agent_tick.tick_once(host, home)
    assert merged_numbers(host) == ["20"]


def test_two_epics_each_merge_one(home: Path) -> None:
    host = host_for(task_pr(20, 5), task_pr(21, 7, base=OTHER))
    host.issues += [epic_issue(237, "Epic: other"), task(7, "agent:review", epic=237)]
    agent_tick.tick_once(host, home)
    assert merged_numbers(host) == ["20", "21"]
