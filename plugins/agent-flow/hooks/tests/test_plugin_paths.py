"""The hooks run from the plugin: they find the project through CLAUDE_PROJECT_DIR.

Run: uv run pytest ../plugins/agent-flow/hooks/tests --no-cov -q (from the app folder)
"""

import json
import os
import shutil
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

HOOKS = Path(__file__).resolve().parents[1]
APP = Path(os.environ["CLAUDE_PROJECT_DIR"])
REPO = "hungle-agilityio/ai-training"


def load(name: str) -> ModuleType:
    spec = util.spec_from_file_location(name.replace("-", "_") + "_paths", HOOKS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDIT = load("before-edit-check")
FINISH = load("before-finish-check")
GITHUB = load("before-github-command-check")
PUBLISH = load("before-artifact-publish")


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


def project(folder: Path, repo: str = REPO, protected: str = "app/tests") -> Path:
    """A project folder with its own ops/flow.toml and a copy of ops/flow_config.py."""
    (folder / "ops").mkdir(parents=True)
    shutil.copy(APP / "ops" / "flow_config.py", folder / "ops" / "flow_config.py")
    text = (APP / "ops" / "flow.toml").read_text()
    text = text.replace(f'repo = "{REPO}"', f'repo = "{repo}"')
    text = text.replace(
        'protected_test_dirs = ["reviews/tests"]', f'protected_test_dirs = ["{protected}"]'
    )
    text = text.replace(
        'commands = [\n    ["uv", "run", "ruff", "check", "."],',
        'commands = [\n    ["own-check"],\n    ["uv", "run", "ruff", "check", "."],',
    )
    (folder / "ops" / "flow.toml").write_text(text)
    return folder


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git root holding a project folder `lab` with a test on main under app/tests."""
    git(tmp_path, "init", "-q", "-b", "main")
    lab = project(tmp_path / "lab")
    (lab / "app" / "tests").mkdir(parents=True)
    (lab / "app" / "tests" / "test_old.py").write_text("x = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def real(args: list[str], cwd: Path) -> tuple[int, str]:
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout


def run_hook(
    name: str, payload: dict[str, Any], env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(HOOKS / f"{name}.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", **env},
        check=False,
    )


# AC2: flow.toml and flow_config.py come from the project, not from the hook's folder


def test_no_hook_locates_files_from_its_own_folder() -> None:
    for hook in HOOKS.glob("*.py"):
        assert "parents[2]" not in hook.read_text(), hook.name
        assert "github-allowed-repo" not in hook.read_text(), hook.name


def test_edit_check_reads_the_protected_tests_of_the_project_dir(repo: Path) -> None:
    lab = repo / "lab"
    env = {"FLOW_LOOP": "1", "CLAUDE_PROJECT_DIR": str(lab)}

    blocked = EDIT.evaluate(str(lab / "app" / "tests" / "test_old.py"), lab, env, real)

    assert blocked == ["test_old.py is a test that is already on main; fix the code, not the test"]


def test_edit_check_falls_back_to_the_payload_cwd(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    lab = repo / "lab"
    env = {"FLOW_LOOP": "1"}

    blocked = EDIT.evaluate(str(lab / "app" / "tests" / "test_old.py"), lab, env, real)

    assert blocked and "already on main" in blocked[0]


def test_edit_check_without_flow_toml_keeps_todays_message(tmp_path: Path) -> None:
    env = {"FLOW_LOOP": "1", "CLAUDE_PROJECT_DIR": str(tmp_path)}

    blocked = EDIT.evaluate(str(tmp_path / "app.py"), tmp_path, env, real)

    assert len(blocked) == 1
    assert blocked[0].startswith("app.py not checked: ops/flow.toml could not be read (")


def test_finish_check_runs_the_commands_of_the_project_dir(repo: Path) -> None:
    calls: list[list[str]] = []

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        calls.append(args)
        return 0, ""

    lab = repo / "lab"
    env = {"FLOW_LOOP": "1", "CLAUDE_PROJECT_DIR": str(lab)}

    assert FINISH.evaluate({}, lab, env, run) == []
    assert calls[0] == ["own-check"]


def test_finish_check_without_flow_toml_keeps_todays_message(tmp_path: Path) -> None:
    env = {"FLOW_LOOP": "1", "CLAUDE_PROJECT_DIR": str(tmp_path)}

    problems = FINISH.evaluate({}, tmp_path, env, real)

    assert len(problems) == 1
    assert problems[0].startswith("the checks of ops/flow.toml could not be read (")


# AC3: the allowed repository is project.repo of flow.toml


def test_the_allowed_repo_file_is_gone() -> None:
    assert not (HOOKS / "github-allowed-repo.txt").exists()
    assert not (APP / ".claude" / "hooks").exists()


def test_the_guard_takes_the_repo_from_flow_toml(tmp_path: Path) -> None:
    lab = project(tmp_path, repo="Someone/Other-Repo")

    assert GITHUB.read_allowed({"CLAUDE_PROJECT_DIR": str(lab)}) == "someone/other-repo"


def test_the_guard_falls_back_to_the_payload_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    lab = project(tmp_path, repo="someone/other")

    assert GITHUB.read_allowed({}, str(lab)) == "someone/other"


def test_with_todays_flow_toml_the_guard_allows_what_it_allows_today() -> None:
    allowed = GITHUB.read_allowed({"CLAUDE_PROJECT_DIR": str(APP)})

    assert allowed == REPO
    assert GITHUB.check_command(f"gh issue view 1 --repo {REPO}", allowed, False) == []
    assert GITHUB.check_command("gh issue view 1 --repo other/repo", allowed, False)


def test_the_guard_blocks_when_flow_toml_cannot_be_read(tmp_path: Path) -> None:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": f"gh issue view 1 --repo {REPO}"},
        "cwd": str(tmp_path),
    }

    done = run_hook("before-github-command-check", payload, {"CLAUDE_PROJECT_DIR": str(tmp_path)})

    assert done.returncode == 2
    assert "the guard could not check this command" in done.stderr


def test_the_guard_hook_allows_the_repo_of_the_project(tmp_path: Path) -> None:
    lab = project(tmp_path)
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": f"gh issue view 1 --repo {REPO}"},
        "cwd": str(lab),
    }

    done = run_hook("before-github-command-check", payload, {"CLAUDE_PROJECT_DIR": str(lab)})

    assert done.returncode == 0, done.stderr


# AC4: in loop mode the plugin source and the marketplace are protected too


@pytest.mark.parametrize(
    "rel",
    [
        "plugins/agent-flow/hooks/before-edit-check.py",
        "plugins/other/README.md",
        ".claude-plugin/marketplace.json",
        "Plugins/agent-flow/x.py",
    ],
)
def test_loop_refuses_the_plugin_source_and_marketplace(repo: Path, rel: str) -> None:
    env = {"FLOW_LOOP": "1", "CLAUDE_PROJECT_DIR": str(repo / "lab")}

    blocked = EDIT.evaluate(str(repo / rel), repo / "lab", env, real)

    name = Path(rel).name
    assert blocked == [
        f"{name} is part of the flow plugin; the loop never changes its own rules, ask the user"
    ]


def test_a_plugins_folder_inside_the_app_is_not_the_plugin_source(repo: Path) -> None:
    env = {"FLOW_LOOP": "1", "CLAUDE_PROJECT_DIR": str(repo / "lab")}

    assert EDIT.evaluate(str(repo / "lab" / "plugins" / "x.py"), repo / "lab", env, real) == []


def test_outside_loop_mode_the_plugin_source_is_not_guarded(repo: Path) -> None:
    env = {"CLAUDE_PROJECT_DIR": str(repo / "lab")}

    assert (
        EDIT.evaluate(str(repo / "plugins" / "agent-flow" / "x.py"), repo / "lab", env, real) == []
    )


# The publish hook finds the sharing gate in the plugin, else in the project


def test_the_publish_hook_finds_the_gate_in_the_project(tmp_path: Path) -> None:
    gate = tmp_path / ".claude" / "skills" / "share-report" / "share_gate.py"
    gate.parent.mkdir(parents=True)
    gate.write_text("")

    found = PUBLISH.gate_path({"CLAUDE_PROJECT_DIR": str(tmp_path)}, tmp_path)

    assert found in (gate, HOOKS.parent / "skills" / "share-report" / "share_gate.py")
    if not (HOOKS.parent / "skills" / "share-report" / "share_gate.py").is_file():
        assert found == gate


# hooks.json registers the events and matchers of the old settings.json block


def test_hooks_json_registers_the_same_events_and_matchers() -> None:
    data = json.loads((HOOKS / "hooks.json").read_text())["hooks"]
    seen = {
        (event, group.get("matcher", "")): [hook["command"] for hook in group["hooks"]]
        for event, groups in data.items()
        for group in groups
    }

    def cmd(name: str) -> str:
        return f'/usr/bin/env python3 -I "${{CLAUDE_PLUGIN_ROOT}}/hooks/{name}.py"'

    assert seen == {
        ("PreToolUse", "Bash"): [
            cmd("before-github-command-check"),
            cmd("before-commit-check"),
            cmd("before-skill-script-allow"),
        ],
        ("PreToolUse", "Edit|Write|NotebookEdit"): [cmd("before-edit-check")],
        ("PreToolUse", "Artifact"): [cmd("before-artifact-publish")],
        ("Stop", ""): [cmd("before-finish-check")],
        ("PostToolUse", "Edit|Write"): [cmd("after-edit-format")],
    }


def test_settings_turn_the_plugin_on_and_hold_no_hooks() -> None:
    settings = json.loads((APP / ".claude" / "settings.json").read_text())

    assert "hooks" not in settings
    assert settings["enabledPlugins"] == {"agent-flow@ai-training": True}
    assert settings["extraKnownMarketplaces"] == {
        "ai-training": {"source": {"source": "github", "repo": REPO}}
    }
