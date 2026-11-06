"""route_issue.py: an existing test named under 'Existing tests that change' is not manual."""

import os
import tomllib
from importlib import util
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[1] / "route_issue.py"
PROJECT = Path(os.environ["CLAUDE_PROJECT_DIR"])
FLOW_DATA = tomllib.loads((PROJECT / "ops" / "flow.toml").read_text())
APP_DIR = FLOW_DATA["project"]["app_dir"]
PKG = FLOW_DATA["checks"]["protected_test_dirs"][0].split("/")[0]
ALLOW = [f"Edit(./{PKG}/**)", "Edit(./reviewradar/**)"]


def load() -> ModuleType:
    spec = util.spec_from_file_location("route_issue_test_edits", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROUTE = load()
OLD = f"{APP_DIR}/{PKG}/tests/integration/test_seed_demo_replies.py"
NEW = f"{APP_DIR}/{PKG}/tests/integration/test_seed_demo_reply_times.py"


def issue(edits: str) -> str:
    files = (
        "## Files likely touched\n\n"
        f"- `{APP_DIR}/{PKG}/management/commands/seed_demo_data.py`\n"
        f"- `{OLD}`\n"
        f"- `{NEW}` (NEW test file)\n\n"
    )
    return "## Summary\n\nx\n\n" + files + edits + "## How to check it when built\n\n1. x\n"


def test_a_listed_existing_test_is_ready() -> None:
    edits = f"## Existing tests that change\n\n- `{OLD}::test_default_seed`: 9 replies.\n\n"
    assert ROUTE.route(issue(edits), ALLOW) == ["area:app", "agent:ready"]


def test_a_listed_path_without_test_name_is_ready() -> None:
    edits = f"## Existing tests that change\n\n- `{OLD}`\n\n"
    assert ROUTE.route(issue(edits), ALLOW) == ["area:app", "agent:ready"]


def test_without_the_section_the_existing_test_is_manual() -> None:
    assert ROUTE.route(issue(""), ALLOW) == ["area:app", "agent:manual"]


def test_listing_another_test_does_not_open_this_one() -> None:
    other = f"{APP_DIR}/{PKG}/tests/unit/test_other.py"
    edits = f"## Existing tests that change\n\n- `{other}::test_x`\n\n"
    assert ROUTE.route(issue(edits), ALLOW) == ["area:app", "agent:manual"]
