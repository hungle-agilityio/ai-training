"""route_issue takes its folder prefix from project.app_dir of ops/flow.toml.

Run: uv run pytest .claude/skills/create-issue/tests --no-cov -q
"""

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
FLOW_TOML = PROJECT / "ops" / "flow.toml"


def load() -> ModuleType:
    spec = util.spec_from_file_location("route_issue_flow", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROUTE = load()


def body(*paths: str) -> str:
    bullets = "\n".join(f"- `{path}`" for path in paths)
    return f"Summary.\n\n## Files likely touched\n\n{bullets}\n"


def config_with_app_dir(folder: Path, app_dir: str) -> Path:
    text = FLOW_TOML.read_text()
    current = tomllib.loads(text)["project"]["app_dir"]
    path = folder / "flow.toml"
    path.write_text(text.replace(f'app_dir = "{current}"', f'app_dir = "{app_dir}"'))
    return path


def route_cli(tmp_path: Path, config: Path, *paths: str) -> str:
    issue = tmp_path / "issue.md"
    issue.write_text(body(*paths))
    settings = tmp_path / "settings.json"
    settings.write_text('{"permissions": {"allow": ["Edit(./ops/**)", "Edit(./src/**)"]}}')
    env = {**os.environ, "FLOW_CONFIG": str(config)}
    done = subprocess.run(
        [sys.executable, str(SCRIPT), str(issue), "--settings", str(settings)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return done.stdout.strip()


def test_prefix_comes_from_the_committed_app_dir() -> None:
    app_dir = tomllib.loads(FLOW_TOML.read_text())["project"]["app_dir"]
    assert ROUTE.LAB_PREFIX == f"{app_dir}/"
    assert ROUTE.paths_of(body(f"{app_dir}/ops/x.py")) == ["ops/x.py"]


@pytest.mark.parametrize(("app_dir", "prefix"), [(".", ""), ("web", "web/"), ("web/", "web/")])
def test_prefix_for_an_app_dir(app_dir: str, prefix: str) -> None:
    assert ROUTE.prefix_for(app_dir) == prefix


def test_dot_means_no_prefix() -> None:
    text = body("ops/x.py", f"{APP_DIR}/ops/y.py")
    assert ROUTE.paths_of(text, "") == ["ops/x.py", f"{APP_DIR}/ops/y.py"]


def test_cli_strips_the_configured_app_dir(tmp_path: Path) -> None:
    config = config_with_app_dir(tmp_path, "web")
    assert route_cli(tmp_path, config, "web/ops/x.py") == "area:flow agent:ready"


def test_cli_with_dot_app_dir_keeps_paths_from_the_root(tmp_path: Path) -> None:
    config = config_with_app_dir(tmp_path, ".")
    assert route_cli(tmp_path, config, "ops/x.py") == "area:flow agent:ready"
    other = route_cli(tmp_path, config, f"{APP_DIR}/ops/x.py")
    assert other == "area:app agent:ready"
