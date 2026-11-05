"""#199: the tick and start-loop.sh read ops/agent.env first, else the state folder (AC1 to AC5).

No network, no `claude`: the host is faked, the folders are temporary.
Run: uv run pytest ops/tests --no-cov
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost
from ops.tests.test_tick_notify_priority import PriorityHost

LAB_DIR = Path(__file__).resolve().parents[2]
SECRET = "hooks.example.test/secret-value-123"


@pytest.fixture
def folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "state"
    home.mkdir()
    repo_env = tmp_path / "ops" / "agent.env"
    repo_env.parent.mkdir()
    monkeypatch.setattr(agent_tick, "REPO_ENV", repo_env)
    return home, repo_env


# AC1


def test_repo_file_wins_over_state_file(folders: tuple[Path, Path]) -> None:
    home, repo_env = folders
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=state-topic\n")
    repo_env.write_text("AGENT_CONCURRENCY=3\n")
    settings = agent_tick.read_settings(agent_tick.settings_file(home))
    assert settings.concurrency == 3
    assert settings.ntfy_topic == ""  # keys are not merged


def test_missing_repo_file_falls_back_to_state_file(folders: tuple[Path, Path]) -> None:
    home, _ = folders
    (home / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=state-topic\n")
    settings = agent_tick.read_settings(agent_tick.settings_file(home))
    assert (settings.concurrency, settings.ntfy_topic) == (2, "state-topic")


# AC3


def test_tick_first_line_names_repo_file_without_values(folders: tuple[Path, Path]) -> None:
    home, repo_env = folders
    repo_env.write_text(f"AGENT_CONCURRENCY=2\nSLACK_WEBHOOK_URL={SECRET}\n")
    lines = agent_tick.tick_once(FakeHost(), home)
    assert lines[0] == "settings: ops/agent.env"
    assert all(SECRET not in line for line in lines)


def test_tick_first_line_names_state_file_on_fallback(folders: tuple[Path, Path]) -> None:
    home, _ = folders
    (home / "agent.env").write_text(f"SLACK_WEBHOOK_URL={SECRET}\n")
    lines = agent_tick.tick_once(FakeHost(), home)
    assert lines[0] == f"settings: {home / 'agent.env'}"
    assert all(SECRET not in line for line in lines)


def test_started_names_the_file_and_prints_no_value(
    folders: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    home, repo_env = folders
    repo_env.write_text(f"NTFY_TOPIC=repo-topic\nSLACK_WEBHOOK_URL={SECRET}\n")
    host = PriorityHost()
    assert agent_tick.announce_started(host, home, "mini") == 0
    out = capsys.readouterr().out
    assert "settings: ops/agent.env" in out
    assert SECRET not in out and "repo-topic" not in out
    assert [m for _, m in host.priorities] == ["ReviewRadar loop started on mini"]


# AC2


def run_settings_snippet(lab: Path, state: Path) -> str:
    """Runs the settings part of the real start-loop.sh for a fake lab and state folder."""
    script = (LAB_DIR / "ops" / "start-loop.sh").read_text()
    start = script.index("# Same rule as the tick")
    end = script.index('if [ -n "$TOPIC" ]')
    snippet = f'LAB="{lab}"\nSTATE="{state}"\n' + script[start:end] + 'echo "topic=$TOPIC"\n'
    result = subprocess.run(["bash", "-c", snippet], capture_output=True, text=True, check=True)
    return result.stdout


def test_start_loop_reads_topic_from_repo_file(tmp_path: Path) -> None:
    (tmp_path / "ops").mkdir()
    (tmp_path / "ops" / "agent.env").write_text("NTFY_TOPIC=repo-topic\n")
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "agent.env").write_text("NTFY_TOPIC=state-topic\n")
    out = run_settings_snippet(tmp_path, tmp_path / "state")
    assert "settings: ops/agent.env" in out and "topic=repo-topic" in out


def test_start_loop_falls_back_to_state_file(tmp_path: Path) -> None:
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "agent.env").write_text("NTFY_TOPIC=state-topic\n")
    out = run_settings_snippet(tmp_path, tmp_path / "state")
    assert "topic=state-topic" in out


# AC5


def test_repo_agent_env_cannot_be_committed() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-q", "ops/agent.env"], cwd=LAB_DIR, check=False
    )
    assert result.returncode == 0
