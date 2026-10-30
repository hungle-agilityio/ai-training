"""A build without the Artifact tool is stopped and started again.

Spec: specs/build-artifact-tool/spec.md (AC1 to AC7). No `claude`, no network: Popen, killpg
and the clock are faked. Run: uv run pytest ops/tests --no-cov
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, add_run, issue

WITH = json.dumps({"type": "system", "subtype": "init", "tools": ["Bash", "Artifact"]}) + "\n"
WITHOUT = json.dumps({"type": "system", "subtype": "init", "tools": ["Bash"]}) + "\n"
RESULT = json.dumps({"type": "result", "result": "all done"}) + "\n"


class Child:
    pid = 4242

    def __init__(self, lines: list[str], code: int = 0, hangs: bool = False) -> None:
        self.stdout = lines
        self.code = code
        self.hangs = hangs

    def wait(self, timeout: float) -> int:
        if self.hangs:
            raise subprocess.TimeoutExpired("claude", timeout)
        return self.code


class Fake:
    """Hands out one Child per start and records the calls."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, children: list[Child]) -> None:
        self.children = list(children)
        self.starts: list[tuple[list[str], dict[str, Any]]] = []
        self.signals: list[int] = []
        self.now = 1000.0
        monkeypatch.setattr(subprocess, "Popen", self.popen)
        monkeypatch.setattr(os, "killpg", lambda pid, sig: self.signals.append(sig))
        monkeypatch.setattr(time, "monotonic", lambda: self.now)

    def popen(self, args: list[str], **kwargs: Any) -> Child:
        self.starts.append((args, kwargs))
        return self.children.pop(0)


def test_artifact_present_runs_one_start_and_keeps_the_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "0"
    args, kwargs = fake.starts[0]
    assert args[:3] == ["claude", "-p", "p"] and args[-1] == agent_tick.HINT
    assert args[args.index("--allowedTools") + 1] == "Artifact"
    assert "dangerously" not in " ".join(args)
    assert kwargs["env"]["REVIEWRADAR_LOOP"] == "1"
    assert kwargs["stdin"] == subprocess.DEVNULL and kwargs["start_new_session"] is True
    assert (tmp_path / "session-1.jsonl").read_text() == WITH + RESULT
    assert (tmp_path / "log.txt").read_text() == "start 1 of 3\nall done\n"
    assert (tmp_path / "exit").read_text() == "0"
    assert fake.signals == []


def test_missing_then_present_starts_again(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = Fake(monkeypatch, [Child([WITHOUT]), Child([WITH, RESULT])])
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "0"
    assert len(fake.starts) == 2
    assert fake.signals == [signal.SIGTERM] and fake.children == []
    assert (tmp_path / "session-1.jsonl").read_text() == WITHOUT
    assert (tmp_path / "session-2.jsonl").read_text() == WITH + RESULT
    assert (tmp_path / "log.txt").read_text() == (
        "start 1 of 3\nstart 1: no Artifact tool, stopped\nstart 2 of 3\nall done\n"
    )


def test_missing_three_times_is_no_artifact_and_fails_the_issue_without_a_pause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = Fake(monkeypatch, [Child([WITHOUT]) for _ in range(3)])
    home = tmp_path / "home"
    home.mkdir()
    (home / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    run = add_run(home, "issue-1", 77)
    assert agent_tick.run_build(run, tmp_path, "p") == "no-artifact"
    assert len(fake.starts) == 3
    assert (run / "exit").read_text() == "no-artifact"
    reason = "started 3 times without the Artifact tool"
    host = FakeHost(issues=[issue(1, "agent:ready", "agent:running")])
    agent_tick.tick_once(host, home)
    assert ["gh", "issue", "edit", "1", "--add-label", "agent:failed", "--remove-label",
            "agent:running", "--repo", agent_tick.REPO] in host.calls
    assert reason in host.gh_calls("issue", "comment")[0][5]
    assert host.sent[0] == f"rr-test: ReviewRadar build for issue #1 failed: {reason}"
    assert not (home / "paused-until").exists()


def test_no_init_event_runs_to_its_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = Fake(monkeypatch, [Child([RESULT], code=3)])
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "3"
    assert len(fake.starts) == 1 and fake.signals == []


def test_a_line_that_is_not_json_goes_to_both_logs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    Fake(monkeypatch, [Child(["Claude usage limit reached\n", WITH])])
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "0"
    assert "Claude usage limit reached\n" in (tmp_path / "log.txt").read_text()
    assert (tmp_path / "session-1.jsonl").read_text() == "Claude usage limit reached\n" + WITH


def test_time_limit_counts_all_starts_and_stops_the_running_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = Fake(monkeypatch, [Child([WITHOUT]), Child([], hangs=True)])
    clock = iter([1000.0, 1000.0, 1001.0, 1001.0, 1001.0 + agent_tick.RUN_LIMIT])
    monkeypatch.setattr(time, "monotonic", lambda: next(clock))
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "timeout"
    assert len(fake.starts) == 2
    assert fake.signals == [signal.SIGTERM, signal.SIGTERM, signal.SIGKILL]
    assert (tmp_path / "exit").read_text() == "timeout"
