"""#478: the loop leaves alone what is assigned to a team member. Run: pytest ops"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER, NAME, OWNER, REPO
from ops.tests.test_agent_tick import issue
from ops.tests.test_epic_branch import EpicHost, epic_issue
from ops.tests.test_tick_hardening import GitHost

BRANCH = "epic/600-reply-to-reviews"
README = Path(__file__).resolve().parents[1] / "README.md"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def logins(*names: str) -> list[dict[str, str]]:
    return [{"login": name} for name in names]


def member_issue(
    number: int, *labels: str, assignees: list[str] | None = None, epic: int = 0
) -> dict[str, Any]:
    body = f"Part of the epic #{epic}\n" if epic else "Do it.\n"
    item = issue(number, *labels, body=body)
    if assignees is not None:
        item["assignees"] = logins(*assignees)
    return item


def epic_with(*assignees: str, number: int = 600) -> dict[str, Any]:
    item = epic_issue(number, "Epic: reply to reviews")
    item["assignees"] = logins(*assignees)
    return item


def make_tick(home: Path, issues: list[dict[str, Any]]) -> agent_tick.Tick:
    return agent_tick.Tick(
        host=GitHost(issues=issues),
        home=home,
        settings=agent_tick.read_settings(home / "agent.env"),
    )


def host_of(tick: agent_tick.Tick) -> GitHost:
    assert isinstance(tick.host, GitHost)
    return tick.host


def member_of(tick: agent_tick.Tick, item: dict[str, Any]) -> tuple[str, int | None] | None:
    found: tuple[str, int | None] | None = agent_tick.member_of(  # type: ignore[attr-defined,unused-ignore]
        tick, item
    )
    return found


def chosen_keys(tick: agent_tick.Tick) -> list[str]:
    return [t.key for t in agent_tick.choose(tick, [], {})]


def edits(host: GitHost) -> list[list[str]]:
    return host.gh_calls("issue", "edit")


# M1 / AC1: the issue list asks for assignees; member_of


def test_issue_list_asks_for_assignees_in_one_call(home: Path) -> None:
    tick = make_tick(home, [member_issue(500, "agent:ready")])
    agent_tick.open_issue_list(tick)
    agent_tick.open_issue_list(tick)
    lists = host_of(tick).gh_calls("issue", "list")
    assert len(lists) == 1
    fields = lists[0][lists[0].index("--json") + 1].split(",")
    assert "assignees" in fields


def test_member_of_gives_the_first_member_in_sorted_order(home: Path) -> None:
    item = member_issue(500, "agent:ready", assignees=["zed", OWNER, "bob", "carol"])
    tick = make_tick(home, [item])
    assert member_of(tick, item) == ("bob", None)


def test_member_of_gives_the_epics_first_member_with_the_epic_number(home: Path) -> None:
    item = member_issue(601, "agent:ready", assignees=[OWNER], epic=600)
    tick = make_tick(home, [epic_with("carol", "alice"), item])
    assert member_of(tick, item) == ("alice", 600)


def test_member_of_prefers_the_issues_own_member_over_the_epics(home: Path) -> None:
    item = member_issue(602, "agent:ready", assignees=["bob"], epic=600)
    tick = make_tick(home, [epic_with("alice"), item])
    assert member_of(tick, item) == ("bob", None)


def test_member_of_is_none_without_a_member_on_the_issue_or_its_epic(home: Path) -> None:
    item = member_issue(601, "agent:ready", assignees=[OWNER], epic=600)
    tick = make_tick(home, [epic_with(OWNER), item])
    assert member_of(tick, item) is None


def test_member_of_counts_an_issue_without_assignees_key_as_having_none(home: Path) -> None:
    item = member_issue(500, "agent:ready")
    assert "assignees" not in item
    tick = make_tick(home, [item])
    assert member_of(tick, item) is None


def test_member_of_ignores_an_epic_that_is_not_labelled_epic(home: Path) -> None:
    not_epic = epic_with("alice") | {"labels": []}
    item = member_issue(601, "agent:ready", epic=600)
    tick = make_tick(home, [not_epic, item])
    assert member_of(tick, item) is None


def test_member_of_ignores_an_epic_that_is_not_open(home: Path) -> None:
    item = member_issue(601, "agent:ready", epic=600)
    tick = make_tick(home, [item])
    assert member_of(tick, item) is None


# M2 / AC2: an issue assigned to a member is skipped


def test_issue_assigned_to_a_member_is_not_chosen_and_logged(home: Path) -> None:
    tick = make_tick(home, [member_issue(500, "agent:ready", assignees=["alice"])])
    assert chosen_keys(tick) == []
    assert "issue-500: assigned to alice; skipped" in tick.log


def test_issue_assigned_to_a_member_and_the_owner_is_skipped(home: Path) -> None:
    tick = make_tick(home, [member_issue(500, "agent:ready", assignees=[OWNER, "alice"])])
    assert chosen_keys(tick) == []
    assert "issue-500: assigned to alice; skipped" in tick.log


# M3 / AC2: owner only, or nobody, is as on main


@pytest.mark.parametrize("assignees", [[OWNER], [], None])
def test_issue_assigned_to_the_owner_or_nobody_is_chosen(
    home: Path, assignees: list[str] | None
) -> None:
    tick = make_tick(home, [member_issue(500, "agent:ready", assignees=assignees)])
    assert chosen_keys(tick) == ["issue-500"]
    assert not any("assigned to" in line for line in tick.log)


# M4 / AC3: the epic's member


def test_task_of_an_epic_assigned_to_a_member_is_skipped_with_the_epic_number(
    home: Path,
) -> None:
    issues = [epic_with("alice"), member_issue(601, "agent:ready", assignees=[OWNER], epic=600)]
    tick = make_tick(home, issues)
    assert chosen_keys(tick) == []
    assert "issue-601: assigned to alice (epic #600); skipped" in tick.log


# M5 / AC3: the task's own member wins


def test_task_member_wins_over_the_epics_member(home: Path) -> None:
    issues = [epic_with("alice"), member_issue(602, "agent:ready", assignees=["bob"], epic=600)]
    tick = make_tick(home, issues)
    assert chosen_keys(tick) == []
    assert "issue-602: assigned to bob; skipped" in tick.log
    assert not any("alice" in line for line in tick.log)


# M6 / AC4: the member leaves, the loop takes it at the next choose


def test_issue_is_chosen_again_when_the_member_is_removed_and_no_label_changes(
    home: Path,
) -> None:
    item = member_issue(500, "agent:ready", assignees=["alice"])
    first = make_tick(home, [item])
    assert chosen_keys(first) == []
    item["assignees"] = []
    second = make_tick(home, [item])
    assert chosen_keys(second) == ["issue-500"]
    assert edits(host_of(first)) == [] and edits(host_of(second)) == []


def test_task_is_chosen_again_when_the_epics_member_is_removed(home: Path) -> None:
    issues = [epic_with("alice"), member_issue(601, "agent:ready", epic=600)]
    assert chosen_keys(make_tick(home, issues)) == []
    issues[0]["assignees"] = []
    assert chosen_keys(make_tick(home, issues)) == ["issue-601"]


# M7 / AC5: a build the loop runs goes on, the member is told once


def claimed(home: Path, assignees: list[str], *labels: str, epic: int = 0) -> GitHost:
    issues = [member_issue(500, *labels, assignees=assignees, epic=epic)]
    if epic:
        issues.insert(0, epic_with("alice"))
    return GitHost(issues=issues, git={"branch --show-current": (0, "main\n")})


NOTICE = f"{NAME} #500 is assigned to alice while the loop builds it: https://github.com/{REPO}/issues/500"
LINE = "issue-500: assigned to alice while the loop builds it; the build goes on"


@pytest.mark.parametrize("label", ["agent:running", "agent:review"])
def test_member_on_a_running_build_is_logged_and_notified_once(home: Path, label: str) -> None:
    host = claimed(home, ["alice"], label)
    log = agent_tick.tick_once(host, home)
    assert LINE in log
    assert host.sent.count(f"rr-test: {NOTICE}") == 1
    assert (home / "member-claims").read_text().splitlines() == ["500 alice"]
    again = agent_tick.tick_once(host, home)
    assert LINE not in again
    assert host.sent.count(f"rr-test: {NOTICE}") == 1
    assert (home / "member-claims").read_text().splitlines() == ["500 alice"]


def test_member_on_a_running_build_changes_no_label_and_adds_no_gh_call(home: Path) -> None:
    with_member = claimed(home, ["alice"], "agent:running")
    without = claimed(home, [], "agent:running")
    agent_tick.tick_once(with_member, home)
    other = home / "other"
    other.mkdir()
    (other / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    agent_tick.tick_once(without, other)
    assert with_member.gh_calls() == without.gh_calls()
    assert edits(with_member) == edits(without)


def test_member_through_the_epic_says_epic_in_log_and_notification(home: Path) -> None:
    host = claimed(home, [OWNER], "agent:running", epic=600)
    log = agent_tick.tick_once(host, home)
    assert (
        "issue-500: assigned to alice (epic #600) while the loop builds it; the build goes on"
        in log
    )
    text = f"{NAME} #500 is assigned to alice (epic #600) while the loop builds it: "
    assert f"rr-test: {text}https://github.com/{REPO}/issues/500" in host.sent
    assert (home / "member-claims").read_text().splitlines() == ["500 alice"]


def test_a_new_member_on_the_same_issue_is_told_again(home: Path) -> None:
    host = claimed(home, ["alice"], "agent:running")
    agent_tick.tick_once(host, home)
    host.issues[0]["assignees"] = logins("bob")
    log = agent_tick.tick_once(host, home)
    assert "issue-500: assigned to bob while the loop builds it; the build goes on" in log
    assert sorted((home / "member-claims").read_text().splitlines()) == ["500 alice", "500 bob"]


def test_owner_only_on_a_running_build_says_nothing(home: Path) -> None:
    host = claimed(home, [OWNER], "agent:running")
    log = agent_tick.tick_once(host, home)
    assert not any("while the loop builds it" in line for line in log)
    assert not (home / "member-claims").exists()


def test_member_claim_is_checked_after_tidy_worktrees_and_before_the_pause(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    order: list[str] = []
    real_tidy = agent_tick.tidy_worktrees

    def tidy(*args: Any) -> None:
        order.append("tidy")
        real_tidy(*args)

    def paused(tick: agent_tick.Tick) -> bool:
        order.append("paused")
        return True

    monkeypatch.setattr(agent_tick, "tidy_worktrees", tidy)
    monkeypatch.setattr(agent_tick, "paused", paused)
    host = claimed(home, ["alice"], "agent:running")
    log = agent_tick.tick_once(host, home)
    assert LINE in log
    assert order == ["tidy", "paused"]
    assert log.index(LINE) < log.index("paused after the plan limit; no build started")


# M8 / AC6: failed and ready issues of a member


def test_member_failed_issue_is_never_retried(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    asked: list[int] = []

    def retry(tick: agent_tick.Tick, item: dict[str, Any], parent: Any = None) -> str:
        asked.append(item["number"])
        return "main moved"

    monkeypatch.setattr(agent_tick, "retry_reason", retry)
    tick = make_tick(home, [member_issue(500, "agent:failed", assignees=["alice"])])
    assert chosen_keys(tick) == []
    assert asked == []
    assert "issue-500: assigned to alice; skipped" in tick.log


def test_member_ready_issue_does_not_stop_queue_empty(home: Path) -> None:
    host = GitHost(issues=[member_issue(500, "agent:ready", assignees=["alice"])])
    tick = agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env"))
    agent_tick.queue_empty(tick, [])
    assert any("queue empty" in line for line in tick.log)
    assert any("queue empty" in m for m in host.sent)


def test_queue_empty_reads_the_issues_with_open_issue_list(home: Path) -> None:
    host = GitHost(issues=[member_issue(500, "agent:ready", assignees=["alice"])])
    tick = agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env"))
    agent_tick.queue_empty(tick, [])
    assert tick.open_issues is not None
    lists = host.gh_calls("issue", "list")
    assert len(lists) == 1
    assert "assignees" in lists[0][lists[0].index("--json") + 1]


def test_member_ready_issue_is_not_listed_by_blocked_lines(home: Path) -> None:
    blocker = member_issue(499, "agent:running")
    item = member_issue(500, "agent:ready", assignees=["alice"])
    item["body"] = "Depends on #499\n"
    tick = make_tick(home, [blocker, item])
    count, lines = agent_tick.blocked_lines(tick, [], {}, set())
    assert (count, lines) == (0, [])


def test_ready_issue_without_member_is_still_listed_by_blocked_lines(home: Path) -> None:
    blocker = member_issue(499, "agent:running")
    item = member_issue(500, "agent:ready")
    item["body"] = "Depends on #499\n"
    tick = make_tick(home, [blocker, item])
    count, lines = agent_tick.blocked_lines(tick, [], {}, set())
    assert count == 1 and lines


# M9 / AC7: a hand merge by a member into the epic branch


def by_hand(
    number: int = 610,
    closes: int = 601,
    state: str = "MERGED",
    marker: bool = False,
    author: str = "alice",
    **extra: Any,
) -> dict[str, Any]:
    body = (MARKER + "\n" if marker else "") + f"Closes #{closes}"
    return {
        "number": number,
        "state": state,
        "body": body,
        "labels": [],
        "headRefName": f"task/{closes}-x",
        "baseRefName": BRANCH,
        "author": {"login": author},
        "isCrossRepository": False,
        "createdAt": "2026-11-10T00:00:00Z",
        "commits": [{"committedDate": "2026-11-10T00:00:00Z"}],
        "comments": [],
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "isDraft": False,
        "mergeStateStatus": "CLEAN",
        "headRefOid": "abc1234def",
        "title": "Task",
    } | extra


def epic_host(*prs: dict[str, Any]) -> EpicHost:
    host = EpicHost(branches={BRANCH})
    host.prs = list(prs)
    host.issues = [
        epic_issue(600, "Epic: reply to reviews"),
        member_issue(601, "agent:review", assignees=["alice"], epic=600),
        member_issue(602, "agent:review", assignees=["alice"], epic=600),
    ]
    return host


def in_epic_edits(host: EpicHost) -> list[list[str]]:
    return [c for c in host.gh_calls("issue", "edit") if "agent:in-epic" in c]


@pytest.mark.parametrize(
    "pr",
    [
        by_hand(),
        by_hand(marker=True, author="alice"),
    ],
    ids=["no-marker", "marker-from-another-login"],
)
def test_hand_merge_of_a_member_pull_request_marks_the_task_in_epic_once(
    home: Path, pr: dict[str, Any]
) -> None:
    host = epic_host(pr)
    log = agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert f"pr-610: merged into {BRANCH}; #601 agent:in-epic" in log
    edit = in_epic_edits(host)
    assert len(edit) == 1
    assert edit[0][3:8] == [
        "601", "--add-label", "agent:in-epic",
        "--remove-label", "agent:review,agent:running,agent:ready",
    ]  # fmt: skip
    assert "610" in (home / "epic-tasks-merged").read_text().split()


def test_hand_merge_of_a_member_pull_request_reads_no_extra_pull_request_list(
    home: Path,
) -> None:
    host = epic_host(by_hand())
    agent_tick.tick_once(host, home)
    every = [c for c in host.gh_calls("pr", "list") if "all" in c]
    assert len(every) == 1


def test_loop_pull_requests_returns_only_loop_pull_requests(home: Path) -> None:
    loop = by_hand(number=611, closes=602, marker=True, author=OWNER)
    tick = agent_tick.Tick(
        epic_host(by_hand(), loop), home, agent_tick.read_settings(home / "agent.env")
    )
    assert [pr["number"] for pr in agent_tick.loop_pull_requests(tick)] == [611]


def test_open_pull_request_of_a_member_into_the_epic_branch_is_never_touched(
    home: Path,
) -> None:
    host = epic_host(by_hand(number=612, closes=602, state="OPEN", labels=[]))
    host.prs[0]["labels"] = [{"name": "pr:ready-for-review"}]
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "merge") == []
    assert host.gh_calls("pr", "comment") == []
    assert host.gh_calls("pr", "edit") == []
    assert host.gh_calls("pr", "update-branch") == []
    assert in_epic_edits(host) == []


def test_closed_unmerged_pull_request_of_a_member_does_not_mark_the_task(home: Path) -> None:
    host = epic_host(by_hand(state="CLOSED"))
    agent_tick.tick_once(host, home)
    assert in_epic_edits(host) == []


# M10 / AC8: regression, passes before the change


def test_task_depending_on_an_in_epic_task_is_chosen_on_the_epic_branch(home: Path) -> None:
    done = member_issue(601, "agent:in-epic", epic=600)
    nxt = member_issue(603, "agent:ready", epic=600)
    nxt["body"] += "Depends on #601\n"
    host = GitHost(issues=[epic_issue(600, "Epic: reply to reviews"), done, nxt])
    host.git = {"--quiet refs/remotes/origin/": (0, "abc1234\n")}
    tick = agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env"))
    targets = agent_tick.choose(tick, [], {})
    assert [t.key for t in targets] == ["issue-603"]
    assert targets[0].stack_branch == BRANCH


# M11 / AC9: the README section


def test_readme_has_team_members_right_after_the_epic_pull_request() -> None:
    text = README.read_text()
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    after = headings.index("## The epic pull request") + 1
    assert headings[after] == "## Team members"


def test_readme_team_members_has_the_three_gh_issue_edit_commands() -> None:
    text = README.read_text()
    section = text.split("\n## Team members\n", 1)[1].split("\n## ", 1)[0]
    assert "gh issue edit <n> --add-assignee @me" in section
    assert "gh issue edit <n> --remove-assignee @me" in section
    assert "gh issue edit <n> --remove-assignee @me --add-assignee <login>" in section


def test_readme_team_members_explains_the_branch_and_the_running_warning() -> None:
    text = README.read_text()
    section = text.split("\n## Team members\n", 1)[1].split("\n## ", 1)[0]
    assert "agent:running" in section and "agent:review" in section
    assert "<kind>/<n>-<short-description>" in section
    assert "epic/<N>-<slug>" in section
    assert "git push origin origin/main:refs/heads/epic/<N>-<slug>" in section


def test_readme_epic_branch_allows_a_member_to_create_the_branch() -> None:
    text = README.read_text()
    section = text.split("## The epic branch", 1)[1].split("\n## ", 1)[0]
    assert "Only the tick pushes `epic/*` or deletes it, except that a member creates" in section
    assert "(`## Team members`)" in section
