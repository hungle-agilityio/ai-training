"""ops/flow.toml holds the project values of the flow. Run: pytest ops/tests/test_flow_config.py"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ops import flow_config
from ops.flow_config import FlowConfig, FlowConfigError

OPS = Path(__file__).resolve().parents[1]
CHECKS = (
    ("uv", "run", "ruff", "check", "."),
    ("uv", "run", "mypy", "."),
    ("uv", "run", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider"),
)
VALID = """\
[project]
repo = "acme/shop"
owner = "acme-owner"
app_dir = "."
display_name = "Shop"
slug = "shop"

[loop]
state_dir = "~/.shop"
tmux_session = "shop-loop"
launchd_label = "com.shop.loop"
setup_command = ["uv", "sync", "--frozen"]
alone_words = []

[checks]
commands = [["uv", "run", "pytest"]]
ci_workflow = "CI"
protected_test_dirs = ["tests"]

[release]
timezone = "Europe/Berlin"
deploy_line = ""
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "flow.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_committed_file_has_todays_values() -> None:
    config = flow_config.load(OPS / "flow.toml")
    assert config.project_repo == "hungle-agilityio/ai-training"
    assert config.project_owner == "hungle-agilityio"
    assert config.project_app_dir == "claude-code-training-lab"
    assert config.project_display_name == "ReviewRadar"
    assert config.project_slug == "reviewradar"
    assert config.loop_state_dir == Path.home() / ".reviewradar"
    assert config.loop_tmux_session == "rr-loop"
    assert config.loop_launchd_label == "com.reviewradar.loop"
    assert config.loop_setup_command == ("uv", "sync", "--frozen")
    assert config.loop_alone_words == ("migrations/", "models.py")
    assert config.checks_commands == CHECKS
    assert config.checks_ci_workflow == "Checks"
    assert config.checks_protected_test_dirs == ("reviews/tests",)
    assert config.release_timezone == "Asia/Ho_Chi_Minh"
    assert config.release_deploy_line == "Render deploys branch deploy after Checks pass."


def test_load_returns_frozen_config(tmp_path: Path) -> None:
    config = flow_config.load(write(tmp_path, VALID))
    assert isinstance(config, FlowConfig)
    assert config.project_slug == "shop"
    assert config.release_deploy_line == ""
    with pytest.raises(AttributeError):
        config.project_slug = "other"  # type: ignore[misc]


def test_state_dir_expands_home(tmp_path: Path) -> None:
    config = flow_config.load(write(tmp_path, VALID))
    assert config.loop_state_dir == Path.home() / ".shop"


def test_default_path_is_the_file_next_to_the_module(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLOW_CONFIG", raising=False)
    assert flow_config.load().project_repo == "hungle-agilityio/ai-training"


def test_flow_config_variable_names_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLOW_CONFIG", str(write(tmp_path, VALID)))
    assert flow_config.load().project_repo == "acme/shop"


def test_explicit_path_wins_over_the_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLOW_CONFIG", str(tmp_path / "missing.toml"))
    assert flow_config.load(write(tmp_path, VALID)).project_repo == "acme/shop"


def test_missing_key_names_file_and_key(tmp_path: Path) -> None:
    path = write(tmp_path, VALID.replace('tmux_session = "shop-loop"\n', ""))
    with pytest.raises(FlowConfigError) as raised:
        flow_config.load(path)
    assert str(raised.value) == f"{path}: missing loop.tmux_session"


def test_missing_section_names_its_first_key(tmp_path: Path) -> None:
    path = write(tmp_path, VALID.split("[release]")[0])
    with pytest.raises(FlowConfigError, match=r"missing release\.timezone"):
        flow_config.load(path)


def test_unknown_key_names_file_and_key(tmp_path: Path) -> None:
    path = write(tmp_path, VALID.replace("[loop]\n", "[loop]\nnope = 1\n"))
    with pytest.raises(FlowConfigError) as raised:
        flow_config.load(path)
    assert str(raised.value) == f"{path}: unknown loop.nope"


def test_unknown_section_is_refused(tmp_path: Path) -> None:
    path = write(tmp_path, VALID + "\n[extra]\nx = 1\n")
    with pytest.raises(FlowConfigError, match=r"unknown extra"):
        flow_config.load(path)


@pytest.mark.parametrize(
    ("old", "new", "key"),
    [
        ('slug = "shop"', "slug = 3", "project.slug"),
        ('tmux_session = "shop-loop"', 'tmux_session = ["a"]', "loop.tmux_session"),
        (
            'setup_command = ["uv", "sync", "--frozen"]',
            'setup_command = "uv sync"',
            "loop.setup_command",
        ),
        ("alone_words = []", "alone_words = [1]", "loop.alone_words"),
        ('commands = [["uv", "run", "pytest"]]', 'commands = ["uv run pytest"]', "checks.commands"),
        ('commands = [["uv", "run", "pytest"]]', "commands = [[1]]", "checks.commands"),
        ('deploy_line = ""', "deploy_line = false", "release.deploy_line"),
    ],
)
def test_wrong_type_names_file_and_key(tmp_path: Path, old: str, new: str, key: str) -> None:
    path = write(tmp_path, VALID.replace(old, new))
    with pytest.raises(FlowConfigError) as raised:
        flow_config.load(path)
    assert str(raised.value).startswith(f"{path}: ")
    assert key in str(raised.value)


def test_missing_file_is_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(FlowConfigError, match="cannot read"):
        flow_config.load(tmp_path / "nope.toml")


def test_broken_toml_is_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(FlowConfigError, match="not valid TOML"):
        flow_config.load(write(tmp_path, "[project\n"))


def run_cli(*args: str, config: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/bin:/bin"}
    if config is not None:
        env["FLOW_CONFIG"] = str(config)
    return subprocess.run(
        [sys.executable, str(OPS / "flow_config.py"), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_cli_prints_a_value() -> None:
    done = run_cli("loop.tmux_session")
    assert (done.returncode, done.stdout) == (0, "rr-loop\n")


def test_cli_prints_a_list_as_words() -> None:
    done = run_cli("loop.setup_command")
    assert (done.returncode, done.stdout) == (0, "uv sync --frozen\n")


def test_cli_prints_commands_one_per_line_of_words() -> None:
    done = run_cli("checks.commands")
    assert done.returncode == 0
    assert done.stdout.count("\n") == 1  # one line, as the spec says


def test_cli_prints_an_empty_value_as_an_empty_line(tmp_path: Path) -> None:
    done = run_cli("release.deploy_line", config=write(tmp_path, VALID))
    assert (done.returncode, done.stdout) == (0, "\n")


def test_cli_unknown_key_exits_2_with_the_key() -> None:
    done = run_cli("loop.nope")
    assert done.returncode == 2
    assert "loop.nope" in done.stderr + done.stdout
    assert done.stdout == ""


def test_cli_broken_config_exits_2(tmp_path: Path) -> None:
    done = run_cli("loop.tmux_session", config=write(tmp_path, "[project]\n"))
    assert done.returncode == 2
    assert "missing" in done.stderr
