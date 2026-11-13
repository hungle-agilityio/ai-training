"""A new project allows edits of its prototype folder like its spec documents (#573)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ops import bootstrap, bootstrap_layout

REPO = "acme/garden"
SPECS_RULE = "Edit(./docs/specs/**)"
DESIGN_RULE = "Edit(./docs/design/**)"


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


def _bootstrap(target: Path, *extra: str) -> int:
    argv = [
        "--target", str(target), "--repo", REPO, "--owner", "acme-owner",
        "--name", "Garden", "--slug", "garden", "--ntfy-topic", "garden-test", "--no-labels",
    ]  # fmt: skip
    return bootstrap.main([*argv, *extra])


def _allow(target: Path) -> list[str]:
    settings = json.loads((target / ".claude" / "settings.json").read_text())
    allow: list[str] = settings["permissions"]["allow"]
    return allow


def test_specs_rule_moves_to_intent_specs_and_design_in_order() -> None:
    assert bootstrap_layout.EDIT_MOVES["Edit(./specs/**)"] == [
        "Edit(./docs/intent/**)",
        SPECS_RULE,
        DESIGN_RULE,
    ]


def test_stack_settings_allow_design_edits_once_right_after_specs(target: Path) -> None:
    assert _bootstrap(target, "--stack", "python") == 0
    allow = _allow(target)
    assert allow.count(DESIGN_RULE) == 1
    assert allow.index(DESIGN_RULE) == allow.index(SPECS_RULE) + 1


def test_old_layout_settings_name_no_design_folder(target: Path) -> None:
    assert _bootstrap(target, "--app-dir", ".") == 0
    assert not [rule for rule in _allow(target) if "docs/design" in rule]
