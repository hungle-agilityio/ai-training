"""Loop builds hand over: write out/, comment on issues. Run: uv run pytest .claude/hooks/tests"""

import json
import os
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parents[1]
LAB = HOOKS.parents[1]
GITHUB_HOOK = HOOKS / "before-github-command-check.py"
ALLOWED = "hungle-agilityio/ai-training"
LOOP = {"REVIEWRADAR_LOOP": "1"}


def load(name: str, path: Path) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load("guard_handover", GITHUB_HOOK)
EDIT = load("edit_handover", HOOKS / "before-edit-check.py")


def no_git(args: list[str]) -> tuple[int, str]:
    return 0, "task/61-x\n"


def no_git_edit(args: list[str], cwd: Path) -> tuple[int, str]:
    return 1, ""


def guard_problems(command: str) -> list[str]:
    result: list[str] = GUARD.check_command(command, ALLOWED)
    return result


def publish_decision(command: str) -> str:
    decision: str = GUARD.check_publish(command, True, no_git)[0]
    return decision


def allow_rules() -> list[str]:
    settings = json.loads((LAB / ".claude" / "settings.json").read_text())
    rules: list[str] = settings["permissions"]["allow"]
    return rules


# AC1: a loop build may write under out/.


def test_settings_allow_edits_under_out() -> None:
    assert "Edit(./out/**)" in allow_rules()


@pytest.mark.parametrize("rel", ["out/v61/criteria.json", "out/verify/2026/report.html"])
def test_edit_hook_lets_loop_write_under_out(rel: str, tmp_path: Path) -> None:
    assert EDIT.evaluate(str(tmp_path / rel), tmp_path, LOOP, no_git_edit) == []


# AC2: issue comments and edits with awkward bodies pass the hook.

AWKWARD_ISSUE_COMMANDS = [
    "gh issue comment 61 --body \"The build couldn't open the pull request\"",
    "gh issue comment 61 --body 'He said \"done\" twice'",
    'gh issue comment 61 --body "Line one\nIt couldn\'t push\nLine three"',
    "gh issue comment 61 --body-file out/v61/comment.md",
    "gh issue comment 61 --body-file - <<EOF\nThe loop couldn't finish.\nEOF",
    "gh issue comment 61 --body \"$(cat <<'EOF'\nThe loop couldn't finish; it stopped.\nEOF\n)\"",
    'gh issue edit 61 --add-label agent:failed --body "Build stopped\nIt couldn\'t commit"',
    "gh issue edit 61 --repo hungle-agilityio/ai-training --body \"it's done\nnext\"",
]


@pytest.mark.parametrize("command", AWKWARD_ISSUE_COMMANDS)
def test_issue_comment_and_edit_pass_the_repository_check(command: str) -> None:
    assert guard_problems(command) == []


@pytest.mark.parametrize("command", AWKWARD_ISSUE_COMMANDS)
def test_issue_comment_and_edit_pass_the_publish_gate_in_loop(command: str) -> None:
    assert publish_decision(command) == "allow"


def test_hook_lets_a_heredoc_issue_comment_run_in_loop_mode() -> None:
    command = "gh issue comment 61 --body \"$(cat <<'EOF'\nIt couldn't push.\nEOF\n)\""
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(LAB)}
    done = subprocess.run(
        [sys.executable, "-I", str(GITHUB_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, **LOOP},
        check=False,
    )
    assert done.returncode == 0, done.stderr


# AC3: another repository is still refused, also when the text cannot be split.

FOREIGN_UNSPLIT = [
    "gh issue comment 1 -R other/repo --body \"it's done\nnext\"",
    "gh issue comment 1 --repo=other/repo --body \"it's done\nnext\"",
    "gh issue edit 1 --body \"see https://github.com/other/repo it's there\nnext\"",
    "gh issue comment 1 --body \"it's in repos/other/repo now\nnext\"",
    "git push \"https://github.com/other/repo.git it's",
    "git fetch git@github.com:other/repo.git \"it's",
]


@pytest.mark.parametrize("command", FOREIGN_UNSPLIT)
def test_unsplit_command_naming_another_repository_is_refused(command: str) -> None:
    assert any("other/repo" in problem for problem in guard_problems(command))


@pytest.mark.parametrize(
    "command",
    [
        "gh api repos/hungle-agilityio/ai-training/issues -f body=\"it's\nnext\"",
        "gh secret list \"it's",
        "git push origin \"it's",
    ],
)
def test_unsplit_command_that_needs_exact_reading_is_still_refused(command: str) -> None:
    assert guard_problems(command) != []


@pytest.mark.parametrize(
    "command",
    [
        "gh pr merge 5 --merge --body \"it's\nnext\"",
        "gh pr create --title x --body \"it's\nnext\"",
        "gh api repos/hungle-agilityio/ai-training/pulls -f title=\"it's\nnext\"",
        "git push origin \"it's",
    ],
)
def test_unsplit_publish_commands_are_still_refused_in_loop(command: str) -> None:
    assert publish_decision(command) == "deny"


# AC4: writes outside out/, reviews/ and reviewradar/ stay refused for loop builds.


def test_settings_allow_edits_only_in_out_reviews_and_reviewradar() -> None:
    edits = sorted(rule for rule in allow_rules() if rule.startswith(("Edit(", "Write(")))
    assert edits == ["Edit(./out/**)", "Edit(./reviewradar/**)", "Edit(./reviews/**)"]


@pytest.mark.parametrize(
    "rel", [".claude/settings.json", ".claude/hooks/x.py", ".github/workflows/checks.yml"]
)
def test_edit_hook_still_refuses_rule_files_in_loop(rel: str, tmp_path: Path) -> None:
    assert EDIT.evaluate(str(tmp_path / rel), tmp_path, LOOP, no_git_edit) != []
