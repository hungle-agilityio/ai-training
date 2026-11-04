"""The tick passes the Claude Code sign-in folder and entrypoint to every build (#172, AC1 to AC4).

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
    "rr-test: ReviewRadar Claude Code is not signed in (FOLDER); builds wait. "
    "Sign in with: CLAUDE_CONFIG_DIR=FOLDER claude auth login"
)


def message(folder: str) -> str:
    return MESSAGE.replace("FOLDER", folder)


@dataclass
class AuthHost(FakeHost):
    """Answers `claude auth status` with `status`; everything else as FakeHost."""

    status: str = SIGNED_IN
    status_code: int = 0

    def run(self, args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
        if list(args)[-3:] == ["claude", "auth", "status"]:
            self.calls.append(list(args))
            return self.status_code, self.status
        return super().run(args, cwd)

    def status_calls(self) -> list[list[str]]:
        return [c for c in self.calls if c[-3:] == ["claude", "auth", "status"]]


def write_env(home: Path, extra: str = "") -> None:
    (home / "agent.env").write_text(f"AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n{extra}")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_ENTRYPOINT", raising=False)


def ready_host(status: str = SIGNED_IN, status_code: int = 0) -> AuthHost:
    return AuthHost(issues=[issue(1, "agent:ready")], status=status, status_code=status_code)


# AC1: settings and the build environment


def test_both_keys_are_read_and_the_tilde_is_expanded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", "/Users/mini")
    write_env(
        tmp_path, "CLAUDE_CONFIG_DIR=~/.claude-study\nCLAUDE_CODE_ENTRYPOINT=claude-desktop\n"
    )
    settings = agent_tick.read_settings(tmp_path / "agent.env")
    assert agent_tick.claude_env(settings) == {
        "CLAUDE_CONFIG_DIR": "/Users/mini/.claude-study",
        "CLAUDE_CODE_ENTRYPOINT": "claude-desktop",
    }


def test_no_key_or_an_empty_key_changes_nothing(tmp_path: Path) -> None:
    write_env(tmp_path, "CLAUDE_CONFIG_DIR=\nCLAUDE_CODE_ENTRYPOINT=\n")
    assert agent_tick.claude_env(agent_tick.read_settings(tmp_path / "agent.env")) == {}
    write_env(tmp_path)
    assert agent_tick.claude_env(agent_tick.read_settings(tmp_path / "agent.env")) == {}


def test_a_build_start_gets_both_values_and_agent_env_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "from-the-tick")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/from/the/tick")
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    wanted = {
        "CLAUDE_CONFIG_DIR": "/Users/mini/.claude-study",
        "CLAUDE_CODE_ENTRYPOINT": "claude-desktop",
    }
    assert agent_tick.run_build(tmp_path, tmp_path, "p", wanted) == "0"
    env = fake.starts[0][1]["env"]
    assert env["CLAUDE_CONFIG_DIR"] == "/Users/mini/.claude-study"
    assert env["CLAUDE_CODE_ENTRYPOINT"] == "claude-desktop"
    assert env["REVIEWRADAR_LOOP"] == "1"


def test_without_keys_the_build_environment_is_the_ticks_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "from-the-tick")
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_build(tmp_path, tmp_path, "p")
    env = fake.starts[0][1]["env"]
    assert env["CLAUDE_CODE_ENTRYPOINT"] == "from-the-tick"
    assert "CLAUDE_CONFIG_DIR" not in env


def test_the_background_wrapper_reads_agent_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_env(tmp_path, "CLAUDE_CODE_ENTRYPOINT=claude-desktop\n")
    run = tmp_path / "runs" / "issue-1"
    run.mkdir(parents=True)
    monkeypatch.setenv("REVIEWRADAR_HOME", str(tmp_path))
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    assert agent_tick.main(["run", str(run), str(tmp_path), "p"]) == 0
    assert fake.starts[0][1]["env"]["CLAUDE_CODE_ENTRYPOINT"] == "claude-desktop"


def test_the_auth_check_gets_the_same_environment(tmp_path: Path) -> None:
    write_env(tmp_path, "CLAUDE_CONFIG_DIR=/x/study\nCLAUDE_CODE_ENTRYPOINT=claude-desktop\n")
    host = ready_host()
    agent_tick.tick_once(host, tmp_path)
    check = host.status_calls()
    assert len(check) == 1
    assert "CLAUDE_CONFIG_DIR=/x/study" in check[0]
    assert "CLAUDE_CODE_ENTRYPOINT=claude-desktop" in check[0]


# AC2, AC3: signed out


def test_signed_out_starts_no_build_changes_no_label_and_says_so_once(tmp_path: Path) -> None:
    write_env(tmp_path, "CLAUDE_CONFIG_DIR=/x/study\n")
    host = ready_host(SIGNED_OUT, 1)
    agent_tick.tick_once(host, tmp_path)
    assert host.spawned == []
    assert host.gh_calls("issue", "edit") == []
    assert host.sent == [message("/x/study")]
    agent_tick.tick_once(host, tmp_path)
    assert host.spawned == [] and len(host.sent) == 1


def test_the_folder_defaults_to_dot_claude(tmp_path: Path) -> None:
    write_env(tmp_path)
    host = ready_host(SIGNED_OUT)
    agent_tick.tick_once(host, tmp_path)
    assert host.sent == [message("~/.claude")]


def test_the_message_is_urgent() -> None:
    text = "ReviewRadar Claude Code is not signed in (x); builds wait."
    assert agent_tick.message_priority(text) == "urgent"


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


def test_the_issue_builds_in_the_first_tick_after_sign_in(tmp_path: Path) -> None:
    write_env(tmp_path)
    host = ready_host(SIGNED_OUT)
    agent_tick.tick_once(host, tmp_path)
    assert host.gh_calls("issue", "edit") == []
    host.status = SIGNED_IN
    agent_tick.tick_once(host, tmp_path)
    assert any("agent:running" in c for c in host.gh_calls("issue", "edit"))
    assert len(host.spawned) == 1


@pytest.mark.parametrize("output", ["", "something else", "not json {"])
def test_an_unreadable_status_goes_on_as_today(tmp_path: Path, output: str) -> None:
    write_env(tmp_path)
    host = ready_host(output, 1)
    agent_tick.tick_once(host, tmp_path)
    assert len(host.spawned) == 1
    assert not any("not signed in" in m for m in host.sent)


# AC4: the failure text


def failed_comment(home: Path, extra: str, exit_text: str = "no-artifact") -> str:
    write_env(home, extra)
    add_run(home, "issue-1", 77, exit_text=exit_text)
    host = AuthHost(issues=[issue(1, "agent:ready", "agent:running")])
    agent_tick.tick_once(host, home)
    return host.gh_calls("issue", "comment")[0][5]


def test_no_artifact_without_the_entrypoint_names_the_missing_key(tmp_path: Path) -> None:
    body = failed_comment(tmp_path, "")
    assert "started 3 times without the Artifact tool" in body
    assert "CLAUDE_CODE_ENTRYPOINT is not set in agent.env" in body


def test_no_artifact_with_the_entrypoint_does_not(tmp_path: Path) -> None:
    body = failed_comment(tmp_path, "CLAUDE_CODE_ENTRYPOINT=claude-desktop\n")
    assert "started 3 times without the Artifact tool" in body
    assert "CLAUDE_CODE_ENTRYPOINT is not set" not in body


def test_an_entrypoint_in_the_ticks_own_environment_counts_as_passed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "claude-desktop")
    assert "is not set" not in failed_comment(tmp_path, "")


def test_another_failure_never_gets_the_entrypoint_text(tmp_path: Path) -> None:
    assert "CLAUDE_CODE_ENTRYPOINT" not in failed_comment(tmp_path, "", "3")
