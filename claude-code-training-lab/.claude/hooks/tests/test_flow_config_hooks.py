"""The hooks read ops/flow.toml. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import json
import subprocess
import tomllib
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

HOOKS = Path(__file__).resolve().parents[1]
APP = HOOKS.parents[1]
FLOW_TOML = APP / "ops" / "flow.toml"
BLOCKED_TEST = "is a test that is already on main; fix the code, not the test"


def load(name: str) -> ModuleType:
    spec = util.spec_from_file_location(name.replace("-", "_") + "_flow", HOOKS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDIT = load("before-edit-check")
FINISH = load("before-finish-check")
GITHUB = load("before-github-command-check")


def toml_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return json.dumps(value)


def write_config(folder: Path, **changes: Any) -> Path:
    """A copy of ops/flow.toml with `section_key=value` changes."""
    data = tomllib.loads(FLOW_TOML.read_text())
    for dotted, value in changes.items():
        section, key = dotted.split("_", 1)
        data[section][key] = value
    lines: list[str] = []
    for section, values in data.items():
        lines.append(f"[{section}]")
        lines += [f"{key} = {toml_value(value)}" for key, value in values.items()]
    path = folder / "flow.toml"
    path.write_text("\n".join(lines) + "\n")
    return path


def recorder(calls: list[list[str]], failing: str = "") -> object:
    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        calls.append(args)
        return (1 if failing and failing in args else 0), "output"

    return run


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture
def lab(tmp_path: Path) -> Path:
    """A git root with a lab folder; a test under reviews/tests and one under app/tests on main."""
    git(tmp_path, "init", "-q", "-b", "main")
    lab_dir = tmp_path / "lab"
    for folder in ("reviews/tests", "app/tests"):
        (lab_dir / folder).mkdir(parents=True)
        (lab_dir / folder / "test_old.py").write_text("x = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    return lab_dir


# AC1: the finish hook runs checks.commands in order


def test_finish_runs_the_configured_commands_in_order(tmp_path: Path) -> None:
    commands = [["make", "lint"], ["make", "types"], ["make", "test"]]
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(write_config(tmp_path, checks_commands=commands))}
    calls: list[list[str]] = []
    assert FINISH.evaluate({}, tmp_path, env, recorder(calls)) == []
    assert calls == commands


def test_finish_reports_a_failing_configured_command(tmp_path: Path) -> None:
    config = write_config(tmp_path, checks_commands=[["npm", "test"]])
    env = {"REVIEWRADAR_LOOP": "1", "FLOW_CONFIG": str(config)}
    found = FINISH.evaluate({}, tmp_path, env, recorder([], failing="npm"))
    assert len(found) == 1 and "`npm test` failed" in found[0]


def test_finish_runs_todays_three_checks_from_the_committed_file(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    FINISH.evaluate({}, tmp_path, {"FLOW_LOOP": "1"}, recorder(calls))
    assert [args[2] for args in calls] == ["ruff", "mypy", "pytest"]


def test_finish_blocks_when_the_config_cannot_be_read(tmp_path: Path) -> None:
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(tmp_path / "missing.toml")}
    found = FINISH.evaluate({}, tmp_path, env, recorder([]))
    assert len(found) == 1 and "flow.toml" in found[0]


# AC2: the edit hook protects every folder of checks.protected_test_dirs


def edit(lab: Path, rel: str, env: dict[str, str]) -> list[str]:
    return EDIT.evaluate(str(lab / rel), lab, env, EDIT.real_run)  # type: ignore[no-any-return]


def test_edit_protects_a_configured_test_folder(lab: Path, tmp_path: Path) -> None:
    config = write_config(tmp_path, checks_protected_test_dirs=["app/tests"])
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(config)}
    assert edit(lab, "app/tests/test_old.py", env) == [f"test_old.py {BLOCKED_TEST}"]
    assert edit(lab, "reviews/tests/test_old.py", env) == []
    assert edit(lab, "app/tests/test_new.py", env) == []


def test_edit_protects_every_configured_folder(lab: Path, tmp_path: Path) -> None:
    config = write_config(tmp_path, checks_protected_test_dirs=["reviews/tests", "app/tests"])
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(config)}
    assert edit(lab, "app/tests/test_old.py", env)
    assert edit(lab, "reviews/tests/test_old.py", env)


def test_edit_keeps_the_allow_test_edit_escape(lab: Path, tmp_path: Path) -> None:
    config = write_config(tmp_path, checks_protected_test_dirs=["app/tests"])
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(config), "ALLOW_TEST_EDIT": "1"}
    assert edit(lab, "app/tests/test_old.py", env) == []


def test_edit_protects_reviews_tests_from_the_committed_file(lab: Path) -> None:
    found = edit(lab, "reviews/tests/test_old.py", {"FLOW_LOOP": "1"})
    assert found == [f"test_old.py {BLOCKED_TEST}"]


def test_edit_fails_closed_when_the_config_cannot_be_read(lab: Path, tmp_path: Path) -> None:
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(tmp_path / "missing.toml")}
    assert edit(lab, "reviews/tests/test_old.py", env)


# AC3: FLOW_LOOP=1 or REVIEWRADAR_LOOP=1 is loop mode in every hook that checks it


@pytest.mark.parametrize("name", ["FLOW_LOOP", "REVIEWRADAR_LOOP"])
def test_edit_hook_takes_either_variable_as_loop_mode(lab: Path, name: str) -> None:
    assert edit(lab, ".claude/settings.json", {name: "1"})


@pytest.mark.parametrize("name", ["FLOW_LOOP", "REVIEWRADAR_LOOP"])
def test_finish_hook_takes_either_variable_as_loop_mode(tmp_path: Path, name: str) -> None:
    calls: list[list[str]] = []
    FINISH.evaluate({}, tmp_path, {name: "1"}, recorder(calls))
    assert calls


def test_hooks_do_nothing_without_either_variable(lab: Path, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    assert FINISH.evaluate({}, tmp_path, {"FLOW_LOOP": "0"}, recorder(calls)) == []
    assert calls == []
    assert edit(lab, ".claude/settings.json", {}) == []


@pytest.mark.parametrize("name", ["FLOW_LOOP", "REVIEWRADAR_LOOP"])
def test_github_hook_takes_either_variable_as_loop_mode(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    for other in ("FLOW_LOOP", "REVIEWRADAR_LOOP"):
        monkeypatch.delenv(other, raising=False)
    assert GITHUB.is_loop() is False
    monkeypatch.setenv(name, "1")
    assert GITHUB.is_loop() is True


def test_every_hook_naming_the_old_variable_also_takes_flow_loop() -> None:
    for hook in HOOKS.glob("*.py"):
        text = hook.read_text()
        if "REVIEWRADAR_LOOP" in text:
            assert "FLOW_LOOP" in text, hook.name


# AC5: github-allowed-repo.txt stays the guard's source and matches project.repo


def test_allowed_repo_file_matches_project_repo() -> None:
    lines = (HOOKS / "github-allowed-repo.txt").read_text().splitlines()
    first = next(line.strip() for line in lines if line.strip() and not line.startswith("#"))
    repo = tomllib.loads(FLOW_TOML.read_text())["project"]["repo"]
    assert first == repo
    assert GITHUB.read_allowed() == repo.lower()
