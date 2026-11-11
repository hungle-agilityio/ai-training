"""`bootstrap.py --stack` writes the stack-agnostic layout of a new project.

Spec: specs/project-layout/spec.md (AC16 to AC24). Run: pytest ops/tests/test_bootstrap_layout.py
"""

from __future__ import annotations

import json
import re
import stat
import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap

REPO = "acme/garden"
STACKS = ("python", "node", "other")
ROOT_ENTRIES = {
    ".claude",
    ".claude-plugin",
    ".env.example",
    ".flow",
    ".github",
    ".gitignore",
    "CLAUDE.md",
    "README.md",
    "docs",
    "scripts",
    "src",
}
OLD_WORDS = re.compile(r"ai-training|reviewradar|ReviewRadar|claude-code-training-lab|reviews/")
NEW_PATHS = {
    "loop_dir": ".flow/loop",
    "plugin_dir": ".flow/plugin",
    "intent_file": "docs/intent/{feature}.md",
    "specs_dir": "docs/specs",
    "spec_pr_dirs": ["docs/intent", "docs/specs"],
    "plans_dir": "docs/plans",
    "decisions_dir": "docs/decisions",
    "templates_dir": "docs/templates",
    "code_dirs": ["src"],
    "flow_dirs": [".flow/", ".claude/", ".github/", "docs/intent/", "docs/specs/", "scripts/"],
}
Run = Callable[..., int]


@pytest.fixture
def target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    path = tmp_path / "garden"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{REPO}.git"], cwd=path, check=True
    )
    return path


@pytest.fixture
def run(target: Path) -> Run:
    def call(*extra: str) -> int:
        argv = [
            "--target", str(target), "--repo", REPO, "--owner", "acme-owner",
            "--name", "Garden", "--slug", "garden", "--ntfy-topic", "garden-test", "--no-labels",
        ]  # fmt: skip
        return bootstrap.main([*argv, *extra])

    return call


def files_of(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]


def flow_toml(target: Path) -> dict[str, dict[str, object]]:
    return tomllib.loads((target / ".flow" / "flow.toml").read_text())


# AC16: --stack, and --app-dir must be .


