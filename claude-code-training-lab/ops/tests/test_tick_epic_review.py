"""#495: the tick starts one epic review on a green epic pull request. Run: pytest ops/tests"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import add_run, started
from ops.tests.test_epic_pull_request import (
    BRANCH,
    NEW_PR,
    RED,
    Host,
    host_for,
    the_epic_pr,
    two_merged,
)
from ops.tests.test_epic_pull_request import home as home  # fixture, re-exported for pytest
from ops.tests.test_tick_merge import remark

REVIEW_PROMPT = f"Use the work-queue skill for pull request #{NEW_PR} only: epic review."
NORMAL_PROMPT = f"Use the work-queue skill for pull request #{NEW_PR} only."
REVIEW_BODY = f"{MARKER}\n<!-- epic-review -->\n## Epic review\n\nNo findings."
RUNNING = [{"status": "IN_PROGRESS", "conclusion": ""}]


class HeadHost(Host):
    """Host that answers `git rev-parse HEAD` of a worktree, as a real checkout does."""

    def run(self, args: Any, cwd: Path | None = None) -> tuple[int, str]:
        if list(args)[3:] == ["rev-parse", "HEAD"]:
            self.calls.append(list(args))
            return 0, "fff0001\n"
        return super().run(args, cwd)


def head_host_for(*prs: dict[str, Any]) -> HeadHost:
    """Like host_for, with a git that knows its HEAD, so a round file can be written."""
    host = HeadHost(branches={BRANCH})
    plain = host_for(*prs)
    host.prs = plain.prs
    host.issues = plain.issues
    return host


def tick(host: Host, home: Path) -> list[str]:
    return agent_tick.tick_once(host, home)


def review_comment() -> dict[str, Any]:
    return remark(7, REVIEW_BODY)


def round_file(home: Path) -> Path:
    return home / "worktrees" / f"pr-{NEW_PR}" / agent_tick.APP_DIR / "out" / "pr-round.json"


def count_file(home: Path) -> Path:
    return home / f"epic-review-{NEW_PR}"


def told_file(home: Path) -> Path:
    return home / f"epic-review-{NEW_PR}-told"


def ready_labels(host: Host) -> list[list[str]]:
    return [c for c in host.gh_calls("pr", "edit", str(NEW_PR)) if "pr:ready-for-review" in c]


def unfinished_notes(host: Host) -> list[str]:
    return [m for m in host.sent if "the epic review did not finish" in m]


def unfinished_text() -> str:
    return (
        f"rr-test: {agent_tick.NAME} epic PR #{NEW_PR}: the epic review did not finish; "
        f"review it without it: https://github.com/{agent_tick.REPO}/pull/{NEW_PR}"
    )


def run_going(host: Host, home: Path) -> None:
    add_run(home, f"pr-{NEW_PR}", 4242)
    host.alive_pids.add(4242)


# M13: a green, open epic pull request with no review comment is reviewed


def test_m13_a_green_epic_pull_request_without_comment_starts_an_epic_review(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert started(host) == [REVIEW_PROMPT]


def test_m13_the_run_is_on_the_epic_branch(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert any(c[3:6] == ["worktree", "add", "-B"] and BRANCH in c for c in host.calls)


def test_m13_the_start_message_says_reviewing_epic_pr(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert f"rr-test: {agent_tick.NAME} reviewing epic PR #{NEW_PR}" in host.sent


def test_m13_reviewing_epic_message_has_low_priority() -> None:
    assert agent_tick.message_priority(f"{agent_tick.NAME} reviewing epic PR #{NEW_PR}") == "low"
    assert agent_tick.message_priority(f"{agent_tick.NAME} working on PR #{NEW_PR} (CI)") == "low"


# M14: when it is not started for review


@pytest.mark.parametrize(
    "build",
    [
        lambda: the_epic_pr(review_comment(), labels=()),
        lambda: the_epic_pr(labels=(), checks=RED),
        lambda: the_epic_pr(labels=(), checks=RUNNING),
        lambda: the_epic_pr(labels=(), checks=[]),
        lambda: the_epic_pr(labels=("pr:ready-for-review",)),
        lambda: the_epic_pr(labels=("pr:blocked",)),
        lambda: the_epic_pr(labels=("pr:changes-requested",)),
        lambda: the_epic_pr(labels=("pr:ci-failed",)),
    ],
    ids=[
        "comment",
        "red-check",
        "running-check",
        "no-check",
        "ready-label",
        "blocked-label",
        "changes-label",
        "ci-failed-label",
    ],
)
def test_m14_it_is_not_started_for_review(home: Path, build: Callable[[], dict[str, Any]]) -> None:
    host = host_for(*two_merged(), build())
    tick(host, home)
    assert REVIEW_PROMPT not in started(host)


def test_m14_a_comment_of_someone_else_does_not_count_as_the_epic_review(home: Path) -> None:
    other = remark(7, REVIEW_BODY, login="someone-else")
    host = host_for(*two_merged(), the_epic_pr(other, labels=()))
    tick(host, home)
    assert REVIEW_PROMPT in started(host)


def test_m14_an_open_change_request_gets_the_normal_prompt(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(remark(1, "rename the heading"), labels=()))
    tick(host, home)
    assert started(host) == [NORMAL_PROMPT]


def test_m14_a_running_pull_request_is_not_started_again(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    run_going(host, home)
    tick(host, home)
    assert started(host) == []


# M14b: the round file


def test_m14b_an_epic_review_run_writes_no_round_file(home: Path) -> None:
    host = head_host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert started(host) == [REVIEW_PROMPT]
    assert not round_file(home).exists()


def test_m14b_an_epic_review_run_removes_an_old_round_file(home: Path) -> None:
    round_file(home).parent.mkdir(parents=True)
    round_file(home).write_text(json.dumps({"head": "old", "pr": NEW_PR}))
    host = head_host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert started(host) == [REVIEW_PROMPT]
    assert not round_file(home).exists()


def test_m14b_a_change_request_run_on_the_same_pull_request_writes_it(home: Path) -> None:
    host = head_host_for(*two_merged(), the_epic_pr(remark(1, "rename the heading")))
    tick(host, home)
    assert started(host) == [NORMAL_PROMPT]
    assert json.loads(round_file(home).read_text())["pr"] == NEW_PR


# M15: mark_green_ready waits for the epic review comment


def test_m15_it_stays_unlabelled_without_the_comment(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    run_going(host, home)
    count_file(home).write_text("1")
    tick(host, home)
    assert ready_labels(host) == []


def test_m15_it_is_labelled_ready_once_the_comment_exists(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(review_comment(), labels=()))
    tick(host, home)
    assert ready_labels(host) != []


def test_m15_the_tick_that_starts_the_review_does_not_label(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert ready_labels(host) == []


# M16: two runs ended without the comment


def test_m16_after_two_runs_no_run_starts_and_it_is_labelled_ready(home: Path) -> None:
    count_file(home).write_text("2")
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert started(host) == []
    assert ready_labels(host) != []


def test_m16_the_owner_is_told_once_over_two_ticks(home: Path) -> None:
    count_file(home).write_text("2")
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    tick(host, home)
    assert unfinished_notes(host) == [unfinished_text()]
    assert told_file(home).exists()


def test_m16_the_owner_is_told_even_when_the_checks_are_red(home: Path) -> None:
    count_file(home).write_text("2")
    host = host_for(*two_merged(), the_epic_pr(labels=(), checks=RED))
    tick(host, home)
    assert unfinished_notes(host) == [unfinished_text()]
    assert ready_labels(host) == []


def test_m16_nothing_is_said_while_the_second_run_is_going(home: Path) -> None:
    count_file(home).write_text("2")
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    run_going(host, home)
    tick(host, home)
    assert unfinished_notes(host) == []


def test_m16_nothing_is_said_when_the_comment_exists(home: Path) -> None:
    count_file(home).write_text("2")
    host = host_for(*two_merged(), the_epic_pr(review_comment(), labels=()))
    tick(host, home)
    assert unfinished_notes(host) == []


# AC4: the count of started runs


def test_ac4_a_started_review_adds_one_to_the_count(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert count_file(home).read_text().strip() == "1"


def test_ac4_a_second_run_makes_the_count_two_and_tells_nothing_yet(home: Path) -> None:
    count_file(home).write_text("1")
    host = host_for(*two_merged(), the_epic_pr(labels=()))
    tick(host, home)
    assert started(host) == [REVIEW_PROMPT]
    assert count_file(home).read_text().strip() == "2"
    assert unfinished_notes(host) == []


def test_ac4_a_start_that_fails_does_not_count(home: Path) -> None:
    host = host_for(*two_merged(), the_epic_pr(labels=()), fail="worktree add")
    tick(host, home)
    assert started(host) == []
    assert not count_file(home).exists()
