import os
import plistlib
import subprocess
from pathlib import Path

import pytest

LAB_DIR = Path(__file__).resolve().parents[2]
INSTALL = LAB_DIR / "ops" / "install-launchd.sh"
START = LAB_DIR / "ops" / "start-loop.sh"
SYSTEM_PATH = "/usr/bin:/bin"


def _fake(bin_dir: Path, name: str, body: str) -> None:
    script = bin_dir / name
    script.write_text(f"#!/bin/bash\n{body}\n")
    script.chmod(0o755)


def _logging_fake(box: dict[str, Path], name: str, tail: str = "") -> None:
    calls = box["calls"]
    _fake(box["bin"], name, f'echo "{name} $*" >> "{calls}"\n{tail}')


@pytest.fixture
def sandbox(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    bin_dir = tmp_path / "bin"
    home.mkdir()
    bin_dir.mkdir()
    box = {"home": home, "bin": bin_dir, "calls": tmp_path / "calls.txt"}
    _logging_fake(box, "launchctl")
    _logging_fake(box, "tmux", 'if [ "$1" = has-session ]; then exit 1; fi')
    _logging_fake(box, "uv")
    return box


def _run(script: Path, args: list[str], box: dict[str, Path]) -> subprocess.CompletedProcess[str]:
    env = {"HOME": str(box["home"]), "PATH": f"{box['bin']}:{SYSTEM_PATH}"}
    return subprocess.run(
        ["/bin/bash", str(script), *args], env=env, capture_output=True, text=True, check=False
    )


def _plist(box: dict[str, Path]) -> Path:
    return box["home"] / "Library" / "LaunchAgents" / "com.reviewradar.loop.plist"


def test_install_writes_a_login_agent_plist(sandbox: dict[str, Path]) -> None:
    result = _run(INSTALL, [], sandbox)
    assert result.returncode == 0, result.stderr
    data = plistlib.loads(_plist(sandbox).read_bytes())
    home = sandbox["home"]
    assert data["Label"] == "com.reviewradar.loop"
    assert data["ProgramArguments"] == ["/bin/bash", str(LAB_DIR / "ops" / "start-loop.sh")]
    assert data["RunAtLoad"] is True
    assert "KeepAlive" not in data
    assert "StartInterval" not in data
    log = str(home / ".reviewradar" / "launchd.log")
    assert data["StandardOutPath"] == log
    assert data["StandardErrorPath"] == log
    assert data["EnvironmentVariables"]["PATH"] == ":".join(
        ["/opt/homebrew/bin", "/usr/local/bin", f"{home}/.local/bin", "/usr/bin", "/bin"]
    )


def test_install_boots_out_an_old_agent_then_bootstraps(sandbox: dict[str, Path]) -> None:
    _run(INSTALL, [], sandbox)
    lines = sandbox["calls"].read_text().splitlines()
    uid = str(os.getuid())
    assert lines[0].startswith(f"launchctl bootout gui/{uid}")
    assert lines[1] == f"launchctl bootstrap gui/{uid} {_plist(sandbox)}"


def test_remove_boots_out_and_archives_the_plist(sandbox: dict[str, Path]) -> None:
    _run(INSTALL, [], sandbox)
    result = _run(INSTALL, ["--remove"], sandbox)
    assert result.returncode == 0, result.stderr
    assert not _plist(sandbox).exists()
    archived = list((sandbox["home"] / ".reviewradar" / "archive").glob("com.reviewradar.loop*"))
    assert len(archived) == 1
    assert sandbox["calls"].read_text().splitlines()[-1].startswith("launchctl bootout")


def test_remove_without_a_plist_is_not_an_error(sandbox: dict[str, Path]) -> None:
    assert _run(INSTALL, ["--remove"], sandbox).returncode == 0


def test_start_loop_announces_once_after_creating_the_session(sandbox: dict[str, Path]) -> None:
    result = _run(START, [], sandbox)
    assert result.returncode == 0, result.stderr
    lines = sandbox["calls"].read_text().splitlines()
    assert lines[-1] == "uv run python ops/agent_tick.py started"
    assert any(line.startswith("tmux new-session") for line in lines[:-1])


def test_start_loop_prints_the_subscribe_link_when_a_topic_is_set(
    sandbox: dict[str, Path],
) -> None:
    settings = sandbox["home"] / ".reviewradar"
    settings.mkdir()
    (settings / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-secret-topic\n")
    result = _run(START, [], sandbox)
    assert "Phone messages: https://ntfy.sh/rr-secret-topic" in result.stdout


def test_start_loop_prints_no_link_when_the_topic_is_empty(sandbox: dict[str, Path]) -> None:
    settings = sandbox["home"] / ".reviewradar"
    settings.mkdir()
    (settings / "agent.env").write_text("NTFY_TOPIC=\n")
    result = _run(START, [], sandbox)
    assert "Phone messages" not in result.stdout + result.stderr


def test_start_loop_sends_nothing_when_the_loop_already_runs(sandbox: dict[str, Path]) -> None:
    _logging_fake(sandbox, "tmux")
    result = _run(START, [], sandbox)
    assert result.returncode == 1
    assert "uv run" not in sandbox["calls"].read_text()
