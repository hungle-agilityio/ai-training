"""Tests of the push, pull request and merge guard (run with the other hook tests)."""

import json
import os
import subprocess
import sys
from importlib import util
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-github-command-check.py"
SHA = "a1b2c3d4e5f6a7b8c9d0a1b2c3d4e5f6a7b8c9d0"


def load():  # type: ignore[no-untyped-def]
    spec = util.spec_from_file_location("guard_publish", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load()


def pr_json(**changes: object) -> str:
    data: dict[str, object] = {
        "state": "OPEN",
        "headRefName": "feat/20-search",
        "headRefOid": SHA,
        "baseRefName": "main",
        "isCrossRepository": False,
    }
    data.update(changes)
    return json.dumps(data)


def decide(command: str, loop: bool, view: str = "", branch: str = "feat/1-x") -> str:
    def run(args: list[str]) -> tuple[int, str]:
        if args[:3] == ["git", "branch", "--show-current"]:
            return 0, branch
        if args[:3] == ["gh", "pr", "view"]:
            return (0, view) if view else (1, "")
        return 1, ""

    decision, _ = GUARD.check_publish(command, loop, run)
    return str(decision)


MERGE = f"gh pr merge 5 --merge --match-head-commit {SHA}"


def test_ordinary_commands_pass_through() -> None:
    assert decide("git status", False) == "allow"
    assert decide("uv run pytest -q", True) == "allow"
    assert decide("gh pr view 5 --json state", True) == "allow"


def test_push_of_an_issue_branch_asks_outside_the_loop_and_runs_inside_it() -> None:
    assert decide("git push -u origin feat/20-search", False) == "ask"
    assert decide("git push -u origin feat/20-search", True) == "allow"


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push origin HEAD:main",
        "git push origin HEAD:refs/heads/main",
        "git push origin feat/1-x:master",
        "git push origin +feat/1-x",
        "git push origin :feat/1-x",
        "git push origin feat/1-x --force",
        "git push --force-with-lease origin feat/1-x",
        "git push -f origin feat/1-x",
        "git push -fu origin feat/1-x",
        "git push -uf origin feat/1-x",
        "git push -d origin feat/1-x",
        "git push --delete origin feat/1-x",
        "git push --all origin",
        "git push --mirror origin",
    ],
)
def test_dangerous_pushes_are_refused_in_every_mode(command: str) -> None:
    assert decide(command, True) == "deny"
    assert decide(command, False) == "deny"


def test_a_push_that_names_no_branch_checks_the_current_branch() -> None:
    for command in ("git push", "git push origin HEAD", "git push -u origin @"):
        assert decide(command, True, branch="main") == "deny"
        assert decide(command, True, branch="feat/1-x") == "allow"


def test_a_push_must_run_in_the_current_folder() -> None:
    assert decide("git -C ../other push origin feat/1-x", True) == "deny"
    assert decide("cd ../other && git push origin feat/1-x", True) == "deny"


def test_pull_request_creation_asks_outside_the_loop() -> None:
    assert decide("gh pr create --base main --title t --body-file b", False) == "ask"
    assert decide("gh pr create --base main --title t --body-file b", True) == "allow"


def test_the_loop_never_merges() -> None:
    assert decide(MERGE, True, pr_json()) == "deny"


def test_the_owner_merges_with_a_prompt_that_names_the_head_commit() -> None:
    assert decide(MERGE, False, pr_json()) == "ask"
    assert decide(f"gh pr merge 5 --merge --match-head-commit={SHA[:7]}", False, pr_json()) == "ask"


@pytest.mark.parametrize(
    "command",
    [
        "gh pr merge 5",
        "gh pr merge 5 --merge",
        f"gh pr merge 5 --admin --merge --match-head-commit {SHA}",
        f"gh pr merge 5 --squash --match-head-commit {SHA}",
        f"gh pr merge 5 --rebase --match-head-commit {SHA}",
        f"gh pr merge 5 --merge --delete-branch --match-head-commit {SHA}",
        f"gh pr merge 5 --merge --auto --match-head-commit {SHA}",
        f"gh pr merge --merge --match-head-commit {SHA}",
        f"gh pr merge abc --merge --match-head-commit {SHA}",
        "gh pr merge 5 --merge --match-head-commit nothex",
    ],
)
def test_merge_flags_are_exact(command: str) -> None:
    assert decide(command, False, pr_json()) == "deny"


def test_merge_checks_the_pull_request_itself() -> None:
    other_head = pr_json(headRefOid="0" * 40)
    cases = [
        pr_json(state="MERGED"),
        pr_json(headRefName="main"),
        pr_json(headRefName="my-branch"),
        pr_json(baseRefName="develop"),
        pr_json(isCrossRepository=True),
        other_head,
    ]
    for view in cases:
        assert decide(MERGE, False, view) == "deny"


def test_merge_fails_closed_when_the_pull_request_cannot_be_read() -> None:
    assert decide(MERGE, False, view="") == "deny"
    assert decide(MERGE, False, view="not json") == "deny"


def test_merge_cannot_be_chained_with_another_command() -> None:
    assert decide(f"git push origin feat/1-x && {MERGE}", False, pr_json()) == "deny"
    assert decide(f"{MERGE}; echo done", False, pr_json()) == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "gh api --method=PUT repos/o/r/pulls/5/merge",
        "gh api -X PUT repos/o/r/pulls/5/merge",
        "gh api repos/o/r/merges -f base=main -f head=feat/1-x",
        "gh api -X PATCH repos/o/r/git/refs/heads/main -F force=true",
    ],
)
def test_gh_api_is_not_a_side_door_to_merge(command: str) -> None:
    assert decide(command, False) == "deny"
    assert decide(command, True) == "deny"


def test_gh_api_reads_are_untouched() -> None:
    assert decide("gh api repos/o/r/pulls/5", True) == "allow"


def test_setting_the_loop_variable_inside_the_command_does_not_switch_loop_mode_on() -> None:
    assert decide(f"REVIEWRADAR_LOOP=1 {MERGE}", False, pr_json()) == "ask"


def run_hook(command: str, cwd: Path, loop: bool) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key != "REVIEWRADAR_LOOP"}
    if loop:
        env["REVIEWRADAR_LOOP"] = "1"
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    return subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_the_hook_asks_with_the_documented_json_and_exit_zero(tmp_path: Path) -> None:
    done = run_hook("git push -u origin feat/1-x", tmp_path, loop=False)
    assert done.returncode == 0
    reply = json.loads(done.stdout)["hookSpecificOutput"]
    assert reply["hookEventName"] == "PreToolUse"
    assert reply["permissionDecision"] == "ask"


def test_the_hook_blocks_with_exit_two_and_a_reason(tmp_path: Path) -> None:
    done = run_hook("git push --force origin feat/1-x", tmp_path, loop=True)
    assert done.returncode == 2
    assert "force" in done.stderr


def test_the_hook_stays_silent_for_a_loop_push(tmp_path: Path) -> None:
    done = run_hook("git push -u origin feat/1-x", tmp_path, loop=True)
    assert done.returncode == 0
    assert done.stdout == ""
