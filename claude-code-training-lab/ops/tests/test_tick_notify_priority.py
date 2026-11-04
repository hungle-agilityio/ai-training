"""#167: ntfy priority and title per message, the 6-hour pull reminder, `started` (host faked)."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost
from ops.tests.test_tick_notify_cases import HOOK, ON_MAIN, NotifyHost, make_home

HOUR = 3600.0


@dataclass
class PriorityHost(NotifyHost):
    """NotifyHost that also records the priority of each ntfy message."""

    priorities: list[tuple[str, str]] = field(default_factory=list)

    def notify_priority(self, topic: str, message: str, priority: str) -> None:
        self.priorities.append((priority, message))


@pytest.fixture
def home(tmp_path: Path) -> Path:
    return make_home(tmp_path)


def sent_priority(message: str, tmp_path: Path) -> str:
    host = PriorityHost()
    tick = agent_tick.Tick(host, tmp_path, agent_tick.Settings(1, "rr-test"))
    tick.notify(message)
    assert [m for _, m in host.priorities] == [message]
    return host.priorities[0][0]


HIGH = [
    "ReviewRadar PR #5 opened for #4 (pr:ready-for-review)",
    "ReviewRadar PR #5 updated for #4 (pr:ready-for-review)",
    "ReviewRadar PR #5 needs you: pr:blocked",
    "ReviewRadar build for issue #4 failed: boom",
    "ReviewRadar build for pull request #5 timed out",
    "ReviewRadar build for issue #4 did not start: worktree failed",
    "ReviewRadar PR #5 not merged: CI is red",
    "ReviewRadar PR #5 merged (#4); main checkout not updated: the checkout is on feat/x",
    "main is red at abc1234: https://example.test/run/1",
    "ReviewRadar main checkout not updated: it has tracked changes",
    "ReviewRadar loop paused 60 minutes: plan limit reached (issue-4)",
    "ReviewRadar loop started on mini",
    "ReviewRadar some message nobody listed",
]
LOW = [
    "ReviewRadar started #4: Fix the thing",
    "ReviewRadar working on PR #5 (2 change requests open)",
    "ReviewRadar PR #5 merged (#4); main is now abc1234",
    "ReviewRadar waiting: 1 ready issues blocked\n#6 waits for #4: building",
    "ReviewRadar waiting: 2 pull requests open, 1 ready issue",
    "ReviewRadar queue empty, 0 pull requests waiting",
]


# AC1, AC2


@pytest.mark.parametrize("message", HIGH)
def test_messages_that_need_the_owner_ring(message: str, tmp_path: Path) -> None:
    assert sent_priority(message, tmp_path) == "high"


@pytest.mark.parametrize("message", LOW)
def test_information_messages_are_silent(message: str, tmp_path: Path) -> None:
    assert sent_priority(message, tmp_path) == "low"


def test_tick_sends_started_silently_and_failure_loudly(home: Path) -> None:
    from ops.tests.test_agent_tick import add_run, issue

    add_run(home, "issue-1", 77, exit_text="1", log="boom")
    host = PriorityHost(
        issues=[issue(1, "agent:running"), issue(4, "agent:ready") | {"title": "Fix"}]
    )
    agent_tick.tick_once(host, home)
    by_text = {m: p for p, m in host.priorities}
    assert by_text["ReviewRadar started #4: Fix"] == "low"
    assert any(p == "high" and "failed" in m for p, m in host.priorities)


# AC3


class Seen:
    def __init__(self) -> None:
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request, timeout: float = 0) -> Any:
        self.requests.append(request)
        return type("Reply", (), {"close": lambda self: None})()


def test_real_ntfy_post_has_title_and_priority_and_unchanged_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = Seen()
    monkeypatch.setattr(urllib.request, "urlopen", seen)
    agent_tick.RealHost().notify_priority("rr-test", "ReviewRadar started #4: x", "low")
    (request,) = seen.requests
    assert request.get_header("Title") == "ReviewRadar"
    assert request.get_header("Priority") == "low"
    assert request.data == b"ReviewRadar started #4: x"


def test_real_notify_without_priority_defaults_to_high(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = Seen()
    monkeypatch.setattr(urllib.request, "urlopen", seen)
    agent_tick.RealHost().notify("rr-test", "hello")
    assert seen.requests[0].get_header("Priority") == "high"
    assert seen.requests[0].get_header("Title") == "ReviewRadar"


def test_failed_ntfy_post_prints_the_error_and_goes_on(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise OSError("no route")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    agent_tick.RealHost().notify_priority("rr-test", "hi", "low")
    assert "ntfy failed: no route" in capsys.readouterr().out


def test_slack_gets_plain_text_without_priority(tmp_path: Path) -> None:
    home = make_home(tmp_path, f"NTFY_TOPIC=rr-test\nSLACK_WEBHOOK_URL={HOOK}\n")
    host = PriorityHost()
    agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env")).notify(
        "ReviewRadar started #4: x"
    )
    assert host.slack_sent == ["ReviewRadar started #4: x"]


def test_host_without_priority_support_still_gets_the_message(home: Path) -> None:
    host = FakeHost()
    agent_tick.Tick(host, home, agent_tick.Settings(1, "rr-test")).notify("hello")
    assert host.sent == ["rr-test: hello"]


# AC4


def pull_problem_host(clock: float) -> PriorityHost:
    return PriorityHost(clock=clock, git={"branch --show-current": (0, "feat/x\n")})


def reminders(host: PriorityHost) -> list[str]:
    return [m for _, m in host.priorities if "main checkout not updated" in m]


def test_pull_problem_is_sent_first_time_and_not_again_before_six_hours(home: Path) -> None:
    host = pull_problem_host(1_000_000.0)
    agent_tick.tick_once(host, home)
    host.clock += 6 * HOUR - 60
    agent_tick.tick_once(host, home)
    assert reminders(host) == ["ReviewRadar main checkout not updated: the checkout is on feat/x"]


def test_pull_problem_is_sent_again_after_six_hours(home: Path) -> None:
    host = pull_problem_host(1_000_000.0)
    agent_tick.tick_once(host, home)
    host.clock += 6 * HOUR
    agent_tick.tick_once(host, home)
    assert len(reminders(host)) == 2


def test_a_new_reason_is_sent_at_once(home: Path) -> None:
    host = pull_problem_host(1_000_000.0)
    agent_tick.tick_once(host, home)
    host.git = {"branch --show-current": (0, "main\n"), "status --porcelain": (0, " M a.py\n")}
    host.clock += 60
    agent_tick.tick_once(host, home)
    assert len(reminders(host)) == 2


def test_a_good_pull_clears_the_reminder(home: Path) -> None:
    host = pull_problem_host(1_000_000.0)
    agent_tick.tick_once(host, home)
    assert (home / "last-pull-problem").exists()
    host.git = dict(ON_MAIN)
    host.clock += 60
    agent_tick.tick_once(host, home)
    assert not (home / "last-pull-problem").exists()
    assert not (home / "last-pull-problem-sent").exists()
    host.git = {"branch --show-current": (0, "feat/x\n")}
    host.clock += 60
    agent_tick.tick_once(host, home)
    assert len(reminders(host)) == 2


# AC5


def test_started_sends_one_message_and_takes_no_lock(home: Path) -> None:
    host = PriorityHost()
    assert agent_tick.announce_started(host, home, "mini") == 0
    assert host.priorities == [("high", "ReviewRadar loop started on mini")]
    assert host.calls == [] and not (home / "tick.lock").exists()


def test_started_without_topic_sends_nothing(tmp_path: Path) -> None:
    home = make_home(tmp_path, "")
    host = PriorityHost()
    assert agent_tick.announce_started(host, home, "mini") == 0
    assert host.priorities == [] and host.sent == []


def test_main_started_command_exits_zero(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    host = PriorityHost()
    monkeypatch.setenv("REVIEWRADAR_HOME", str(home))
    monkeypatch.setattr(agent_tick, "RealHost", lambda: host)
    assert agent_tick.main(["started"]) == 0
    assert len(host.priorities) == 1 and host.priorities[0][0] == "high"
