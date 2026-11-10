"""before-edit-check lets a loop build edit the files its issue lists (FLOW_ALLOWED_EDITS)."""

import json
import os
import subprocess
import sys
from importlib import util
from pathlib import Path
from typing import Any

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-edit-check.py"
LOOP = {"REVIEWRADAR_LOOP": "1"}
GUARD_MESSAGE = (
    "settings.json: the loop never changes the keys that turn guards off "
    "(disableAllHooks, enabledPlugins, extraKnownMarketplaces, hooks, permissions.deny); "
    "ask the user"
)


def load():  # type: ignore[no-untyped-def]
    spec = util.spec_from_file_location("edit_check_allowed_edits", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDIT = load()
SETTINGS = {
    "permissions": {"allow": ["Edit(./ops/**)"], "deny": ["Bash(rm:*)"]},
    "hooks": {"PreToolUse": []},
    "enabledPlugins": {"agent-flow@local": True},
}


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture
def lab(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    lab_dir = tmp_path / "lab"
    for rel in (
        "lab/reviews/tests/unit/test_old.py",
        "lab/.claude/rules/git.md",
        "lab/.claude/knowledge/decisions/ADR-001.md",
        "lab/pyproject.toml",
        "lab/.mcp.json",
        "lab/reviews/views.py",
        ".github/workflows/checks.yml",
        "plugins/agent-flow/hooks/before-edit-check.py",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x\n")
    (lab_dir / ".claude" / "settings.json").write_text(json.dumps(SETTINGS, indent=2))
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "task/386-x")
    return lab_dir


def check(
    lab: Path,
    rel: str,
    allowed: str = "",
    tool: str = "Edit",
    tool_input: dict[str, Any] | None = None,
    **extra: str,
) -> list[str]:
    env = {**LOOP, "FLOW_ALLOWED_EDITS": allowed, **extra} if allowed else {**LOOP, **extra}
    result: list[str] = EDIT.evaluate(
        str(lab / rel), lab, env, EDIT.real_run, tool, tool_input or {}
    )
    return result


@pytest.mark.parametrize(
    "rel",
    [
        ".claude/rules/git.md",
        ".claude/knowledge/decisions/ADR-001.md",
        "pyproject.toml",
        ".mcp.json",
        "reviews/tests/unit/test_old.py",
        "../.github/workflows/checks.yml",
        "../plugins/agent-flow/hooks/before-edit-check.py",
    ],
)
def test_a_listed_guarded_file_may_be_edited(lab: Path, rel: str) -> None:
    assert check(lab, rel, f"reviews/views.py\n{rel}\n") == []


def test_the_listed_path_ignores_letter_case_and_dot_slash(lab: Path) -> None:
    assert check(lab, ".claude/rules/git.md", "./.CLAUDE/Rules/GIT.md") == []


@pytest.mark.parametrize(
    ("rel", "message"),
    [
        (".claude/rules/git.md", "git.md is a rule file; the loop never changes its own rules"),
        ("pyproject.toml", "pyproject.toml sets the lint, type, test or dependency gates"),
        ("reviews/tests/unit/test_old.py", "test_old.py is a test that is already on main"),
        ("../plugins/agent-flow/hooks/before-edit-check.py", "is part of the flow plugin"),
    ],
)
def test_an_unlisted_guarded_file_keeps_todays_message(lab: Path, rel: str, message: str) -> None:
    problems = check(lab, rel, "reviews/views.py\n")
    assert len(problems) == 1 and message in problems[0]


def test_an_unlisted_unguarded_file_is_left_to_the_permission_rules(lab: Path) -> None:
    assert check(lab, "reviews/forms.py", "reviews/views.py\n") == []
    assert EDIT.listed_edit(lab / "reviews/forms.py", lab, {"FLOW_ALLOWED_EDITS": "x"}) is False


def test_flow_test_edits_still_opens_a_listed_test(lab: Path) -> None:
    rel = "reviews/tests/unit/test_old.py"
    assert check(lab, rel, FLOW_TEST_EDITS=rel) == []


@pytest.mark.parametrize("rel", ["../.git/config", "../.git/hooks/pre-commit", ".git/HEAD"])
def test_a_path_in_git_is_refused_even_when_listed(lab: Path, rel: str) -> None:
    problems = check(lab, rel, f"{rel}\n")
    assert problems and "inside .git" in problems[0]


def write(content: object) -> dict[str, Any]:
    text = content if isinstance(content, str) else json.dumps(content)
    return {"content": text}


LISTED_SETTINGS = ".claude/settings.json\n"


def test_a_settings_write_that_keeps_the_guard_keys_is_allowed(lab: Path) -> None:
    changed = {**SETTINGS, "permissions": {**SETTINGS["permissions"], "allow": ["Edit(./x/**)"]}}
    rel = ".claude/settings.json"
    assert check(lab, rel, LISTED_SETTINGS, "Write", write(changed)) == []


@pytest.mark.parametrize(
    "changed",
    [
        {**SETTINGS, "disableAllHooks": True},
        {**SETTINGS, "hooks": {}},
        {k: v for k, v in SETTINGS.items() if k != "enabledPlugins"},
        {**SETTINGS, "extraKnownMarketplaces": {"x": {}}},
        {**SETTINGS, "permissions": {"allow": [], "deny": []}},
        {**SETTINGS, "permissions": {"allow": []}},
    ],
    ids=["disable", "hooks", "plugins", "marketplaces", "deny-emptied", "deny-removed"],
)
def test_a_settings_write_that_changes_a_guard_key_is_refused(
    lab: Path, changed: dict[str, Any]
) -> None:
    problems = check(lab, ".claude/settings.json", LISTED_SETTINGS, "Write", write(changed))
    assert len(problems) == 1
    assert problems[0].startswith("settings.json: the loop never changes the keys")
    assert problems[0].endswith("; ask the user")


def test_the_refusal_names_the_keys_that_change(lab: Path) -> None:
    changed = {**SETTINGS, "disableAllHooks": True, "hooks": {}}
    problems = check(lab, ".claude/settings.json", LISTED_SETTINGS, "Write", write(changed))
    assert problems == [
        "settings.json: the loop never changes the keys that turn guards off "
        "(disableAllHooks, hooks); ask the user"
    ]


def test_an_edit_is_applied_to_the_file_on_disk(lab: Path) -> None:
    ok = {"old_string": '"Edit(./ops/**)"', "new_string": '"Edit(./ops/**)", "Edit(./x/**)"'}
    assert check(lab, ".claude/settings.json", LISTED_SETTINGS, "Edit", ok) == []
    bad = {"old_string": '"Bash(rm:*)"', "new_string": ""}
    problems = check(lab, ".claude/settings.json", LISTED_SETTINGS, "Edit", bad)
    assert problems and "(permissions.deny)" in problems[0]


def test_a_multi_edit_is_applied_in_order(lab: Path) -> None:
    edits = {
        "edits": [
            {"old_string": '"Edit(./ops/**)"', "new_string": '"Edit(./a/**)"'},
            {"old_string": '"Edit(./a/**)"', "new_string": '"Edit(./b/**)"'},
        ]
    }
    assert check(lab, ".claude/settings.json", LISTED_SETTINGS, "MultiEdit", edits) == []
    edits["edits"].append({"old_string": '"hooks"', "new_string": '"hooks_off"'})
    problems = check(lab, ".claude/settings.json", LISTED_SETTINGS, "MultiEdit", edits)
    assert problems and "(hooks)" in problems[0]


@pytest.mark.parametrize(
    ("tool", "tool_input"),
    [
        ("Edit", {"old_string": "not in the file", "new_string": "x"}),
        ("Write", {"content": "{not json"}),
        ("Write", {"content": "[]"}),
        ("Edit", {"old_string": "{", "new_string": "{{"}),
        ("NotebookEdit", {"new_source": "x"}),
    ],
    ids=["old-missing", "invalid-json", "not-an-object", "edit-breaks-json", "notebook"],
)
def test_a_settings_result_that_cannot_be_worked_out_is_refused(
    lab: Path, tool: str, tool_input: dict[str, Any]
) -> None:
    assert check(lab, ".claude/settings.json", LISTED_SETTINGS, tool, tool_input) == [GUARD_MESSAGE]


def test_settings_local_json_is_guarded_the_same_way(lab: Path) -> None:
    rel = ".claude/settings.local.json"
    assert check(lab, rel, f"{rel}\n", "Write", write({"permissions": {"allow": []}})) == []
    problems = check(lab, rel, f"{rel}\n", "Write", write({"disableAllHooks": True}))
    assert problems and problems[0].startswith("settings.local.json: the loop never changes")


def test_an_unlisted_settings_file_keeps_the_rule_file_message(lab: Path) -> None:
    problems = check(lab, ".claude/settings.json", "x\n", "Write", write(SETTINGS))
    assert problems == [
        "settings.json is a rule file; the loop never changes its own rules, ask the user"
    ]


def test_outside_loop_mode_nothing_changes(lab: Path) -> None:
    path = str(lab / ".claude/settings.json")
    tool_input = write({"disableAllHooks": True})
    env = {"FLOW_ALLOWED_EDITS": LISTED_SETTINGS}
    assert EDIT.evaluate(path, lab, env, EDIT.real_run, "Write", tool_input) == []


def run_hook(lab: Path, rel: str, allowed: str | None, loop: bool = True) -> tuple[int, str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("FLOW_LOOP", "REVIEWRADAR_LOOP")}
    env.pop("FLOW_ALLOWED_EDITS", None)
    env.pop("FLOW_TEST_EDITS", None)
    env["CLAUDE_PROJECT_DIR"] = str(lab)
    env["FLOW_CONFIG"] = str(Path(os.environ["CLAUDE_PROJECT_DIR"]) / "ops" / "flow.toml")
    if loop:
        env["REVIEWRADAR_LOOP"] = "1"
    if allowed is not None:
        env["FLOW_ALLOWED_EDITS"] = allowed
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(lab / rel), "old_string": "x", "new_string": "y"},
        "cwd": str(lab),
    }
    done = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return done.returncode, done.stdout, done.stderr


def test_the_hook_answers_allow_for_a_listed_file(lab: Path) -> None:
    code, out, _ = run_hook(lab, ".claude/rules/git.md", ".claude/rules/git.md\n")
    assert code == 0
    answer = json.loads(out)["hookSpecificOutput"]
    assert answer["hookEventName"] == "PreToolUse"
    assert answer["permissionDecision"] == "allow"


def test_the_hook_blocks_an_unlisted_guarded_file(lab: Path) -> None:
    code, out, err = run_hook(lab, ".claude/rules/git.md", "reviews/views.py\n")
    assert code == 2 and out == ""
    assert "git.md is a rule file" in err


def test_the_hook_says_nothing_for_an_unlisted_unguarded_file(lab: Path) -> None:
    assert run_hook(lab, "reviews/views.py", ".claude/rules/git.md\n") == (0, "", "")


def test_the_hook_says_nothing_outside_loop_mode(lab: Path) -> None:
    assert run_hook(lab, ".claude/rules/git.md", ".claude/rules/git.md\n", loop=False) == (
        0,
        "",
        "",
    )
