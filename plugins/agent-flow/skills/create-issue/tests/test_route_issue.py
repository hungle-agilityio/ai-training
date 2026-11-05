"""Tests of the issue router. Run: uv run pytest .claude/skills/create-issue/tests --no-cov -q"""

import json
import os
import subprocess
import sys
import tomllib
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "route_issue.py"
PROJECT = Path(os.environ["CLAUDE_PROJECT_DIR"])
FLOW_DATA = tomllib.loads((PROJECT / "ops" / "flow.toml").read_text())
APP_DIR = FLOW_DATA["project"]["app_dir"]
PKG = FLOW_DATA["checks"]["protected_test_dirs"][0].split("/")[0]


def load() -> ModuleType:
    spec = util.spec_from_file_location("route_issue", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROUTE = load()
ALLOW = [f"Edit(./{PKG}/**)", "Edit(./reviewradar/**)", "Edit(./ops/**)", "Edit(//**/render.yaml)"]


def body(*paths: str) -> str:
    bullets = "\n".join(f"- {path}" for path in paths)
    return f"Summary.\n\n## Files likely touched\n\n{bullets}\n\n## After\n\n- `docs/x.md`\n"


def labels(*paths: str) -> list[str]:
    result: list[str] = ROUTE.route(body(*paths), ALLOW)
    return result


def test_an_app_issue_inside_the_allow_rules_is_ready() -> None:
    assert labels(f"`{PKG}/views.py`", f"`{PKG}/tests/integration/test_x.py` (NEW)") == [
        "area:app",
        "agent:ready",
    ]


def test_an_ops_issue_is_flow_and_ready() -> None:
    assert labels("`ops/agent_tick.py`", "`ops/tests/test_agent_tick.py`") == [
        "area:flow",
        "agent:ready",
    ]


@pytest.mark.parametrize(
    "path",
    [
        "`.claude/settings.json`",
        "`.github/workflows/checks.yml`",
        "`.mcp.json`",
        "`pyproject.toml`",
        "`uv.lock`",
        f"`{PKG}/tests/conftest.py`",
        f"`{PKG}/tests/integration/test_dashboard.py`",
    ],
)
def test_a_path_the_hook_refuses_makes_the_issue_manual(path: str) -> None:
    assert labels(f"`{PKG}/views.py`", path)[1] == "agent:manual"


def test_an_existing_ops_test_is_not_manual_because_the_hook_allows_it() -> None:
    assert labels("`ops/tests/test_tick_merge.py`")[1] == "agent:ready"


def test_a_path_without_an_allow_rule_needs_permission() -> None:
    assert labels("`reviewradar/settings.py`", f"`.gitignore` in `{APP_DIR}/`") == [
        "area:app",
        "agent:needs-permission",
    ]


def test_the_repository_root_is_one_folder_up() -> None:
    assert labels("`render.yaml` (NEW, repository root)")[1] == "agent:ready"
    assert labels("`../render.yaml` (NEW)")[1] == "agent:ready"
    assert labels(f"`{APP_DIR}/{PKG}/views.py`")[1] == "agent:ready"


@pytest.mark.parametrize("path", ["`specs/x/spec.md`", "`docs/learning/a.md`", "`.claude/x.md`"])
def test_flow_folders_make_the_issue_flow(path: str) -> None:
    assert labels(f"`{PKG}/views.py`", path)[0] == "area:flow"


def test_docs_of_the_app_stay_app() -> None:
    assert labels("`docs/app/x.md`")[0] == "area:app"


def test_only_the_files_section_is_read() -> None:
    assert ROUTE.paths_of(body(f"`{PKG}/views.py`")) == [f"{PKG}/views.py"]


def test_an_issue_without_the_section_is_refused() -> None:
    with pytest.raises(ValueError):
        ROUTE.route("Summary only.\n", ALLOW)


def test_the_script_reads_the_allow_rules_from_the_settings_file(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"permissions": {"allow": ["Edit(./ops/**)"]}}))
    issue = tmp_path / "issue.md"
    issue.write_text(body(f"`{PKG}/views.py`"))
    done = subprocess.run(
        [sys.executable, str(SCRIPT), str(issue), "--settings", str(settings)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0
    assert done.stdout.split() == ["area:app", "agent:needs-permission"]


def test_the_script_stops_with_one_line_when_the_section_is_missing(tmp_path: Path) -> None:
    issue = tmp_path / "issue.md"
    issue.write_text("Summary only.\n")
    done = subprocess.run(
        [sys.executable, str(SCRIPT), str(issue)], capture_output=True, text=True, check=False
    )
    assert done.returncode != 0
    assert len(done.stdout.strip().splitlines() + done.stderr.strip().splitlines()) == 1
