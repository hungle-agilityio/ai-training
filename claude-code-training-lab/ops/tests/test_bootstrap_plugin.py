"""Spec specs/flow-plugin/spec.md, AC25 to AC28: bootstrap turns the plugin on, never copies it."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ops import bootstrap

REPO = "acme/shop"
SOURCE = {"source": "github", "repo": "hungle-agilityio/ai-training"}
MARKETPLACE = {"ai-training": {"source": SOURCE}}
PLUGINS = {"agent-flow@ai-training": True}
INSTALL = (
    "claude plugin marketplace add hungle-agilityio/ai-training",
    "claude plugin install agent-flow@ai-training",
)


@pytest.fixture
def target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    path = tmp_path / "shop"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{REPO}.git"], cwd=path, check=True
    )
    return path


def _run(target: Path, *extra: str) -> int:
    return bootstrap.main(
        [
            "--target", str(target), "--repo", REPO, "--owner", "acme-owner",
            "--app-dir", ".", "--name", "Shop", "--slug", "shop", "--ntfy-topic", "t",
            "--no-labels", *extra,
        ]
    )  # fmt: skip


def test_settings_turn_the_plugin_on_with_the_original_marketplace(target: Path) -> None:
    assert _run(target) == 0

    settings = json.loads((target / ".claude/settings.json").read_text())
    assert settings["extraKnownMarketplaces"] == MARKETPLACE
    assert settings["enabledPlugins"] == PLUGINS
    assert "permissions" in settings


def test_existing_plugin_keys_are_replaced_and_others_kept() -> None:
    other = {"other": {"source": {"source": "github", "repo": "x/y"}}}
    source = json.dumps(
        {
            "env": {"A": "1"},
            "extraKnownMarketplaces": other,
            "enabledPlugins": {"agent-flow@ai-training": False, "keep@me": True},
        }
    )

    result = json.loads(bootstrap.with_plugin_settings(source))

    assert result["env"] == {"A": "1"}
    assert result["extraKnownMarketplaces"] == MARKETPLACE
    assert result["enabledPlugins"] == PLUGINS


def test_dry_run_lists_the_settings_and_writes_nothing(
    target: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(target, "--dry-run") == 0

    assert "would write .claude/settings.json" in capsys.readouterr().out
    assert not (target / ".claude/settings.json").exists()


def test_a_real_run_copies_no_hooks_skills_commands_or_agents(target: Path) -> None:
    assert _run(target) == 0

    for folder in ("hooks", "commands", "agents"):
        assert not (target / ".claude" / folder).exists()
    assert not (target / ".claude/skills/work-queue").exists()


def test_the_install_commands_are_the_first_steps(
    target: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(target, "--dry-run") == 0

    lines = capsys.readouterr().out.splitlines()
    steps = [line for line in lines if line.startswith(("1. ", "2. "))]
    assert INSTALL[0] in steps[0]
    assert INSTALL[1] in steps[1]


def test_the_guide_says_the_same() -> None:
    text = (Path(bootstrap.__file__).parent / "BOOTSTRAP.md").read_text()

    assert all(command in text for command in INSTALL)
