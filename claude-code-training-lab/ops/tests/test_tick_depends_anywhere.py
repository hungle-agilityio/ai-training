"""#584: the tick reads `Depends on` and `Part of the epic` anywhere in a line."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.epic_branch import epic_number
from ops.tests.test_agent_tick import issue, started
from ops.tests.test_tick_hardening import GitHost

EPIC = 104


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def files(name: str) -> str:
    return f"## Files likely touched\n\n- `reviews/{name}.py`\n"


def tick(home: Path, issues: list[dict[str, Any]]) -> tuple[GitHost, list[str]]:
    host = GitHost(prs=[], issues=issues, git={})
    return host, agent_tick.tick_once(host, home)


def epic_issue() -> dict[str, Any]:
    return issue(EPIC, "epic", body="The epic.") | {"title": "Epic: living with nature"}


def base_task(*labels: str) -> dict[str, Any]:
    body = f"Part of the epic #{EPIC}.\nDepends on: none\n\n" + files("t107")
    return issue(107, *(labels or ("agent:ready",)), body=body)


def dependent_task() -> dict[str, Any]:
    body = f"Part of the epic #{EPIC}. Depends on #107.\n\n" + files("t105")
    return issue(105, "agent:ready", body=body)


# M1: a dependency written after other text in the line is read


def test_depends_on_is_read_after_other_text_in_the_same_line() -> None:
    assert agent_tick.depends_on("Part of the epic #104. Depends on #107.") == {107}


def test_depends_on_still_reads_every_line_of_a_multi_line_body() -> None:
    body = "Depends on #63, #61 (both change settings.py)\nDepends on #7\nSee #99"
    assert agent_tick.depends_on(body) == {63, 61, 7}


# M2: no dependency gives an empty set


def test_depends_on_none_gives_no_dependency() -> None:
    assert agent_tick.depends_on("Depends on: none") == set()


def test_a_body_without_depends_on_gives_no_dependency() -> None:
    assert agent_tick.depends_on("No dependency here, see #5") == set()


# M3: the epic is read anywhere in a line


def test_epic_number_is_read_after_other_text_in_the_same_line() -> None:
    assert epic_number("Some text. Part of the epic #104. Depends on #107.") == 104


def test_epic_number_takes_the_first_match_and_none_without_it() -> None:
    assert epic_number("x Part of the epic #1.\nPart of the epic #2.") == 1
    assert epic_number("No epic here, see #5") is None


# M4 and AC3: the dependent task is held until its base task is in the epic branch


def test_the_tick_starts_the_base_task_and_not_the_older_dependent_one(home: Path) -> None:
    host, _ = tick(home, [epic_issue(), dependent_task(), base_task()])
    prompts = started(host)
    assert len(prompts) == 1
    assert "issue #107 only" in prompts[0]
    assert not any("issue #105" in p for p in prompts)


def test_nothing_starts_for_the_dependent_task_while_its_base_task_is_running(
    home: Path,
) -> None:
    host, _ = tick(home, [epic_issue(), dependent_task(), base_task("agent:running")])
    assert not any("issue #105" in p for p in started(host))
