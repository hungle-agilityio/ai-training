"""The plugin code reads the flow config of a new project (.flow/) and of ReviewRadar (ops/).

Spec: specs/project-layout/spec.md (AC4 to AC7). Run from the app folder:
uv run pytest ../plugins/agent-flow/tests/test_layout_paths.py --no-cov -q
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tomllib
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
READER = next(
    path
    for path in (PROJECT / ".flow" / "loop" / "flow_config.py", PROJECT / "ops" / "flow_config.py")
    if path.is_file()
)
ROUTE = PLUGIN / "skills" / "create-issue" / "route_issue.py"
BLOCKED_TEST = "is a test that is already on main; fix the code, not the test"
FLOW_TOML = """\
[project]
repo = "acme/garden"
owner = "acme-owner"
app_dir = "."
display_name = "Garden"
slug = "garden"

[loop]
state_dir = "~/.garden"
tmux_session = "garden-loop"
launchd_label = "com.garden.loop"
setup_command = ["npm", "ci"]
alone_words = ["migrations/"]

[checks]
commands = [["bash", "scripts/check.sh"]]
ci_workflow = "Checks"
protected_test_dirs = ["tests"]

[release]
timezone = "Asia/Ho_Chi_Minh"
deploy_line = ""

[plugin]
id = "agent-flow@garden"
marketplace = "garden"

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


def load(path: Path, name: str) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDIT = load(PLUGIN / "hooks" / "before-edit-check.py", "before_edit_check_layout")
FINISH = load(PLUGIN / "hooks" / "before-finish-check.py", "before_finish_check_layout")
GITHUB = load(PLUGIN / "hooks" / "before-github-command-check.py", "before_github_layout")
REPORT = load(PLUGIN / "skills" / "build-verify-report" / "build_report.py", "build_report_layout")


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture
def garden(tmp_path: Path) -> Path:
    """A new project: .flow/flow.toml, the reader in .flow/loop/, no ops/, a test on main."""
    project = tmp_path / "garden"
    (project / ".flow" / "loop").mkdir(parents=True)
    shutil.copy(READER, project / ".flow" / "loop" / "flow_config.py")
    (project / ".flow" / "flow.toml").write_text(FLOW_TOML, encoding="utf-8")
    tests = project / "src" / "plants" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_plants.py").write_text("x = 1\n")
    git(project, "init", "-q", "-b", "main")
    git(project, "add", ".")
    git(project, "commit", "-q", "-m", "base")
    return project


def session(project: Path, **extra: str) -> dict[str, str]:
    return {"CLAUDE_PROJECT_DIR": str(project), "FLOW_LOOP": "1", **extra}


def route(project: Path, *paths: str, folder: Path | None = None) -> list[str]:
    body = (folder or project) / "body.md"
    body.write_text("## Files likely touched\n\n" + "".join(f"- `{p}`\n" for p in paths))
    env = {"PATH": os.environ["PATH"], "CLAUDE_PROJECT_DIR": str(project)}
    done = subprocess.run(
        [sys.executable, "-I", str(ROUTE), str(body)],
        capture_output=True,
        text=True,
        cwd=project,
        env=env,
        check=True,
    )
    return done.stdout.split()


# AC4: the hooks read .flow/flow.toml through the reader in .flow/loop/


def test_edit_hook_reads_the_new_layout(garden: Path) -> None:
    config = EDIT.flow_config(session(garden))
    assert config.project_repo == "acme/garden"
    assert EDIT.loader_path(garden, None) == garden / ".flow" / "loop" / "flow_config.py"


def test_finish_hook_runs_the_checks_of_the_new_layout(garden: Path) -> None:
    calls: list[list[str]] = []

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        calls.append(args)
        return 0, ""

    assert FINISH.evaluate({}, garden, session(garden), run) == []
    assert calls == [["bash", "scripts/check.sh"]]


def test_github_hook_allows_the_repository_of_the_new_layout(garden: Path) -> None:
    assert GITHUB.read_allowed(session(garden)) == "acme/garden"


def test_report_finds_the_project_and_test_folders_of_the_new_layout(garden: Path) -> None:
    assert REPORT.project_root(garden / "src" / "plants") == garden
    assert REPORT.config_file(garden) == garden / ".flow" / "flow.toml"


def test_a_named_config_still_wins(garden: Path, tmp_path: Path) -> None:
    other = tmp_path / "other.toml"
    other.write_text(FLOW_TOML.replace("acme/garden", "acme/other"), encoding="utf-8")
    env = session(garden, FLOW_CONFIG=str(other))
    assert GITHUB.read_allowed(env) == "acme/other"


# AC5: area:flow for paths.flow_dirs and the plugin folder


@pytest.mark.parametrize(
    "path",
    [".flow/loop/agent_tick.py", ".flow/plugin/hooks/x.py", "scripts/check.sh", "docs/specs/a.md"],
)
def test_route_gives_area_flow_for_flow_folders(garden: Path, path: str) -> None:
    assert route(garden, path) == ["area:flow", "agent:ready"]


@pytest.mark.parametrize("path", ["src/plants/views.py", "docs/architecture.md", "ops/x.py"])
def test_route_gives_area_app_outside_flow_folders(garden: Path, path: str) -> None:
    assert route(garden, path) == ["area:app", "agent:ready"]


def test_route_keeps_reviewradars_flow_folders(tmp_path: Path) -> None:
    if not (PROJECT / "ops" / "flow.toml").is_file():
        pytest.skip("ReviewRadar's layout only")
    for path, area in [
        ("ops/agent_tick.py", "area:flow"),
        ("specs/x/spec.md", "area:flow"),
        ("docs/learning/a.md", "area:flow"),
        ("../plugins/agent-flow/README.md", "area:flow"),
        ("reviews/services.py", "area:app"),
    ]:
        assert route(PROJECT, path, folder=tmp_path)[0] == area, path


# AC6: a tests folder at any depth is protected


def test_edit_protects_a_feature_test_on_main(garden: Path) -> None:
    rel = garden / "src" / "plants" / "tests" / "test_plants.py"
    found = EDIT.evaluate(str(rel), garden, session(garden), EDIT.real_run)
    assert found == [f"test_plants.py {BLOCKED_TEST}"]


def test_edit_allows_a_new_feature_test(garden: Path) -> None:
    rel = garden / "src" / "plants" / "tests" / "test_new.py"
    assert EDIT.evaluate(str(rel), garden, session(garden), EDIT.real_run) == []


# AC7: the same calls in this repository still read ops/flow.toml


def test_reviewradar_still_reads_ops_flow_toml() -> None:
    if not (PROJECT / "ops" / "flow.toml").is_file():
        pytest.skip("ReviewRadar's layout only")
    env = {"CLAUDE_PROJECT_DIR": str(PROJECT)}
    assert EDIT.config_path(PROJECT, None) == PROJECT / "ops" / "flow.toml"
    assert EDIT.loader_path(PROJECT, None) == PROJECT / "ops" / "flow_config.py"
    assert FINISH.config_path(PROJECT, None) == PROJECT / "ops" / "flow.toml"
    repo = tomllib.loads((PROJECT / "ops" / "flow.toml").read_text())["project"]["repo"]
    assert GITHUB.read_allowed(env) == repo.lower()
    assert REPORT.config_file(PROJECT) == PROJECT / "ops" / "flow.toml"
