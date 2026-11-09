"""#347: a stacked draft opened by a build is marked ready like one the tick made."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import FakeHost
from ops.tests.test_stack_draft import EPIC, parent, ready_calls, record, stacked


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def marked_ready(host: FakeHost, number: int = 20) -> list[list[str]]:
    wanted = ["gh", "pr", "ready", str(number)]
    return [c for c in ready_calls(host) if c[:4] == wanted and "--undo" not in c]


def on_main(**extra: Any) -> dict[str, Any]:
    return stacked(base="main", draft=True, **extra)


# AC1: a draft the build opened is recorded while its base is not main


def test_a_build_made_draft_is_recorded_while_its_base_is_not_main(home: Path) -> None:
    host = FakeHost(prs=[stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert record(home) == ["20"]
    assert ready_calls(host) == []


def test_recording_keeps_the_numbers_already_there(home: Path) -> None:
    (home / "stack-drafts").write_text("7")
    host = FakeHost(prs=[stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert record(home) == ["7", "20"]


def test_a_second_tick_records_it_once(home: Path) -> None:
    host = FakeHost(prs=[stacked(draft=True)])
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert record(home) == ["20"]


# AC2: marked ready when its base moves to main, or already on main


def test_a_recorded_build_draft_is_marked_ready_when_the_tick_moves_it(home: Path) -> None:
    host = FakeHost(prs=[stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert record(home) == ["20"]

    host.prs = [parent(), stacked(draft=True)]
    agent_tick.tick_once(host, home)

    assert len(marked_ready(host)) == 1
    assert record(home) == []


def test_a_build_draft_already_on_main_is_marked_ready_and_not_kept(home: Path) -> None:
    host = FakeHost(prs=[on_main()])
    log = agent_tick.tick_once(host, home)
    assert len(marked_ready(host)) == 1
    assert record(home) == []
    assert "pr-20: ready for review, its base is main" in log


def test_a_draft_moved_in_this_tick_without_a_record_is_ready_at_the_next_tick(home: Path) -> None:
    host = FakeHost(prs=[parent(), stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert marked_ready(host) == []

    host.prs = [on_main()]
    agent_tick.tick_once(host, home)
    assert len(marked_ready(host)) == 1


# AC3: every other draft stays a draft


@pytest.mark.parametrize(
    "body",
    [
        f"Stacked on #9 through {EPIC} (merge those first).\nCloses #5",
        f"{MARKER}\nCloses #5",
        f"{MARKER}\nNot Stacked on anything, see the notes.\nCloses #5",
    ],
    ids=["no-marker", "no-stacked-line", "words-inside-a-line"],
)
@pytest.mark.parametrize("base", ["main", EPIC])
def test_other_drafts_are_never_marked_ready_or_recorded(home: Path, body: str, base: str) -> None:
    host = FakeHost(prs=[stacked(base=base, draft=True, body=body)])
    agent_tick.tick_once(host, home)
    assert marked_ready(host) == []
    assert record(home) == []


def test_a_ready_pull_request_on_main_is_left_alone(home: Path) -> None:
    host = FakeHost(prs=[stacked(base="main", draft=False)])
    agent_tick.tick_once(host, home)
    assert ready_calls(host) == []
    assert record(home) == []


@pytest.mark.parametrize("state", ["MERGED", "CLOSED"])
def test_an_ended_draft_is_left_alone(home: Path, state: str) -> None:
    host = FakeHost(prs=[stacked(base="main", draft=True, state=state)])
    agent_tick.tick_once(host, home)
    assert marked_ready(host) == []
    assert record(home) == []


# AC4: a failed gh pr ready is logged, retried, and does not stop the tick


def test_a_failed_ready_is_logged_and_retried_next_tick(home: Path) -> None:
    host = FakeHost(prs=[on_main()], fail="pr ready")
    log = agent_tick.tick_once(host, home)
    assert sum("pr-20: not marked ready" in line for line in log) == 1
    assert record(home) == ["20"]

    host.fail = ""
    agent_tick.tick_once(host, home)
    assert len(marked_ready(host)) == 2
    assert record(home) == []


def test_a_failed_ready_does_not_stop_the_next_pull_request(home: Path) -> None:
    other = on_main(number=21, headRefName="task/21-x")
    host = FakeHost(prs=[on_main(), other], fail="pr ready 20")
    agent_tick.tick_once(host, home)
    assert len(marked_ready(host, 21)) == 1
    assert record(home) == ["20"]
