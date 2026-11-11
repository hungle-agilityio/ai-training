"""The loop scripts run from any folder: ops/ in ReviewRadar, .flow/loop/ in a new project.

Spec: specs/project-layout/spec.md (AC12 to AC15). Run: pytest ops/tests/test_loop_location.py
"""

from __future__ import annotations

import json
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ops import check_plugin_version, pinned_tests

OPS = Path(__file__).resolve().parents[1]
LAB = OPS.parent
SYSTEM_PATH = "/usr/bin:/bin"
SCRIPTS = (
    "flow_config.py",
    "agent_tick.py",
    "release.py",
    "epic_branch.py",
    "epic_pull_request.py",
    "epic_rescue.py",
    "check_plugin_version.py",
    "pinned_tests.py",
    "flow-value.sh",
    "start-loop.sh",
    "install-launchd.sh",
)
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
{plugin}
[paths]
loop_dir = ".flow/loop"
plugin_dir = ".flow/plugin"
intent_file = "docs/intent/{{feature}}.md"
specs_dir = "docs/specs"
spec_pr_dirs = ["docs/intent", "docs/specs"]
plans_dir = "docs/plans"
decisions_dir = "docs/decisions"
templates_dir = "docs/templates"
code_dirs = ["src"]
flow_dirs = [".flow/", ".claude/", ".github/", "docs/intent/", "docs/specs/", "scripts/"]
"""
PLUGIN = '\n[plugin]\nid = "agent-flow@garden"\nmarketplace = "garden"\n'


def new_project(root: Path, plugin: str = PLUGIN) -> Path:
    """A project with the new layout and no ops/: the loop scripts in .flow/loop/."""
    loop = root / ".flow" / "loop"
    loop.mkdir(parents=True)
    for name in SCRIPTS:
        shutil.copy2(OPS / name, loop / name)
    (root / ".flow" / "flow.toml").write_text(FLOW_TOML.format(plugin=plugin), encoding="utf-8")
    return root


def fake(bin_dir: Path, name: str, calls: Path, tail: str = "") -> None:
    script = bin_dir / name
    script.write_text(f'#!/bin/bash\nprintf "%s\\n" "{name}" "$@" "--" >> "{calls}"\n{tail}\n')
    script.chmod(0o755)


@pytest.fixture
def sandbox(tmp_path: Path) -> dict[str, Path]:
    home, bin_dir = tmp_path / "home", tmp_path / "bin"
    home.mkdir()
    bin_dir.mkdir()
    calls = tmp_path / "calls.txt"
    fake(bin_dir, "tmux", calls, 'if [ "$1" = has-session ]; then exit 1; fi')
    fake(bin_dir, "uv", calls)
    fake(bin_dir, "launchctl", calls)
    return {"home": home, "bin": bin_dir, "calls": calls}


def run_script(script: Path, box: dict[str, Path], *args: str) -> str:
    env = {"HOME": str(box["home"]), "PATH": f"{box['bin']}:{SYSTEM_PATH}"}
    done = subprocess.run(
        ["/bin/bash", str(script), *args], env=env, capture_output=True, text=True, check=False
    )
    assert done.returncode == 0, done.stderr
    return done.stdout


def calls_of(box: dict[str, Path]) -> list[list[str]]:
    words = box["calls"].read_text().splitlines()
    found: list[list[str]] = []
    current: list[str] = []
    for word in words:
        if word == "--":
            found.append(current)
            current = []
        else:
            current.append(word)
    return found


def tick_line(folder: str) -> str:
    return (
        "caffeinate -i bash -c 'while true; do date; uv run python "
        f"{folder}/agent_tick.py; sleep 300; done'"
    )


# AC12: the shell scripts find the project and the scripts beside them


def test_flow_value_reads_dot_flow_toml(tmp_path: Path) -> None:
    loop = new_project(tmp_path) / ".flow" / "loop"
    done = subprocess.run(
        ["bash", "-c", f'source "{loop / "flow-value.sh"}"; flow_value loop.tmux_session'],
        capture_output=True,
        text=True,
        env={"PATH": SYSTEM_PATH, "HOME": str(tmp_path)},
        check=True,
    )
    assert done.stdout == "garden-loop\n"


def test_start_loop_runs_the_tick_beside_it(tmp_path: Path, sandbox: dict[str, Path]) -> None:
    project = new_project(tmp_path / "garden")
    out = run_script(project / ".flow" / "loop" / "start-loop.sh", sandbox)
    calls = calls_of(sandbox)
    new_session = ["tmux", "new-session", "-d", "-s", "garden-loop", "-c", str(project)]
    assert new_session + [tick_line(".flow/loop")] in calls
    assert ["uv", "run", "python", ".flow/loop/agent_tick.py", "started"] in calls
    assert "Loop started in tmux session garden-loop" in out


def test_start_loop_names_the_settings_in_the_loop_folder(
    tmp_path: Path, sandbox: dict[str, Path]
) -> None:
    project = new_project(tmp_path / "garden")
    (project / ".flow" / "loop" / "agent.env").write_text("NTFY_TOPIC=garden-topic\n")
    out = run_script(project / ".flow" / "loop" / "start-loop.sh", sandbox)
    assert "settings: .flow/loop/agent.env" in out
    assert "https://ntfy.sh/garden-topic" in out


def test_start_loop_of_reviewradar_is_unchanged(sandbox: dict[str, Path]) -> None:
    run_script(OPS / "start-loop.sh", sandbox)
    calls = calls_of(sandbox)
    assert ["tmux", "new-session", "-d", "-s", "rr-loop", "-c", str(LAB), tick_line("ops")] in calls
    assert ["uv", "run", "python", "ops/agent_tick.py", "started"] in calls


def test_install_launchd_points_at_the_start_script_beside_it(
    tmp_path: Path, sandbox: dict[str, Path]
) -> None:
    project = new_project(tmp_path / "garden")
    loop = project / ".flow" / "loop"
    out = run_script(loop / "install-launchd.sh", sandbox)
    plist = sandbox["home"] / "Library" / "LaunchAgents" / "com.garden.loop.plist"
    data = plistlib.loads(plist.read_bytes())
    assert data["ProgramArguments"] == ["/bin/bash", str(loop / "start-loop.sh")]
    assert data["WorkingDirectory"] == str(project)
    assert "remove it with: .flow/loop/install-launchd.sh --remove" in out


def test_install_launchd_message_of_reviewradar_is_unchanged(sandbox: dict[str, Path]) -> None:
    out = run_script(OPS / "install-launchd.sh", sandbox)
    assert "remove it with: ops/install-launchd.sh --remove" in out


# AC13: the Python scripts run from .flow/loop/ with no ops package


def describe(project: Path) -> dict[str, object]:
    code = (
        "import json, sys\n"
        f"sys.path.insert(0, {str(project / '.flow' / 'loop')!r})\n"
        "import agent_tick, release, epic_pull_request, check_plugin_version, pinned_tests\n"
        "print(json.dumps({\n"
        "  'settings': agent_tick.REPO_ENV_NAME,\n"
        "  'release_root': str(release.PROJECT_ROOT),\n"
        "  'plugin_dir': check_plugin_version.PLUGIN_DIR,\n"
        "  'test_roots': list(pinned_tests.TEST_ROOTS),\n"
        "  'app_folders': list(pinned_tests.APP_FOLDERS),\n"
        "  'app_prefix': pinned_tests.APP_PREFIX,\n"
        "}))\n"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
        cwd=project,
        env={"PATH": SYSTEM_PATH, "HOME": str(project)},
        check=True,
    )
    loaded: dict[str, object] = json.loads(done.stdout)
    return loaded


def test_python_scripts_load_from_dot_flow_loop(tmp_path: Path) -> None:
    project = new_project(tmp_path / "garden")
    assert describe(project) == {
        "settings": ".flow/loop/agent.env",
        "release_root": str(project),
        "plugin_dir": ".flow/plugin/",
        "test_roots": ["tests", ".flow/loop/tests", ".flow/plugin"],
        "app_folders": ["src/"],
        "app_prefix": "",
    }


def test_a_missing_plugin_key_names_dot_flow_toml(tmp_path: Path) -> None:
    project = new_project(tmp_path / "garden", plugin="")
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(project / '.flow' / 'loop')!r})\n"
        "import agent_tick\n"
        "agent_tick.require_plugin_keys()\n"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
        env={"PATH": SYSTEM_PATH, "HOME": str(project)},
        check=False,
    )
    assert done.returncode != 0
    assert ".flow/flow.toml: missing plugin.id" in done.stderr


def test_pinned_tests_runs_as_a_script_from_dot_flow_loop(tmp_path: Path) -> None:
    project = new_project(tmp_path / "garden")
    tests = project / "src" / "plants" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_plants.py").write_text("def test_water_plants():\n    assert True\n")
    body = tmp_path / "body.md"
    body.write_text(
        "Change `test_water_plants`.\n\n## Files likely touched\n\n- `src/plants/x.py`\n"
    )
    done = subprocess.run(
        [sys.executable, str(project / ".flow" / "loop" / "pinned_tests.py"), str(body)],
        capture_output=True,
        text=True,
        cwd=project,
        env={"PATH": SYSTEM_PATH, "HOME": str(project)},
        check=True,
    )
    assert (
        done.stdout
        == "- `src/plants/tests/test_plants.py::test_water_plants`: names test_water_plants\n"
    )


# AC14 and AC15: ReviewRadar's values are today's


def test_check_plugin_version_reads_reviewradars_plugin_folder() -> None:
    assert check_plugin_version.PLUGIN_DIR == "plugins/agent-flow/"
    assert check_plugin_version.MANIFEST == "plugins/agent-flow/.claude-plugin/plugin.json"


def test_pinned_tests_keeps_reviewradars_roots() -> None:
    assert pinned_tests.TEST_ROOTS == ("reviews/tests", "ops/tests", "../plugins/agent-flow")
    assert pinned_tests.APP_FOLDERS == ("reviews/", "reviewradar/")
    assert pinned_tests.APP_PREFIX == "claude-code-training-lab/"
    assert pinned_tests.PROJECT == LAB
