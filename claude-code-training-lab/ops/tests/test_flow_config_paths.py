"""The flow config is found in either layout and has an optional [paths] table.

Spec: specs/project-layout/spec.md (AC1 to AC3). Run: pytest ops/tests/test_flow_config_paths.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from ops import flow_config
from ops.flow_config import FlowConfigError

OPS = Path(__file__).resolve().parents[1]
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
setup_command = ["npm", "ci"]
alone_words = []

[checks]
commands = [["bash", "scripts/check.sh"]]
ci_workflow = "Checks"
protected_test_dirs = ["tests"]

[release]
timezone = "Europe/Berlin"
deploy_line = ""
"""
NEW_PATHS = """
[paths]
loop_dir = ".flow/loop"
plugin_dir = ".flow/plugin"
intent_file = "docs/intent/{feature}.md"
specs_dir = "docs/specs"
spec_pr_dirs = ["docs/intent", "docs/specs"]
plans_dir = "docs/plans"
decisions_dir = "docs/decisions"
templates_dir = "docs/templates"
code_dirs = ["src"]
flow_dirs = [".flow/", ".claude/", ".github/", "docs/intent/", "docs/specs/", "scripts/"]
"""
REVIEWRADAR = {
    "loop_dir": "ops",
    "plugin_dir": "../plugins/agent-flow",
    "intent_file": "specs/{feature}/intent.md",
    "specs_dir": "specs",
    "spec_pr_dirs": "specs design",
    "plans_dir": "",
    "decisions_dir": ".claude/knowledge/decisions",
    "templates_dir": "docs/app/templates",
    "code_dirs": "reviews reviewradar",
    "flow_dirs": "ops/ .claude/ .github/ specs/ docs/learning/",
}
CLEAN_ENV = {"PATH": "/usr/bin:/bin"}


def new_project(root: Path, paths: str = NEW_PATHS) -> Path:
    """A project with the new layout: .flow/flow.toml and the reader in .flow/loop/."""
    loop = root / ".flow" / "loop"
    loop.mkdir(parents=True)
    shutil.copy(OPS / "flow_config.py", loop / "flow_config.py")
    (root / ".flow" / "flow.toml").write_text(VALID + paths, encoding="utf-8")
    return root


def run_reader(script: Path, key: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), key], capture_output=True, text=True, env=CLEAN_ENV
    )


def test_find_config_prefers_the_named_file(tmp_path: Path) -> None:
    named = tmp_path / "other.toml"
    found = flow_config.find_config(new_project(tmp_path), {"FLOW_CONFIG": str(named)})
    assert found == named


def test_find_config_takes_dot_flow_when_it_exists(tmp_path: Path) -> None:
    project = new_project(tmp_path)
    (project / "ops").mkdir()
    (project / "ops" / "flow.toml").write_text(VALID, encoding="utf-8")
    assert flow_config.find_config(project, {}) == project / ".flow" / "flow.toml"


def test_find_config_falls_back_to_ops(tmp_path: Path) -> None:
    assert flow_config.find_config(tmp_path, {}) == tmp_path / "ops" / "flow.toml"


def test_none_found_names_both_paths(tmp_path: Path) -> None:
    project = new_project(tmp_path)
    (project / ".flow" / "flow.toml").unlink()
    done = run_reader(project / ".flow" / "loop" / "flow_config.py", "project.repo")
    assert done.returncode == 2
    assert ".flow/flow.toml" in done.stderr
    assert "ops/flow.toml" in done.stderr


def test_project_of_knows_both_loop_folders(tmp_path: Path) -> None:
    assert flow_config.project_of(tmp_path / ".flow" / "loop") == tmp_path
    assert flow_config.project_of(tmp_path / "ops") == tmp_path


def test_missing_paths_take_reviewradars_layout(tmp_path: Path) -> None:
    path = tmp_path / "flow.toml"
    path.write_text(VALID, encoding="utf-8")
    config = flow_config.load(path)
    for key, value in REVIEWRADAR.items():
        assert flow_config.lookup(config, f"paths.{key}", "x") == value


def test_new_layout_values_are_read(tmp_path: Path) -> None:
    config = flow_config.load(new_project(tmp_path) / ".flow" / "flow.toml")
    assert config.paths_loop_dir == ".flow/loop"
    assert config.paths_plugin_dir == ".flow/plugin"
    assert config.paths_spec_pr_dirs == ("docs/intent", "docs/specs")
    assert config.paths_plans_dir == "docs/plans"
    assert config.paths_code_dirs == ("src",)


def test_one_missing_key_takes_its_default(tmp_path: Path) -> None:
    path = tmp_path / "flow.toml"
    path.write_text(VALID + '\n[paths]\nloop_dir = ".flow/loop"\n', encoding="utf-8")
    config = flow_config.load(path)
    assert config.paths_loop_dir == ".flow/loop"
    assert config.paths_decisions_dir == ".claude/knowledge/decisions"


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ('code_dirs = "src"', "paths.code_dirs must be a list of strings"),
        ("loop_dir = 3", "paths.loop_dir must be a string"),
        ('colour = "red"', "unknown paths.colour"),
    ],
)
def test_a_wrong_path_key_names_file_and_key(tmp_path: Path, line: str, message: str) -> None:
    path = tmp_path / "flow.toml"
    path.write_text(f"{VALID}\n[paths]\n{line}\n", encoding="utf-8")
    with pytest.raises(FlowConfigError) as caught:
        flow_config.load(path)
    assert str(caught.value) == f"{path}: {message}"


def test_reviewradar_flow_toml_paths_table_has_only_review_sensitive() -> None:
    data = tomllib.loads((OPS / "flow.toml").read_text(encoding="utf-8"))
    assert list(data["paths"]) == ["review_sensitive"]


@pytest.mark.parametrize(("key", "value"), sorted(REVIEWRADAR.items()))
def test_command_line_prints_reviewradars_default(key: str, value: str) -> None:
    done = run_reader(OPS / "flow_config.py", f"paths.{key}")
    assert done.returncode == 0, done.stderr
    assert done.stdout == f"{value}\n"


def test_reader_in_dot_flow_loop_reads_dot_flow_toml(tmp_path: Path) -> None:
    done = run_reader(
        new_project(tmp_path) / ".flow" / "loop" / "flow_config.py", "paths.code_dirs"
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout == "src\n"
