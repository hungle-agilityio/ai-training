"""#526: epic_pull_request reads the guarded-files rule from the plugin's guarded_paths.py.

Rows M4 (no list of its own), M5 (fails closed), M6 and M7 (guard_paths), M8 (parity with the
edit hook and the plugin version).
"""

from __future__ import annotations

import json
import subprocess
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

from ops import epic_pull_request

OPS = Path(__file__).resolve().parents[1]
PLUGIN = OPS.parent.parent / "plugins" / "agent-flow"
HOOK = PLUGIN / "hooks" / "before-edit-check.py"
GUARDED_PATHS = PLUGIN / "hooks" / "guarded_paths.py"
EPIC_FILE = OPS / "epic_pull_request.py"
TEST_DIRS = [("reviews", "tests")]
LAB = "claude-code-training-lab/"
OLD_LISTS = ("GUARD_DIRS", "GUARD_NAMES", "PLUGIN_ROOTS", "GATE_FILES")
PARITY_PATHS = [
    ".claude/rules/git.md",
    ".github/workflows/checks.yml",
    ".mcp.json",
    "ops/flow.toml",
    ".flow/flow.toml",
    "plugins/agent-flow/hooks/hooks.json",
    ".claude-plugin/marketplace.json",
    "pyproject.toml",
    "uv.lock",
    "reviews/conftest.py",
    "reviews/services.py",
    "ops/agent_tick.py",
]
MAIN_PLUGIN_VERSION = (1, 0, 24)


def load_file(name: str, path: Path) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fresh_epic_module(name: str = "epic_pull_request_fresh") -> ModuleType:
    """Import ops/epic_pull_request.py again, so a load at import time sees the environment."""
    return load_file(name, EPIC_FILE)


def config_with_plugin_dir(tmp_path: Path, plugin_dir: Path) -> Path:
    """A copy of ops/flow.toml whose paths.plugin_dir is `plugin_dir` (absolute)."""
    text = (OPS / "flow.toml").read_text()
    assert "\n[paths]\n" in text and "plugin_dir" not in text
    named = tmp_path / "flow.toml"
    named.write_text(text.replace("\n[paths]\n", f'\n[paths]\nplugin_dir = "{plugin_dir}"\n', 1))
    return named


# M4: no list of its own; `guarded` follows guarded_kind


@pytest.mark.parametrize("name", OLD_LISTS)
def test_epic_pull_request_defines_no_guard_list_of_its_own(name: str) -> None:
    """M4."""
    assert not hasattr(epic_pull_request, name)


@pytest.mark.parametrize(
    "path",
    [
        ".claude/rules/git.md",
        "x/.github/workflows/checks.yml",
        ".mcp.json",
        "ops/flow.toml",
        ".flow/flow.toml",
        "plugins/agent-flow/hooks/hooks.json",
        ".claude-plugin/marketplace.json",
        "pyproject.toml",
        "reviews/conftest.py",
        "reviews/services.py",
        "ops/agent_tick.py",
        "Plugins/Agent-Flow/x.py",
        "app/plugins/x.py",
    ],
)
def test_guarded_follows_guarded_kind(path: str) -> None:
    """M4."""
    parts = tuple(part.casefold() for part in path.split("/") if part)
    kind = load_file("guarded_paths_epic", GUARDED_PATHS).guarded_kind(parts)
    assert epic_pull_request.guarded("M", path, []) is (kind is not None)


def test_guarded_keeps_the_test_folder_rule() -> None:
    """M4: a changed test under a protected folder is guarded, an added one is not."""
    assert epic_pull_request.guarded("M", "reviews/tests/unit/test_a.py", TEST_DIRS) is True
    assert epic_pull_request.guarded("A", "reviews/tests/unit/test_a.py", TEST_DIRS) is False
    assert epic_pull_request.guarded("M", "reviews/tests/unit/test_a.py", []) is False


# M5: fails closed when the module cannot be found or loaded


def test_guarded_is_true_for_every_path_when_the_module_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M5: assumes FLOW_CONFIG names a flow config whose paths.plugin_dir has no module."""
    empty = tmp_path / "no-plugin-here"
    empty.mkdir()
    monkeypatch.setenv("FLOW_CONFIG", str(config_with_plugin_dir(tmp_path, empty)))
    module = fresh_epic_module()
    assert module.guarded("M", "reviews/services.py", []) is True
    assert module.guarded("A", "ops/agent_tick.py", TEST_DIRS) is True


def test_guarded_is_true_when_the_plugin_folder_does_not_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M5."""
    monkeypatch.setenv("FLOW_CONFIG", str(config_with_plugin_dir(tmp_path, tmp_path / "nope")))
    assert fresh_epic_module("epic_pull_request_nofolder").guarded("M", "reviews/services.py", [])


