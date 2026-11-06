"""#259: the tick ends a build that runs past the time limit, even when its pid is alive."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ops import agent_tick
from ops.agent_tick import RUN_LIMIT
from ops.tests.test_agent_tick import NOW, FakeHost, add_run, issue

STALE = RUN_LIMIT + 15 * 60


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def put_started(run: Path, text: str) -> None:
    (run / "started").write_text(text)


def keys(host: FakeHost, home: Path) -> list[str]:
    tick = agent_tick.Tick(host, home, agent_tick.Settings(1, "rr-test"))
    return sorted(agent_tick.running_keys(tick))


# AC1


def test_start_writes_the_start_time_next_to_the_pid(home: Path) -> None:
    host = FakeHost(issues=[issue(1, "agent:ready")])
    agent_tick.tick_once(host, home)
    run = home / "runs" / "issue-1"
    assert (run / "started").read_text() == str(int(NOW))
    assert (run / "pid").exists()


# AC2


def test_running_build_inside_the_limit_counts_as_running(home: Path) -> None:
    run = add_run(home, "issue-1", 77)
    put_started(run, str(int(NOW - STALE + 60)))
    assert keys(FakeHost(alive_pids={77}), home) == ["issue-1"]


def test_alive_pid_past_the_limit_counts_as_ended(home: Path) -> None:
    run = add_run(home, "issue-1", 77)
    put_started(run, str(int(NOW - STALE - 1)))
    host = FakeHost(alive_pids={77})
    assert keys(host, home) == []
    assert not any(c[0] == "kill" for c in host.calls)


# AC3


@pytest.mark.parametrize("text", [None, "", "soon"], ids=["missing", "empty", "not-a-number"])
def test_missing_or_bad_start_time_is_judged_by_the_pid(home: Path, text: str | None) -> None:
    run = add_run(home, "issue-1", 77)
    if text is not None:
        put_started(run, text)
    assert keys(FakeHost(alive_pids={77}), home) == ["issue-1"]


# AC4


@pytest.mark.parametrize(("exit_text", "outcome"), [(None, "gone"), ("timeout", "timeout")])
def test_stale_run_is_handled_as_ended(
    home: Path, mocker: MockerFixture, exit_text: str | None, outcome: str
) -> None:
    run = add_run(home, "issue-1", 77, exit_text=exit_text)
    put_started(run, str(int(NOW - STALE - 1)))
    host = FakeHost(issues=[issue(1, "agent:running")], alive_pids={77})
    handled = mocker.spy(agent_tick, "handle_end")
    agent_tick.tick_once(host, home)
    assert handled.call_args.args[2] == outcome
    assert not run.exists()