def test_app_dir_other_than_dot_stops_before_writing(
    run: Run, target: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("--stack", "python", "--app-dir", "app") == 2
    assert "--app-dir 'app'" in capsys.readouterr().err
    assert files_of(target) == []


def test_unknown_stack_is_refused(run: Run, target: Path) -> None:
    with pytest.raises(SystemExit):
        run("--stack", "ruby")
    assert files_of(target) == []


def test_app_dir_dot_is_accepted(run: Run, target: Path) -> None:
    assert run("--stack", "node", "--app-dir", ".") == 0
    assert (target / ".flow" / "flow.toml").is_file()


# AC17: exactly the layout, a README in each empty folder


@pytest.mark.parametrize("stack", STACKS)
def test_root_holds_only_the_layout(run: Run, target: Path, stack: str) -> None:
    assert run("--stack", stack) == 0
    entries = {p.name for p in target.iterdir()} - {".git"}
    expected = ROOT_ENTRIES | ({"pyproject.toml"} if stack == "python" else set())
    assert entries == expected


def test_empty_folders_get_a_one_line_readme(run: Run, target: Path) -> None:
    run("--stack", "other")
    for folder in ("docs/intent", "docs/plans", "src"):
        text = (target / folder / "README.md").read_text()
        assert text.count("\n") == 1 and text.strip()
    for folder in ("docs/specs", "docs/decisions", "docs/templates"):
        assert any((target / folder).rglob("*.md"))
    assert (target / "docs" / "architecture.md").is_file()


# AC18: loop scripts, plugin and marketplace


def test_loop_scripts_are_copied_without_bootstrap_and_tests(run: Run, target: Path) -> None:
    run("--stack", "python")
    loop = {p.name for p in (target / ".flow" / "loop").iterdir()}
    assert {"agent_tick.py", "flow_config.py", "start-loop.sh", "pinned_tests.py"} <= loop
    assert not [name for name in loop if name.lower().startswith("bootstrap")]
    assert "tests" not in loop and "flow.toml" not in loop


def test_plugin_is_vendored_and_renamed(run: Run, target: Path) -> None:
    run("--stack", "python")
    plugin = target / ".flow" / "plugin"
    manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "agent-flow" and manifest["version"] == "1.0.0"
    assert (plugin / "hooks" / "before-edit-check.py").is_file()
    assert not list(plugin.rglob("tests"))
    market = json.loads((target / ".claude-plugin" / "marketplace.json").read_text())
    assert market["name"] == "garden"
    assert market["plugins"][0]["source"] == "./.flow/plugin"


def test_settings_and_flow_toml_point_at_the_vendored_plugin(run: Run, target: Path) -> None:
    run("--stack", "python")
    settings = json.loads((target / ".claude" / "settings.json").read_text())
    assert settings["enabledPlugins"] == {"agent-flow@garden": True}
    assert settings["extraKnownMarketplaces"] == {
        "garden": {"source": {"source": "github", "repo": REPO}}
    }
    edits = [rule for rule in settings["permissions"]["allow"] if rule.startswith("Edit(./")]
    assert "Edit(./src/**)" in edits and "Edit(./docs/specs/**)" in edits
    assert "Edit(./specs/**)" not in edits and "Edit(./tests/**)" not in edits
    assert flow_toml(target)["plugin"] == {"id": "agent-flow@garden", "marketplace": "garden"}


# AC19: flow.toml per stack, check.sh


@pytest.mark.parametrize(
    ("stack", "setup", "alone"),
    [
        ("python", ["uv", "sync", "--frozen"], ["migrations/"]),
        ("node", ["npm", "ci"], ["migrations/"]),
        ("other", ["bash", "scripts/setup.sh"], []),
    ],
)
def test_flow_toml_has_the_new_paths_and_stack_values(
    run: Run, target: Path, stack: str, setup: list[str], alone: list[str]
) -> None:
    run("--stack", stack)
    data = flow_toml(target)
    assert data["paths"] == NEW_PATHS
    assert data["checks"]["commands"] == [["bash", "scripts/check.sh"]]
    assert data["checks"]["protected_test_dirs"] == ["tests"]
    assert data["loop"]["setup_command"] == setup
    assert data["loop"]["alone_words"] == alone
    assert data["project"]["app_dir"] == "."


def test_the_copied_reader_reads_the_new_flow_toml(run: Run, target: Path) -> None:
    run("--stack", "node")
    done = subprocess.run(
        [sys.executable, str(target / ".flow" / "loop" / "flow_config.py"), "paths.code_dirs"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert done.stdout == "src\n"


@pytest.mark.parametrize(
    ("stack", "commands"),
    [
        ("python", ["uv run ruff check .", "uv run mypy .", "uv run pytest -q"]),
        ("node", ["npm run lint", "npm run typecheck", "npm test"]),
    ],
)
def test_check_script_runs_the_stack_commands(
    run: Run, target: Path, stack: str, commands: list[str]
) -> None:
    run("--stack", stack)
    script = target / "scripts" / "check.sh"
    text = script.read_text()
    assert "set -euo pipefail" in text
    assert all(command in text for command in commands)
    assert script.stat().st_mode & stat.S_IXUSR


def test_python_check_counts_no_tests_as_a_pass(run: Run, target: Path) -> None:
    run("--stack", "python")
    text = (target / "scripts" / "check.sh").read_text()
    assert '"$status" -eq 5' in text and "WARNING" in text


def test_other_check_says_todo_and_fails(run: Run, target: Path) -> None:
    run("--stack", "other")
    done = subprocess.run(
        ["bash", str(target / "scripts" / "check.sh")], capture_output=True, text=True
    )
    assert done.returncode == 1
    assert "TODO: add the checks of this stack" in done.stdout


# AC20: .gitignore and .env.example


@pytest.mark.parametrize(
    ("stack", "own", "other"),
    [
        ("python", [".venv/", "__pycache__/", "db.sqlite3", ".coverage"], ["node_modules/"]),
        ("node", ["node_modules/", "dist/", "coverage/"], [".venv/"]),
        ("other", [], [".venv/", "node_modules/"]),
    ],
)
def test_gitignore_has_the_common_and_stack_parts(
    run: Run, target: Path, stack: str, own: list[str], other: list[str]
) -> None:
    run("--stack", stack)
    lines = (target / ".gitignore").read_text().splitlines()
    common = [".env", ".env.*", "!.env.example", "in/", "out/", ".DS_Store", ".playwright-mcp/"]
    assert all(line in lines for line in [*common, "*.log", ".claude/settings.local.json", *own])
    assert not [line for line in other if line in lines]


def test_env_example_has_one_comment_line_and_no_values(run: Run, target: Path) -> None:
    run("--stack", "other")
    lines = (target / ".env.example").read_text().splitlines()
    assert len(lines) == 1 and lines[0].startswith("#")


# AC21: checks.yml


@pytest.mark.parametrize("stack", STACKS)
def test_checks_workflow_runs_check_sh_and_the_plugin_version(
    run: Run, target: Path, stack: str
) -> None:
    run("--stack", stack)
    text = (target / ".github" / "workflows" / "checks.yml").read_text()
    assert text.startswith("name: Checks\n")
    assert "pull_request:" in text and "branches: [main, deploy]" in text
    assert "run: bash scripts/check.sh" in text
    assert "python .flow/loop/check_plugin_version.py" in text
    assert "../" not in text and "working-directory" not in text


# AC22: CLAUDE.md and the architecture rule


def test_claude_md_opens_with_the_layout(run: Run, target: Path) -> None:
    run("--stack", "python")
    head = "\n".join((target / "CLAUDE.md").read_text().splitlines()[:8])
    assert "`src/<feature>/`" in head and "`docs/`" in head
    assert "`.flow/`" in head and "Do not change it in a feature task" in head
    assert "`bash scripts/check.sh`" in head
    rule = (target / ".claude" / "rules" / "architecture.md").read_text()
    assert "by feature, not by layer" in rule


def test_claude_md_imports_only_written_files(run: Run, target: Path) -> None:
    run("--stack", "node")
    for line in (target / "CLAUDE.md").read_text().splitlines():
        if line.startswith("@"):
            assert (target / line[1:]).is_file(), line


# AC23: no old project value anywhere


@pytest.mark.parametrize("stack", STACKS)
def test_no_old_project_value_in_the_target(run: Run, target: Path, stack: str) -> None:
    run("--stack", stack)
    hits = [
        f"{path.relative_to(target)}: {match.group(0)}"
        for path in files_of(target)
        for match in OLD_WORDS.finditer(path.read_text(errors="replace"))
    ]
    assert hits == []


# AC24: --dry-run prints the tree and writes nothing


def test_dry_run_prints_one_path_per_line_and_writes_nothing(
    run: Run, target: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("--stack", "python", "--dry-run") == 0
    out = capsys.readouterr().out.splitlines()
    assert files_of(target) == []
    assert ".flow/flow.toml" in out and "scripts/check.sh" in out and "src/README.md" in out
    assert not [line for line in out if line.startswith("would write .flow")]


def test_a_second_run_stops_before_writing(
    run: Run, target: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run("--stack", "python") == 0
    capsys.readouterr()
    assert run("--stack", "python") == 2
    assert "already exist" in capsys.readouterr().err


def test_spec_rules_name_the_new_document_folders(run: Run, target: Path) -> None:
    run("--stack", "python")
    text = (target / ".claude" / "project-instructions.md").read_text()
    assert "`docs/intent/<feature>.md`, `docs/specs/<feature>/spec.md` and `tasks.md`" in text
    assert "changes only `docs/intent/` and `docs/specs/`" in text
    assert "docs/specs/<feature>/design.md" in text
    assert "`specs/`" not in text and "design/<feature>" not in text.replace("docs/specs/", "")
    template = (target / "docs" / "templates" / "spec" / "spec.md").read_text()
    assert "Copy to docs/specs/<feature>/spec.md" in template
