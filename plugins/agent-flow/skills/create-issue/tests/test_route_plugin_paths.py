"""route_issue.py: a path in the plugin is flow work, done by hand (#345)."""

import os
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
APP_PATH = f"{APP_DIR}/{PKG}/views.py"
ALLOW_APP = [f"Edit(./{PKG}/**)"]
ALLOW_ALL = [*ALLOW_APP, "Edit(../plugins/**)", "Edit(./plugins/**)", "Edit(plugins/**)"]
PLUGIN_PATHS = [
    "../plugins/agent-flow/skills/create-issue/route_issue.py",
    "plugins/agent-flow/hooks/before-edit-check.py",
]


def load() -> ModuleType:
    spec = util.spec_from_file_location("route_issue_plugin_paths", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROUTE = load()


def issue(*paths: str) -> str:
    listed = "\n".join(f"- `{p}`" for p in paths)
    return f"## Summary\n\nx\n\n## Files likely touched\n\n{listed}\n\n## Next\n\n1. x\n"


@pytest.mark.parametrize("path", PLUGIN_PATHS)
@pytest.mark.parametrize("allow", [[], ALLOW_APP, ALLOW_ALL], ids=["none", "app", "all"])
def test_a_plugin_path_is_flow_work_done_by_hand(path: str, allow: list[str]) -> None:
    assert ROUTE.route(issue(path), allow) == ["area:flow", "agent:manual"]


@pytest.mark.parametrize("path", PLUGIN_PATHS)
def test_one_plugin_path_among_app_paths_decides(path: str) -> None:
    assert ROUTE.route(issue(APP_PATH, path), ALLOW_APP) == ["area:flow", "agent:manual"]


def test_only_app_paths_stay_ready_when_allowed() -> None:
    assert ROUTE.route(issue(APP_PATH), ALLOW_APP) == ["area:app", "agent:ready"]


def test_only_app_paths_still_need_permission_when_not_allowed() -> None:
    assert ROUTE.route(issue(APP_PATH), []) == ["area:app", "agent:needs-permission"]


def test_a_folder_that_only_starts_like_plugins_is_not_the_plugin() -> None:
    path = f"{APP_DIR}/{PKG}/plugins/agent-flow/x.py"
    assert ROUTE.route(issue(path), ALLOW_APP)[0] == "area:app"