def test_guarded_is_true_when_the_module_cannot_be_loaded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M5: a broken guarded_paths.py is also a failed load."""
    plugin = tmp_path / "plugin"
    (plugin / "hooks").mkdir(parents=True)
    (plugin / "hooks" / "guarded_paths.py").write_text("def broken(:\n")
    monkeypatch.setenv("FLOW_CONFIG", str(config_with_plugin_dir(tmp_path, plugin)))
    assert fresh_epic_module("epic_pull_request_broken").guarded("M", "reviews/services.py", [])


def test_guarded_is_true_when_the_module_holds_no_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M5: a guarded_paths.py without guarded_kind is also a failed load."""
    plugin = tmp_path / "plugin"
    (plugin / "hooks").mkdir(parents=True)
    (plugin / "hooks" / "guarded_paths.py").write_text("PLUGIN_DIRS = {'plugins'}\n")
    monkeypatch.setenv("FLOW_CONFIG", str(config_with_plugin_dir(tmp_path, plugin)))
    assert fresh_epic_module("epic_pull_request_norule").guarded("M", "reviews/services.py", [])


def test_guarded_is_true_when_the_rule_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M5: a guarded_kind that raises guards the file, guard_paths does not raise."""
    plugin = tmp_path / "plugin"
    (plugin / "hooks").mkdir(parents=True)
    source = "def guarded_kind(parts):\n    raise ValueError('broken rule')\n"
    (plugin / "hooks" / "guarded_paths.py").write_text(source)
    monkeypatch.setenv("FLOW_CONFIG", str(config_with_plugin_dir(tmp_path, plugin)))
    module = fresh_epic_module("epic_pull_request_raises")
    assert module.guard_paths("M\treviews/services.py\n", []) == ["reviews/services.py"]


def test_guard_paths_lists_every_changed_file_when_the_module_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M5: the section lists every changed file, it does not raise."""
    empty = tmp_path / "no-plugin-here"
    empty.mkdir()
    monkeypatch.setenv("FLOW_CONFIG", str(config_with_plugin_dir(tmp_path, empty)))
    module = fresh_epic_module("epic_pull_request_section")
    status = "M\treviews/services.py\nA\tops/new.py\n"
    assert module.guard_paths(status, ["reviews/tests"]) == ["reviews/services.py", "ops/new.py"]


# M6, M7: the section of the pull request


def test_guard_paths_lists_a_changed_flow_toml() -> None:
    """M6."""
    status = f"M\t{LAB}ops/flow.toml\n"
    assert epic_pull_request.guard_paths(status, ["reviews/tests"]) == [f"{LAB}ops/flow.toml"]


def test_guard_paths_of_an_unguarded_change_is_empty() -> None:
    """M7."""
    status = f"M\t{LAB}reviews/services.py\n"
    assert epic_pull_request.guard_paths(status, ["reviews/tests"]) == []
    assert epic_pull_request.guard_paths("M\treviews/services.py\n", ["reviews/tests"]) == []


# M8: parity with the edit hook, and the plugin version


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.mark.parametrize("path", PARITY_PATHS)
def test_the_hook_refuses_exactly_what_the_epic_section_lists(tmp_path: Path, path: str) -> None:
    """M8: loop mode, no allowed edits, against epic_pull_request.guarded("M", path, [])."""
    git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("x\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    hook = load_file("edit_check_parity", HOOK)
    env = {"FLOW_LOOP": "1", "FLOW_CONFIG": str(OPS / "flow.toml")}
    problems = hook.evaluate(str(tmp_path / path), tmp_path, env, hook.real_run, "Edit", {})
    assert bool(problems) is epic_pull_request.guarded("M", path, [])


def test_the_plugin_version_is_above_the_one_on_main() -> None:
    """M8: AC8, plugin.json is above 1.0.24 (check_plugin_version.py passes in CI)."""
    data = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    version = tuple(int(part) for part in data["version"].split("."))
    assert version > MAIN_PLUGIN_VERSION
