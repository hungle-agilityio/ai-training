"""Three fixes of `bootstrap.py --stack`: agent.env ignored, flow.toml path, one loop variable.

Run: pytest ops/tests/test_bootstrap_layout_fixes.py
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap

OPS = Path(__file__).resolve().parents[1]
PLUGIN = OPS.parents[1] / "plugins" / "agent-flow"
STACKS = ("python", "node", "other")
Run = Callable[[str], Path]


@pytest.fixture
def made(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Run:
    """Run bootstrap --stack into a fresh clone and return the clone."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)

    def call(stack: str) -> Path:
        target = tmp_path / stack
        target.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=target, check=True)
        origin = "https://github.com/acme/garden.git"
        subprocess.run(["git", "remote", "add", "origin", origin], cwd=target, check=True)
        argv = [
            "--target", str(target), "--repo", "acme/garden", "--owner", "acme-owner",
            "--name", "Garden", "--slug", "garden", "--ntfy-topic", "t", "--no-labels",
            "--stack", stack,
        ]  # fmt: skip
        assert bootstrap.main(argv) == 0
        return target

    return call


def text_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]


# (a) the loop's own settings file is never committed


@pytest.mark.parametrize("stack", STACKS)
def test_gitignore_ignores_the_loop_settings_file(made: Run, stack: str) -> None:
    lines = (made(stack) / ".gitignore").read_text().splitlines()
    assert ".flow/loop/agent.env" in lines


# (b) the flow config of a new project is .flow/flow.toml


def test_no_text_names_a_flow_toml_inside_the_loop_folder(made: Run) -> None:
    target = made("python")
    hits = [
        str(p.relative_to(target))
        for p in text_files(target)
        if ".flow/loop/flow.toml" in p.read_text()
    ]
    assert hits == []


def test_texts_that_named_ops_flow_toml_name_dot_flow_flow_toml(made: Run) -> None:
    readme = (made("other") / ".flow" / "loop" / "README.md").read_text()
    assert ".flow/flow.toml" in readme


# (c) one loop variable, FLOW_LOOP


@pytest.mark.parametrize("stack", STACKS)
def test_no_old_loop_or_home_variable_is_copied(made: Run, stack: str) -> None:
    target = made(stack)
    hits = [
        str(p.relative_to(target)) for p in text_files(target) if "REVIEWRADAR_" in p.read_text()
    ]
    assert hits == []


def test_no_doubled_loop_variable_is_left(made: Run) -> None:
    target = made("python")
    doubled = re.compile(
        r"FLOW_LOOP\W{1,12}(?:or|and|with)?\W{0,6}FLOW_LOOP|\"FLOW_LOOP\", \"FLOW_LOOP\""
    )
    hits = [str(p.relative_to(target)) for p in text_files(target) if doubled.search(p.read_text())]
    assert hits == []


def test_copied_python_still_parses_and_hooks_read_flow_loop(made: Run) -> None:
    target = made("node")
    for path in (target / ".flow").rglob("*.py"):
        ast.parse(path.read_text(), str(path))
    hook = (target / ".flow" / "plugin" / "hooks" / "before-edit-check.py").read_text()
    assert 'LOOP_VARS = ("FLOW_LOOP",)' in hook
    tick = (target / ".flow" / "loop" / "agent_tick.py").read_text()
    assert '"FLOW_LOOP": "1"}' in tick


def test_reviewradar_keeps_both_variables() -> None:
    assert '"REVIEWRADAR_LOOP": "1"' in (OPS / "agent_tick.py").read_text()
    hook = (PLUGIN / "hooks" / "before-edit-check.py").read_text()
    assert 'LOOP_VARS = ("FLOW_LOOP", "REVIEWRADAR_LOOP")' in hook
