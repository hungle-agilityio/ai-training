"""#530: the epic pull request carries a review checklist right after its task table."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from ops import epic_pull_request
from ops.agent_tick import MARKER
from ops.tests.test_epic_pull_request import (
    BRANCH,
    LINK,
    home,
    host_for,
    merged_task,
    tick,
    two_merged,
)

__all__ = ["home"]  # the fixture comes from the epic pull request tests

HEADING = "## Review checklist"
BOXES = [
    "- [ ] Every task meets its ACs (open each verify report in the table above)",
    "- [ ] Guard files changed: each listed file is expected",
    "- [ ] Query budget: each page of the epic stays within the `## Query budget` "
    "of its `tasks.md`",
    "- [ ] Self-decided fixes: each fix is acceptable",
]
CHECKLIST = HEADING + "\n\n" + "\n".join(BOXES)
FIRST_OFF = BOXES[0]
FIRST_ON = FIRST_OFF.replace("- [ ]", "- [x]", 1)
TICKED = CHECKLIST.replace(FIRST_OFF, FIRST_ON, 1)
HEAD = (
    f"{MARKER}\n\n| Task | Pull request | Verify report |\n|---|---|---|\n| #5 | #20 | {LINK}5 |\n"
)
OTHERS = (
    "## Tests changed by the tasks\n\n- `ops/tests/test_a.py` (M)\n\n"
    "## Self-decided fixes\n\nNone.\n\n"
    "## Guard files changed\n\nNone.\n\n"
)
TAIL = "Closes #5\nCloses #600\n"

Rewrite = Callable[[str], str]

REWRITES: dict[str, Rewrite] = {
    "with_line": lambda body: epic_pull_request.with_line(body, 600, 7),
    "with_changes": lambda body: epic_pull_request.with_changes(
        body, ["- `ops/tests/test_b.py` (M)"]
    ),
    "with_self_fixes": lambda body: epic_pull_request.with_self_fixes(body, ["- #5: https://u/1"]),
    "with_guard_section": lambda body: epic_pull_request.with_guard_section(body, ["ops/x.py"]),
}


def checklist_body(checklist: str) -> str:
    return f"{HEAD}\n{checklist}\n\n{OTHERS}{TAIL}"


# M1 (AC1): body_for puts the section after the table and before the other sections


def test_body_for_puts_the_checklist_right_after_the_task_table() -> None:
    body = epic_pull_request.body_for(
        MARKER, 9, BRANCH, [5], [merged_task(20, 5)], ["- `ops/tests/test_a.py` (M)"], ["x.py"], []
    )
    assert f"{HEAD}\n{CHECKLIST}\n\n## " in body


def test_the_checklist_comes_before_every_other_section() -> None:
    body = epic_pull_request.body_for(
        MARKER, 9, BRANCH, [5], [merged_task(20, 5)], ["- `ops/tests/test_a.py` (M)"], ["x.py"], []
    )
    at = body.index(HEADING)
    for other in (
        "## Tests changed by the tasks",
        "## Self-decided fixes",
        "## Guard files changed",
    ):
        assert at < body.index(other)
    assert body.count(HEADING) == 1


def test_the_checklist_stands_before_the_closes_lines_when_no_other_section() -> None:
    body = epic_pull_request.body_for(MARKER, 9, BRANCH, [5], [merged_task(20, 5)], [])
    assert f"{HEAD}\n{CHECKLIST}\n" in body
    assert body.index(HEADING) < body.index("Closes #5")


# M2 (AC2): a ticked box stays ticked, in the same place, after each rewrite


@pytest.mark.parametrize("name", list(REWRITES))
def test_a_ticked_box_stays_ticked_after_a_rewrite(name: str) -> None:
    after = REWRITES[name](checklist_body(TICKED))
    assert TICKED in after
    assert after.count(HEADING) == 1


@pytest.mark.parametrize("name", list(REWRITES))
def test_the_checklist_stays_directly_after_the_task_table_after_a_rewrite(name: str) -> None:
    after = REWRITES[name](checklist_body(TICKED))
    assert after.startswith(f"{HEAD}\n{TICKED}\n\n")


@pytest.mark.parametrize("name", list(REWRITES))
def test_an_unticked_checklist_is_unchanged_by_a_rewrite(name: str) -> None:
    after = REWRITES[name](checklist_body(CHECKLIST))
    assert after.startswith(f"{HEAD}\n{CHECKLIST}\n\n")
    assert FIRST_ON not in after


@pytest.mark.parametrize("name", list(REWRITES))
def test_a_ticked_box_in_a_body_for_body_stays_after_a_rewrite(name: str) -> None:
    body = epic_pull_request.body_for(
        MARKER, 600, BRANCH, [5], [merged_task(20, 5)], ["- `a.py` (M)"], ["x.py"], ["- #5: u"]
    ).replace(FIRST_OFF, FIRST_ON, 1)
    after = REWRITES[name](body)
    assert after.startswith(body[: body.index(TICKED) + len(TICKED)] + "\n\n")


# M3 (AC3): a body opened before this change gets no checklist


@pytest.mark.parametrize("name", list(REWRITES))
def test_a_body_without_the_checklist_gets_none_from_a_rewrite(name: str) -> None:
    old = f"{HEAD}\n{OTHERS}{TAIL}"
    after = REWRITES[name](old)
    assert HEADING not in after
    assert "Every task meets its ACs" not in after


@pytest.mark.parametrize("name", list(REWRITES))
def test_a_body_with_only_the_table_gets_no_checklist_from_a_rewrite(name: str) -> None:
    after = REWRITES[name](f"{HEAD}\n{TAIL}")
    assert HEADING not in after


# M4 (AC4): the epic pull request the tick opens carries the section in its body file


def test_the_epic_pull_request_opened_by_the_tick_has_the_checklist(home: Path) -> None:
    host = host_for(*two_merged())
    tick(host, home)
    body = host.bodies[0]
    assert CHECKLIST in body
    table_end = body.index(f"| #6 | #21 | {LINK}6 |\n") + len(f"| #6 | #21 | {LINK}6 |\n")
    assert body[table_end:].startswith(f"\n{CHECKLIST}\n\n")
    assert body.index(HEADING) < body.index("## Self-decided fixes")
