"""The loop uses one default Claude Code and sets the Artifact entrypoint itself (AC1 to AC5).

No `claude`, no network: the host, Popen and the clock are faked.
Run: uv run pytest ops/tests --no-cov
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, add_run, issue
from ops.tests.test_build_artifact_tool import RESULT, WITH, Child, Fake

SIGNED_OUT = json.dumps({"loggedIn": False})
SIGNED_IN = json.dumps({"loggedIn": True, "authMethod": "claude.ai"})
MESSAGE = (
    "rr-test: ReviewRadar Claude Code is not signed in (~/.claude); builds wait. "
    "Sign in with: claude auth login"
)
STATUS = ["claude", "auth", "status"]


@dataclass
class AuthHost(FakeHost):
    """Answers `claude auth status` with `status`; everything else as FakeHost."""

    status: str = SIGNED_IN
    status_code: int = 0

    def run(self, args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
        if list(args)[-3:] == STATUS:
            self.calls.append(list(args))
            return self.status_code, self.status
        return super().run(args, cwd)

    def status_calls(self) -> list[list[str]]:
        return [c for c in self.calls if c[-3:] == STATUS]


def write_env(home: Path, extra: str = "") -> None:
    (home / "agent.env").write_text(f"AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n{extra}")


def ready_host(status: str = SIGNED_IN, status_code: int = 0) -> AuthHost:
    return AuthHost(issues=[issue(1, "agent:ready")], status=status, status_code=status_code)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_ENTRYPOINT", raising=False)


# AC1, AC2: the build environment


def test_a_build_start_gets_the_entrypoint_without_any_setting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    assert agent_tick.run_build(tmp_path, tmp_path, "p") == "0"
    env = fake.starts[0][1]["env"]
    assert env["CLAUDE_CODE_ENTRYPOINT"] == "claude-desktop"
    assert env["REVIEWRADAR_LOOP"] == "1"
    assert "CLAUDE_CONFIG_DIR" not in env


def test_the_entrypoint_wins_and_the_config_dir_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "something-else")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/Users/mini/.claude-study")
    monkeypatch.setenv("KEEP_ME", "yes")
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_build(tmp_path, tmp_path, "p")
    env = fake.starts[0][1]["env"]
    assert env["CLAUDE_CODE_ENTRYPOINT"] == "claude-desktop"
    assert "CLAUDE_CONFIG_DIR" not in env
    assert env["KEEP_ME"] == "yes"


def test_the_background_wrapper_sets_the_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_env(tmp_path)
    run = tmp_path / "runs" / "issue-1"
    run.mkdir(parents=True)
    monkeypatch.setenv("REVIEWRADAR_HOME", str(tmp_path))
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    assert agent_tick.main(["run", str(run), str(tmp_path), "p"]) == 0
    assert fake.starts[0][1]["env"]["CLAUDE_CODE_ENTRYPOINT"] == "claude-desktop"


def test_the_auth_check_uses_the_default_folder_and_the_entrypoint(tmp_path: Path) -> None:
    write_env(tmp_path)
    host = ready_host()
    agent_tick.tick_once(host, tmp_path)
    check = host.status_calls()
    assert len(check) == 1
    wanted = ["env", "-u", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_ENTRYPOINT=claude-desktop"]
    assert check[0][:4] == wanted


# AC3: old agent.env keys are ignored


def test_old_keys_in_agent_env_are_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_env(tmp_path, "CLAUDE_CONFIG_DIR=~/.claude-study\nCLAUDE_CODE_ENTRYPOINT=other\n")
    settings = agent_tick.read_settings(tmp_path / "agent.env")
    assert settings.concurrency == 2
    run = tmp_path / "runs" / "issue-1"
    run.mkdir(parents=True)
    monkeypatch.setenv("REVIEWRADAR_HOME", str(tmp_path))
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.main(["run", str(run), str(tmp_path), "p"])
    env = fake.starts[0][1]["env"]
    assert env["CLAUDE_CODE_ENTRYPOINT"] == "claude-desktop"
    assert "CLAUDE_CONFIG_DIR" not in env


def test_the_example_has_no_claude_keys() -> None:
    example = (Path(agent_tick.__file__).parent / "agent.env.example").read_text()
    assert "CLAUDE_CONFIG_DIR" not in example
    assert "CLAUDE_CODE_ENTRYPOINT" not in example


# AC4: signed out (behaviour of #172 kept, new text)


def test_signed_out_starts_no_build_changes_no_label_and_says_so_once(tmp_path: Path) -> None:
    write_env(tmp_path)
    host = ready_host(SIGNED_OUT, 1)
    agent_tick.tick_once(host, tmp_path)
    assert host.spawned == []
    assert host.gh_calls("issue", "edit") == []
    assert host.sent == [MESSAGE]
    agent_tick.tick_once(host, tmp_path)
    assert host.spawned == [] and len(host.sent) == 1


def test_the_message_is_urgent() -> None:
    assert agent_tick.message_priority(MESSAGE.split(": ", 1)[1]) == "urgent"


def test_after_a_signed_in_check_the_message_is_sent_again(tmp_path: Path) -> None:
    write_env(tmp_path)
    host = ready_host(SIGNED_OUT)
    agent_tick.tick_once(host, tmp_path)
    host.status = SIGNED_IN
    agent_tick.tick_once(host, tmp_path)
    assert len(host.spawned) == 1
    host.status = SIGNED_OUT
    agent_tick.tick_once(host, tmp_path)
    assert len([m for m in host.sent if "not signed in" in m]) == 2


@pytest.mark.parametrize("output", ["", "something else", "not json {"])
def test_an_unreadable_status_goes_on_as_today(tmp_path: Path, output: str) -> None:
    write_env(tmp_path)
    host = ready_host(output, 1)
    agent_tick.tick_once(host, tmp_path)
    assert len(host.spawned) == 1
    assert not any("not signed in" in m for m in host.sent)


# AC5: the failure comment


def failed_comment(home: Path, exit_text: str = "no-artifact") -> str:
    write_env(home)
    add_run(home, "issue-1", 77, exit_text=exit_text)
    host = AuthHost(issues=[issue(1, "agent:ready", "agent:running")])
    agent_tick.tick_once(host, home)
    return host.gh_calls("issue", "comment")[0][5]


def test_no_artifact_comment_does_not_mention_agent_env(tmp_path: Path) -> None:
    body = failed_comment(tmp_path)
    assert "started 3 times without the Artifact tool" in body
    assert "CLAUDE_CODE_ENTRYPOINT" not in body
    assert "agent.env" not in body
