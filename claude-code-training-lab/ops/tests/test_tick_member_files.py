"""#525: an issue a member claimed holds its files in the loop. Run: pytest ops"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import issue, started
from ops.tests.test_tick_hardening import GitHost
from ops.tests.test_tick_member_assignment import (
    README,
    epic_with,
    host_of,
    logins,
    make_tick,
)
from ops.tests.test_tick_stacked import child, parent_pr, prompt

VIEWS = "reviews/views.py"
RELEASE = "ops/release.py"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=3\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def files(*paths: str) -> str:
    return "## Files likely touched\n\n" + "\n".join(f"- `{p}`" for p in paths) + "\n\n## Notes\n"


def item(
    number: int,
    *labels: str,
    paths: tuple[str, ...] = (VIEWS,),
    members: tuple[str, ...] = (),
    epic: int = 0,
) -> dict[str, Any]:
    """An open issue; `members` become its assignees, `paths` its Files likely touched."""
    part = f"Part of the epic #{epic}\n\n" if epic else ""
    found = issue(number, *labels, body=part + (files(*paths) if paths else "No files.\n"))
    if members:
        found["assignees"] = logins(*members)
    return found


def ready(number: int, *paths: str) -> dict[str, Any]:
    return item(number, "agent:ready", paths=paths or (VIEWS,))


def waits(tick: agent_tick.Tick) -> tuple[list[str], list[str]]:
    """The keys choose() starts, then the `waits` log lines it wrote."""
    keys = [t.key for t in agent_tick.choose(tick, [], {})]
    return keys, [line for line in tick.log if " waits for " in line]


def blocked(tick: agent_tick.Tick) -> tuple[int, list[str]]:
    return agent_tick.blocked_lines(tick, [], {}, set())


LOG_509 = f"issue-512: waits for #509 (member alice), which also touches {VIEWS}"
LINE_509 = f"#512 waits for #509 (member alice), which also touches {VIEWS}"


# M1 / AC1: a member's issue holds its files, whatever its labels


def test_ready_issue_does_not_start_while_a_member_issue_holds_its_file(home: Path) -> None:
    tick = make_tick(home, [item(509, members=("alice",)), ready(512)])
    keys, lines = waits(tick)
    assert keys == []
    assert LOG_509 in tick.log
    assert lines == [LOG_509]


def test_file_hold_of_a_member_issue_is_logged_once_and_starts_nothing_else(home: Path) -> None:
    other = ready(513, "reviews/forms.py")
    tick = make_tick(home, [item(509, members=("alice",)), ready(512), other])
    keys, _ = waits(tick)
    assert keys == ["issue-513"]
    assert LOG_509 in tick.log


def test_member_issue_holds_a_file_whatever_the_path_prefix(home: Path) -> None:
    held = item(509, paths=(f"claude-code-training-lab/{VIEWS}",), members=("alice",))
    tick = make_tick(home, [held, ready(512)])
    keys, _ = waits(tick)
    assert keys == []
    assert LOG_509 in tick.log


# M2 / AC1: the labels of the member issue do not matter


@pytest.mark.parametrize(
    "label", ["agent:ready", "agent:failed", "agent:in-epic", "agent:manual", "bug"]
)
def test_member_issue_with_any_label_still_holds_its_file(home: Path, label: str) -> None:
    tick = make_tick(home, [item(509, label, members=("alice",)), ready(512)])
    keys, _ = waits(tick)
    assert keys == []
    assert LOG_509 in tick.log


# M3 / AC2: blocked_lines


def test_blocked_lines_counts_the_issue_waiting_on_a_member_issue(home: Path) -> None:
    tick = make_tick(home, [item(509, members=("alice",)), ready(512)])
    assert blocked(tick) == (1, [LINE_509])


def test_blocked_lines_counts_it_for_a_member_issue_with_any_label(home: Path) -> None:
    tick = make_tick(home, [item(509, "agent:ready", members=("alice",)), ready(512)])
    assert blocked(tick) == (1, [LINE_509])


# M4 / AC3: the member of the epic


def epic_case(task_member: tuple[str, ...]) -> list[dict[str, Any]]:
    task = item(601, paths=(RELEASE,), members=task_member, epic=600)
    return [epic_with("bob"), task, ready(605, RELEASE)]


def test_task_of_a_member_epic_holds_its_file_and_names_the_epic(home: Path) -> None:
    tick = make_tick(home, epic_case(()))
    keys, _ = waits(tick)
    assert keys == []
    line = "issue-605: waits for #601 (member bob, epic #600), which also touches ops/release.py"
    assert line in tick.log
    assert blocked(tick) == (
        1,
        ["#605 waits for #601 (member bob, epic #600), which also touches ops/release.py"],
    )


def test_task_own_member_wins_over_the_epics_member_in_the_wait_lines(home: Path) -> None:
    tick = make_tick(home, epic_case(("carol",)))
    keys, _ = waits(tick)
    assert keys == []
    assert "issue-605: waits for #601 (member carol), which also touches ops/release.py" in tick.log
    assert blocked(tick) == (
        1,
        ["#605 waits for #601 (member carol), which also touches ops/release.py"],
    )
    assert not any("bob" in line for line in tick.log)


# M5 / AC4: the member leaves, or the issue leaves the list


def test_issue_starts_when_the_member_is_removed_from_the_holder(home: Path) -> None:
    holder = item(509, members=("alice",))
    assert waits(make_tick(home, [holder, ready(512)]))[0] == []
    holder["assignees"] = []
    keys, lines = waits(make_tick(home, [holder, ready(512)]))
    assert keys == ["issue-512"]
    assert lines == []


def test_issue_starts_when_the_holder_is_not_in_the_open_list(home: Path) -> None:
    keys, lines = waits(make_tick(home, [ready(512)]))
    assert keys == ["issue-512"]
    assert lines == []


def test_issue_starts_when_the_epics_member_is_removed(home: Path) -> None:
    issues = epic_case(())
    assert waits(make_tick(home, issues))[0] == []
    issues[0]["assignees"] = []
    keys, _ = waits(make_tick(home, issues))
    assert keys == ["issue-605"]


def test_blocked_lines_is_empty_once_the_member_is_removed(home: Path) -> None:
    holder = item(509, members=("alice",))
    holder["assignees"] = []
    assert blocked(make_tick(home, [holder, ready(512)])) == (0, [])


# M6 / AC5: who holds a path


@pytest.mark.parametrize("label", ["agent:running", "agent:review"])
@pytest.mark.parametrize("runner_members", [(), ("alice",)], ids=["no-member", "runner-member"])
def test_running_or_review_issue_keeps_the_line_without_a_member(
    home: Path, label: str, runner_members: tuple[str, ...]
) -> None:
    issues = [
        item(509, members=("bob",)),
        item(520, label, members=runner_members),
        ready(512),
    ]
    tick = make_tick(home, issues)
    keys, lines = waits(tick)
    assert keys == []
    assert lines == [f"issue-512: waits for #520, which also touches {VIEWS}"]
    assert blocked(tick) == (1, [f"#512 waits for #520, which also touches {VIEWS}"])


def test_issue_chosen_earlier_in_the_tick_keeps_the_line_of_main_over_a_member(
    home: Path,
) -> None:
    parent = item(4, paths=("ops/x.py",), members=("alice",))
    host = GitHost(prs=[parent_pr()], issues=[parent, child(), ready(7, "ops/x.py")])
    tick = agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env"))
    targets = agent_tick.choose(tick, [parent_pr()], {})
    assert [t.key for t in targets] == ["issue-5"]  # stacked on the member's parent, so it starts
    assert [line for line in tick.log if " waits for " in line] == [
        "issue-7: waits for #5, which also touches ops/x.py"
    ]


def test_the_lowest_numbered_member_issue_holds_the_path(home: Path) -> None:
    issues = [item(510, members=("bob",)), item(509, members=("alice",)), ready(512)]
    tick = make_tick(home, issues)
    keys, lines = waits(tick)
    assert keys == []
    assert lines == [LOG_509]
    assert blocked(tick) == (1, [LINE_509])


def test_the_lowest_member_issue_holds_the_path_through_an_epic_member(home: Path) -> None:
    issues = [epic_with("bob"), item(601, epic=600), item(610, members=("alice",)), ready(612)]
    tick = make_tick(home, issues)
    _, lines = waits(tick)
    assert lines == [
        f"issue-612: waits for #601 (member bob, epic #600), which also touches {VIEWS}"
    ]


def test_path_held_by_an_issue_chosen_earlier_keeps_the_line_of_main(home: Path) -> None:
    tick = make_tick(home, [item(509, members=("alice",)), ready(512)])
    member = agent_tick.member_holds(tick, agent_tick.open_issue_list(tick))
    busy = {VIEWS: 505}  # chosen earlier in this tick, so it is in the busy map
    holder = agent_tick.path_holder(busy, {VIEWS: {505}}, member, VIEWS, set())
    assert holder == (505, "")
    assert agent_tick.path_holder({}, {}, member, VIEWS, set()) == (509, " (member alice)")


def test_member_issues_with_other_paths_do_not_hold_this_one(home: Path) -> None:
    issues = [item(509, paths=("reviews/forms.py",), members=("alice",)), ready(512)]
    keys, lines = waits(make_tick(home, issues))
    assert keys == ["issue-512"]
    assert lines == []


@pytest.mark.parametrize("parent_labels", [("agent:review",), ()], ids=["review", "no-label"])
def test_stacked_parent_member_issue_is_ignored(home: Path, parent_labels: tuple[str, ...]) -> None:
    parent = item(4, *parent_labels, paths=("ops/x.py",), members=("alice",))
    host = GitHost(prs=[parent_pr()], issues=[parent, child()])
    agent_tick.tick_once(host, home)
    assert started(host) == [prompt()]


def test_epic_parent_member_issue_is_ignored(home: Path) -> None:
    done = item(601, "agent:in-epic", paths=("ops/x.py",), members=("alice",), epic=600)
    nxt = item(603, "agent:ready", paths=("ops/x.py",), epic=600)
    nxt["body"] += "Depends on #601\n"
    host = GitHost(issues=[epic_with(), done, nxt])
    host.git = {"--quiet refs/remotes/origin/": (0, "abc1234\n")}
    tick = agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env"))
    targets = agent_tick.choose(tick, [], {})
    assert [t.key for t in targets] == ["issue-603"]
    assert not any("waits for #601" in line for line in tick.log)


def test_epic_parent_member_issue_still_holds_the_path_for_an_unrelated_issue(
    home: Path,
) -> None:
    done = item(601, "agent:in-epic", paths=("ops/x.py",), members=("alice",), epic=600)
    other = ready(612, "ops/x.py")
    tick = make_tick(home, [epic_with(), done, other])
    keys, _ = waits(tick)
    assert keys == []
    assert "issue-612: waits for #601 (member alice), which also touches ops/x.py" in tick.log


# M7 / AC6: a member issue without paths holds nothing; it is still skipped


def test_member_issue_without_paths_does_not_hold_anything(home: Path) -> None:
    quiet = item(509, "agent:ready", paths=(), members=("alice",))
    tick = make_tick(home, [quiet, ready(512)])
    keys, lines = waits(tick)
    assert keys == ["issue-512"]
    assert lines == []
    assert "issue-509: assigned to alice; skipped" in tick.log
    assert blocked(tick) == (0, [])


def test_member_issue_is_skipped_and_never_waits_for_its_own_files(home: Path) -> None:
    issues = [item(520, "agent:running"), item(509, "agent:ready", members=("alice",))]
    tick = make_tick(home, issues)
    keys, lines = waits(tick)
    assert keys == []
    assert "issue-509: assigned to alice; skipped" in tick.log
    assert lines == []
    assert blocked(tick) == (0, [])


def test_two_member_issues_on_one_path_are_skipped_not_waiting(home: Path) -> None:
    issues = [
        item(509, "agent:ready", members=("alice",)),
        item(510, "agent:ready", members=("bob",)),
    ]
    tick = make_tick(home, issues)
    keys, lines = waits(tick)
    assert keys == []
    assert lines == []
    assert "issue-509: assigned to alice; skipped" in tick.log
    assert "issue-510: assigned to bob; skipped" in tick.log


def test_epic_issue_holds_only_the_paths_of_its_own_body(home: Path) -> None:
    epic = epic_with("bob")
    epic["body"] = files(RELEASE)
    task = item(601, paths=("ops/other.py",), epic=600)
    tick = make_tick(home, [epic, task, ready(605, RELEASE), ready(606, "ops/other.py")])
    keys, lines = waits(tick)
    assert keys == []
    assert lines == [
        f"issue-605: waits for #600 (member bob), which also touches {RELEASE}",
        "issue-606: waits for #601 (member bob, epic #600), which also touches ops/other.py",
    ]


def test_epic_issue_without_paths_in_its_body_holds_nothing(home: Path) -> None:
    task = item(601, paths=(), epic=600)
    tick = make_tick(home, [epic_with("bob"), task, ready(605, RELEASE)])
    keys, lines = waits(tick)
    assert keys == ["issue-605"]
    assert lines == []


# M8 / AC6: no member anywhere, as on main


def test_without_members_issues_start_and_log_as_on_main(home: Path) -> None:
    issues = [ready(1, "reviews/services.py", "reviews/a.py"), ready(2, "reviews/services.py")]
    issues.append(ready(3, VIEWS))
    tick = make_tick(home, issues)
    keys, lines = waits(tick)
    assert keys == ["issue-1", "issue-3"]
    assert lines == ["issue-2: waits for #1, which also touches reviews/services.py"]
    assert not any("member" in line for line in tick.log)


def test_without_members_blocked_lines_are_as_on_main(home: Path) -> None:
    issues = [item(5, "agent:review"), ready(6)]
    tick = make_tick(home, issues)
    assert blocked(tick) == (1, [f"#6 waits for #5, which also touches {VIEWS}"])


def test_owner_only_assignee_holds_no_member_line(home: Path) -> None:
    mine = item(509, members=())
    mine["assignees"] = logins(agent_tick.OWNER)
    tick = make_tick(home, [mine, ready(512)])
    keys, lines = waits(tick)
    assert keys == ["issue-512"]
    assert lines == []


# M9 / AC7: no extra gh call


def run_tick(home: Path, tag: str, issues: list[dict[str, Any]]) -> GitHost:
    folder = home / tag
    folder.mkdir()
    (folder / "agent.env").write_text("AGENT_CONCURRENCY=3\nNTFY_TOPIC=rr-test\n")
    host = GitHost(issues=issues, git={"branch --show-current": (0, "main\n")})
    agent_tick.tick_once(host, folder)
    return host


def test_member_hold_makes_the_same_gh_calls_as_a_running_hold(home: Path) -> None:
    with_member = run_tick(home, "member", [item(509, members=("alice",)), ready(512)])
    running = run_tick(home, "running", [item(509, "agent:running"), ready(512)])
    assert with_member.spawned == [] and running.spawned == []
    assert with_member.gh_calls() == running.gh_calls()


def test_member_hold_reads_one_issue_list_and_views_no_issue(home: Path) -> None:
    tick = make_tick(home, [item(509, members=("alice",)), ready(512)])
    waits(tick)
    blocked(tick)
    host = host_of(tick)
    assert len(host.gh_calls("issue", "list")) == 1
    assert host.gh_calls("issue", "view") == []
    assert LOG_509 in tick.log


def test_member_hold_calls_match_with_the_choose_and_blocked_lines_only(home: Path) -> None:
    member = make_tick(home, [item(509, members=("alice",)), ready(512)])
    running = make_tick(home, [item(509, "agent:running"), ready(512)])
    for tick in (member, running):
        waits(tick)
        blocked(tick)
    assert host_of(member).gh_calls() == host_of(running).gh_calls()


# M10 / AC8: the README


def section(heading: str) -> str:
    return README.read_text().split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]


def test_readme_guards_names_the_member_hold_and_its_log_line() -> None:
    text = section("Guards")
    assert "issue-<n>: waits for #<m> (member <login>), which also touches <path>" in text
    assert "has a member" in text
    assert "on the issue or its epic" in text
    assert "any label" in text
    assert "issue-<n>: waits for #<m>, which also touches <path>" in text


def test_readme_team_members_says_a_claim_holds_the_files_of_the_issue() -> None:
    text = section("Team members")
    assert "`## Files likely touched`" in text
    assert "until it is closed or the member is removed" in text
    assert "list them before claiming" in text
