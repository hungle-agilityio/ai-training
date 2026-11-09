"""#264: tasks of an epic start on the epic branch (spec epic-branch AC7 to AC12)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import issue, pull, started
from ops.tests.test_tick_hardening import GitHost

EPIC = 236
BRANCH = "epic/236-reply-to-reviews"
HEAD_A = "aaaa1111aaaa1111"
HEAD_B = "bbbb2222bbbb2222"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def files(name: str) -> str:
    return f"## Files likely touched\n\n- `reviews/{name}.py`\n"


def epic_issue() -> dict[str, Any]:
    found = issue(EPIC, "epic", body="The epic.")
    return found | {"title": "Epic: reply to reviews"}


def task(
    number: int, *labels: str, depends: tuple[int, ...] = (), epic: int | None = EPIC
) -> dict[str, Any]:
    lines = [f"Part of the epic #{epic}." if epic else "No epic."]
    lines += [f"Depends on #{m}" for m in depends]
    body = "\n".join(lines) + "\n\n" + files(f"t{number}")
    return issue(number, *(labels or ("agent:ready",)), body=body)


def dep_pr(number: int, closes: int, head: str, **fields: Any) -> dict[str, Any]:
    found = pull(number, "pr:ready-for-review", closes=closes)
    found |= {
        "headRefName": f"task/{closes}-dep",
        "headRefOid": head,
        "title": f"Dependency {closes}",
        "isDraft": False,
        "baseRefName": "main",
    }
    return found | fields


def deps() -> list[dict[str, Any]]:
    return [task(240, "agent:review"), task(241, "agent:review")]


def prs() -> list[dict[str, Any]]:
    return [dep_pr(252, 240, HEAD_A), dep_pr(251, 241, HEAD_B)]


def epic_prompt(n: int = 242, listed: str = "#251, #252") -> str:
    return (
        f"Use the work-queue skill for issue #{n} only. Stacked on epic branch {BRANCH}: "
        f"branch from origin/{BRANCH} and open the pull request into {BRANCH} "
        "as a draft (`gh pr create --draft`). Put the line "
        f"`Stacked on {listed} through {BRANCH} (merge those first).` just above `Closes #{n}`."
    )


def tick(
    home: Path,
    pulls: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    git: dict[str, tuple[int, str]] | None = None,
) -> tuple[GitHost, list[str]]:
    host = GitHost(prs=pulls, issues=issues, git=git or {})
    log = agent_tick.tick_once(host, home)
    return host, log


# AC1, AC2: the task starts at once on the epic branch, with the stacked line


def test_a_task_with_two_dependencies_in_the_epic_branch_starts_on_it(home: Path) -> None:
    host, _ = tick(home, prs(), [epic_issue(), *deps(), task(242, depends=(240, 241))])
    assert started(host) == [epic_prompt()]
    adds = host.git_calls("worktree add")
    assert any(f"origin/{BRANCH}" in c and "issue-242" in " ".join(c) for c in adds)


def test_the_start_record_names_the_epic_branch_and_the_pull_requests(home: Path) -> None:
    tick(home, prs(), [epic_issue(), *deps(), task(242, depends=(240, 241))])
    record = agent_tick.stacked_record_of(home, 242)
    assert record is not None
    assert record["branch"] == BRANCH
    assert record["prs"] == [251, 252]


# AC5: one dependency uses the epic branch too; no epic keeps ADR-018


def test_one_open_dependency_of_an_epic_task_uses_the_epic_branch(home: Path) -> None:
    host, _ = tick(
        home,
        [dep_pr(252, 240, HEAD_A)],
        [epic_issue(), task(240, "agent:review"), task(242, depends=(240,))],
    )
    assert started(host) == [epic_prompt(listed="#252")]


def test_a_task_without_an_epic_keeps_the_one_parent_stacking(home: Path) -> None:
    host, _ = tick(
        home,
        [dep_pr(252, 240, HEAD_A)],
        [task(240, "agent:review", epic=None), task(242, depends=(240,), epic=None)],
    )
    assert started(host) == [
        "Use the work-queue skill for issue #242 only. Stacked on pull request #252: "
        "branch from origin/task/240-dep and open the pull request into task/240-dep "
        "as a draft (`gh pr create --draft`)."
    ]


# AC6: a dependency outside the epic branch keeps the task waiting, with the reason


@pytest.mark.parametrize(
    ("change", "git", "reason"),
    [
        ({"statusCheckRollup": [{"conclusion": "FAILURE"}]}, {}, "checks are red"),
        ({"isDraft": True}, {}, "it is a draft"),
        ({"labels": [{"name": "pr:changes-requested"}]}, {}, "it is not ready for review"),
        ({}, {f"--is-ancestor {HEAD_A}": (1, "")}, "not merged into it yet"),
    ],
    ids=["red", "draft", "not-ready", "not-merged-in"],
)
def test_a_dependency_not_in_the_epic_branch_keeps_the_task_waiting(
    home: Path, change: dict[str, Any], git: dict[str, tuple[int, str]], reason: str
) -> None:
    pulls = [dep_pr(252, 240, HEAD_A, **change), dep_pr(251, 241, HEAD_B)]
    host, log = tick(home, pulls, [epic_issue(), *deps(), task(242, depends=(240, 241))], git)
    assert not any("issue #242" in s for s in started(host))
    assert f"#242 waits for #240: PR #252 is not in {BRANCH} ({reason})" in log


def test_no_epic_branch_yet_keeps_the_task_waiting(home: Path) -> None:
    host, log = tick(
        home,
        prs(),
        [epic_issue(), *deps(), task(242, depends=(240, 241))],
        {f"refs/remotes/origin/{BRANCH}": (1, "")},
    )
    assert started(host) == []
    assert any(line.startswith("#242 waits for #240:") and BRANCH in line for line in log)


def test_a_dependency_of_another_epic_must_be_merged_first(home: Path) -> None:
    other = task(240, "agent:review", epic=999)
    host, _ = tick(
        home, prs(), [epic_issue(), other, task(241, "agent:review"), task(242, depends=(240, 241))]
    )
    assert started(host) == []


# AC3: never merged into the epic branch; base moves to main once the dependencies merged


def child_pr(state_a: str = "MERGED", state_b: str = "MERGED") -> list[dict[str, Any]]:
    kid = pull(260, "pr:ready-for-review", closes=242) | {
        "baseRefName": BRANCH,
        "headRefName": "feat/242-x",
        "body": f"{MARKER}\nStacked on #251, #252 through {BRANCH} (merge those first).\n"
        "Closes #242",
    }
    return [kid, dep_pr(251, 241, HEAD_B, state=state_b), dep_pr(252, 240, HEAD_A, state=state_a)]


def test_the_base_moves_to_main_when_every_listed_pull_request_is_merged(home: Path) -> None:
    host, log = tick(home, child_pr(), [epic_issue(), task(242, "agent:review")])
    edits = host.gh_calls("pr", "edit", "260")
    assert ["gh", "pr", "edit", "260", "--base", "main", "--repo", agent_tick.REPO] in edits
    assert "pr-260: #251, #252 merged; base is now main" in log


def test_the_base_stays_while_one_listed_pull_request_is_open(home: Path) -> None:
    host, _ = tick(home, child_pr(state_b="OPEN"), [epic_issue(), task(242, "agent:review")])
    assert not any("--base" in c for c in host.gh_calls("pr", "edit", "260"))


def test_a_pull_request_into_the_epic_branch_is_never_merged(home: Path) -> None:
    kid = child_pr(state_b="OPEN")
    kid[0]["comments"] = [
        {
            "author": {"login": agent_tick.OWNER},
            "body": "lgtm",
            "createdAt": "2026-10-21T10:00:00Z",
            "id": "c1",
        }
    ]
    host, _ = tick(home, kid, [epic_issue(), task(242, "agent:review")])
    assert host.gh_calls("pr", "merge") == []


# AC4: a listed pull request closed without merge blocks the child


def test_a_listed_pull_request_closed_without_merge_blocks_the_child(home: Path) -> None:
    host, log = tick(home, child_pr(state_b="CLOSED"), [epic_issue(), task(242, "agent:review")])
    edits = [" ".join(c) for c in host.gh_calls("pr", "edit", "260")]
    assert any("--add-label pr:blocked" in e for e in edits)
    assert "pr-260: PR #251 closed without merge; pr:blocked" in log
