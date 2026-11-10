"""route_issue.py: every issue inside the repository is agent:ready (ADR-023)."""

import os
import subprocess
import sys
import tomllib
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "route_issue.py"
PROJECT = Path(os.environ["CLAUDE_PROJECT_DIR"])
FLOW_DATA = tomllib.loads((PROJECT / "ops" / "flow.toml").read_text())
APP_DIR = FLOW_DATA["project"]["app_dir"]
PKG = FLOW_DATA["checks"]["protected_test_dirs"][0].split("/")[0]
DEPTH = len([part for part in APP_DIR.split("/") if part not in ("", ".")])


def load() -> ModuleType:
    spec = util.spec_from_file_location("route_issue_all_ready", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROUTE = load()


def issue(*paths: str) -> str:
    listed = "\n".join(f"- `{p}`" for p in paths)
    return f"## Summary\n\nx\n\n## Files likely touched\n\n{listed}\n\n## Next\n\n1. x\n"


@pytest.mark.parametrize(
    "path",
    [
        ".claude/settings.json",
        ".github/workflows/checks.yml",
        "../.github/workflows/checks.yml",
        ".mcp.json",
        "pyproject.toml",
        "uv.lock",
        f"{PKG}/tests/conftest.py",
        f"{PKG}/tests/integration/test_dashboard.py",
        "../plugins/agent-flow/hooks/before-edit-check.py",
        "reviewradar/settings.py",
    ],
)
@pytest.mark.parametrize("allow", [[], [f"Edit(./{PKG}/**)"]], ids=["no-rules", "app-rule"])
def test_every_path_inside_the_repository_is_ready(path: str, allow: list[str]) -> None:
    labels = ROUTE.route(issue(f"{PKG}/views.py", path), allow)
    assert labels[1] == "agent:ready"
    assert "agent:manual" not in labels and "agent:needs-permission" not in labels


def test_a_plugin_path_is_flow_and_ready() -> None:
    path = "../plugins/agent-flow/skills/create-issue/route_issue.py"
    assert ROUTE.route(issue(path), []) == ["area:flow", "agent:ready"]


def test_an_app_path_is_app_and_ready_without_allow_rules() -> None:
    assert ROUTE.route(issue(f"{PKG}/views.py"), []) == ["area:app", "agent:ready"]


def test_a_path_that_leaves_the_repository_is_not_routed() -> None:
    outside = "../" * (DEPTH + 1) + "elsewhere/x.py"
    with pytest.raises(ValueError, match=f"{outside} is outside the repository"):
        ROUTE.route(issue(f"{PKG}/views.py", outside), [])


def test_a_path_that_climbs_back_inside_is_routed() -> None:
    inside = "../" * DEPTH + (f"{APP_DIR}/" if DEPTH else "") + f"{PKG}/views.py"
    assert ROUTE.route(issue(inside), [])[1] == "agent:ready"


def run(tmp_path: Path, *extra: str, paths: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "issue.md"
    path.write_text(issue(*paths))
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_cli_prints_not_routed_for_a_path_outside(tmp_path: Path) -> None:
    outside = "../" * (DEPTH + 1) + "x.py"
    done = run(tmp_path, paths=(outside,))
    assert done.returncode == 1
    assert done.stdout.strip() == f"NOT ROUTED: {outside} is outside the repository"


def test_the_cli_keeps_and_ignores_the_settings_option(tmp_path: Path) -> None:
    missing = tmp_path / "no-such-settings.json"
    done = run(tmp_path, "--settings", str(missing), paths=(".claude/settings.json",))
    assert done.returncode == 0
    assert done.stdout.split() == ["area:flow", "agent:ready"]
