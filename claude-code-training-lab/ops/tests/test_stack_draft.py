"""#327: a stacked pull request is a draft until its base is main. Run: pytest ops/tests"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.agent_tick import MARKER
from ops.tests.test_agent_tick import FakeHost, started
from ops.tests.test_tick_merge import loop_pr

EPIC = "epic/312-topics"
PARENT = "task/9-p"


def stacked(
    number: int = 20, base: str = EPIC, draft: bool = False, **extra: Any
) -> dict[str, Any]:
    return (
        loop_pr(labels=())
        | {
            "number": number,
            "baseRefName": base,
            "isDraft": draft,
            "headRefName": f"task/{number}-x",
            "body": f"{MARKER}\nStacked on #9 through {EPIC} (merge those first).\nCloses #5",
        }
        | extra
    )


def parent(state: str = "MERGED") -> dict[str, Any]:
    return loop_pr(labels=()) | {
        "number": 9,
        "state": state,
        "baseRefName": "main",
        "headRefName": "task/9-p",
        "body": f"{MARKER}\nCloses #4",
    }


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    (tmp_path / "announced-merged").write_text("")
    return tmp_path


def record(home: Path) -> list[str]:
    path = home / "stack-drafts"
    return path.read_text().split() if path.exists() else []


def ready_calls(host: FakeHost) -> list[list[str]]:
    return host.gh_calls("pr", "ready")


# AC1: every open, non-draft loop pull request on a base other than main becomes a draft


def test_open_stacked_pull_request_is_made_a_draft_and_recorded(home: Path) -> None:
    host = FakeHost(prs=[stacked(base=PARENT)])
    log = agent_tick.tick_once(host, home)
    assert any(c[:5] == ["gh", "pr", "ready", "20", "--undo"] for c in ready_calls(host))
    assert record(home) == ["20"]
    assert "pr-20: draft while its base is " + PARENT in log


def test_pull_request_on_main_is_left_alone(home: Path) -> None:
    host = FakeHost(prs=[stacked(base="main")])
    agent_tick.tick_once(host, home)
    assert ready_calls(host) == []
    assert record(home) == []


def test_a_draft_stacked_pull_request_is_not_touched_again(home: Path) -> None:
    host = FakeHost(prs=[stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert ready_calls(host) == []


def test_a_pull_request_without_the_marker_is_not_a_loop_pull_request(home: Path) -> None:
    host = FakeHost(prs=[stacked(body="Closes #5")])
    agent_tick.tick_once(host, home)
    assert ready_calls(host) == []


# AC2: the build prompts of a stacked task ask for a draft


def test_epic_prompt_asks_for_a_normal_pull_request() -> None:
    start = agent_tick.EpicStart(312, EPIC, True, "abc", ())
    text = agent_tick.epic_prompt(start)
    assert f"open a normal pull request into {EPIC} (not a draft" in text


def test_one_parent_prompt_asks_for_a_draft() -> None:
    source = Path(agent_tick.__file__).read_text()
    assert (
        "as a draft (`gh pr create --draft`)." in source.split("Stacked on pull request #")[1][:400]
    )


# AC3: moving the base to main marks a recorded pull request ready, and only that one


def test_recorded_pull_request_is_marked_ready_when_its_base_moves_to_main(home: Path) -> None:
    (home / "stack-drafts").write_text("20")
    host = FakeHost(prs=[parent(), stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert any(
        c[:4] == ["gh", "pr", "ready", "20"] and "--undo" not in c for c in ready_calls(host)
    )
    assert record(home) == []


def test_a_pull_request_not_in_the_record_is_never_marked_ready(home: Path) -> None:
    host = FakeHost(prs=[parent(), stacked(draft=True)])
    agent_tick.tick_once(host, home)
    assert ready_calls(host) == []


def test_one_parent_child_moved_to_main_is_marked_ready(home: Path) -> None:
    (home / "stack-drafts").write_text("20")
    child = stacked(base="task/9-p", draft=True, body=f"{MARKER}\nCloses #5")
    host = FakeHost(prs=[parent(), child])
    agent_tick.tick_once(host, home)
    assert any(
        c[:4] == ["gh", "pr", "ready", "20"] and "--undo" not in c for c in ready_calls(host)
    )
    assert record(home) == []


# AC4: a failed gh pr ready is one log line, tried again next tick, never stops the tick


def test_failed_undo_is_logged_and_retried(home: Path) -> None:
    host = FakeHost(prs=[stacked(base=PARENT)], fail="pr ready")
    log = agent_tick.tick_once(host, home)
    assert record(home) == []
    assert sum("pr-20: draft not set" in line for line in log) == 1
    host.fail = ""
    agent_tick.tick_once(host, home)
    assert record(home) == ["20"]


def test_failed_ready_keeps_the_record_and_the_tick_goes_on(home: Path) -> None:
    (home / "stack-drafts").write_text("20")
    host = FakeHost(prs=[parent(), stacked(draft=True)], fail="pr ready")
    log = agent_tick.tick_once(host, home)
    assert record(home) == ["20"]
    assert sum("pr-20: not marked ready" in line for line in log) == 1


# AC5: a draft stacked pull request is otherwise unchanged


def test_a_draft_stacked_pull_request_still_gets_its_change_request_run(home: Path) -> None:
    from ops.tests.test_tick_merge import remark

    pr = stacked(draft=True)
    pr["comments"] = [remark(101, "please rename X")]
    host = FakeHost(prs=[pr])
    agent_tick.tick_once(host, home)
    assert started(host) == ["Use the work-queue skill for pull request #20 only."]
