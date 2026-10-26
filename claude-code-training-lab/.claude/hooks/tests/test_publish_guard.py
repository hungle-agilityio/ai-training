"""Tests of the push, pull request and merge guard (run with the other hook tests)."""

import json
from importlib import util
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-github-command-check.py"
OWNER = "hungle-agilityio"


def load():  # type: ignore[no-untyped-def]
    spec = util.spec_from_file_location("guard_publish", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load()


def pr_json(
    comments: list[dict[str, object]] | None = None,
    branch: str = "feat/20-search",
    state: str = "OPEN",
) -> str:
    return json.dumps(
        {
            "state": state,
            "headRefName": branch,
            "commits": [{"committedDate": "2026-10-26T10:00:00Z"}],
            "comments": comments or [],
        }
    )


def comment(body: str, login: str = OWNER, at: str = "2026-10-26T11:00:00Z") -> dict[str, object]:
    return {"author": {"login": login}, "body": body, "createdAt": at}


def decide(command: str, loop: bool, view: str = "", branch: str = "feat/1-x") -> str:
    def run(args: list[str]) -> tuple[int, str]:
        if args[:3] == ["git", "branch", "--show-current"]:
            return 0, branch
        if args[:3] == ["gh", "pr", "view"]:
            return (0, view) if view else (1, "")
        return 1, ""

    decision, _ = GUARD.check_publish(command, loop, OWNER, run)
    return str(decision)


def test_ordinary_commands_pass_through() -> None:
    assert decide("git status", False) == "allow"
    assert decide("uv run pytest -q", True) == "allow"


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
        "git push --delete origin feat/1-x",
    ],
)
def test_dangerous_pushes_are_refused_in_every_mode(command: str) -> None:
    assert decide(command, True) == "deny"
    assert decide(command, False) == "deny"


def test_bare_push_is_refused_on_main_and_allowed_on_a_branch() -> None:
    assert decide("git push", True, branch="main") == "deny"
    assert decide("git push", True, branch="feat/1-x") == "allow"


def test_pull_request_creation_asks_outside_the_loop() -> None:
    assert decide("gh pr create --base main --title t --body b", False) == "ask"
    assert decide("gh pr create --base main --title t --body b", True) == "allow"


def test_merge_asks_outside_the_loop_even_with_a_comment() -> None:
    view = pr_json([comment("/merge")])
    assert decide("gh pr merge 5 --merge", False, view) == "ask"


def test_merge_in_loop_needs_the_owner_comment_after_the_last_commit() -> None:
    assert decide("gh pr merge 5 --merge", True, pr_json([comment("/merge")])) == "allow"
    assert decide("gh pr merge 5 --merge", True, pr_json([])) == "deny"
    old = comment("/merge", at="2026-10-26T09:00:00Z")
    assert decide("gh pr merge 5 --merge", True, pr_json([old])) == "deny"


def test_merge_ignores_other_authors_and_the_loops_own_comments() -> None:
    other = comment("/merge", login="someone-else")
    marked = comment("<!-- work-queue -->\n/merge")
    quoted = comment("reply /merge to merge")
    for item in (other, marked, quoted):
        assert decide("gh pr merge 5 --merge", True, pr_json([item])) == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "gh pr merge 5",
        "gh pr merge 5 --admin --merge",
        "gh pr merge 5 --squash",
        "gh pr merge 5 --rebase",
        "gh pr merge 5 --merge --delete-branch",
        "gh pr merge 5 --merge --auto",
        "gh pr merge --merge",
        "gh pr merge abc --merge",
    ],
)
def test_merge_flags_are_exact(command: str) -> None:
    assert decide(command, True, pr_json([comment("/merge")])) == "deny"


def test_merge_only_for_issue_branches_and_open_pull_requests() -> None:
    ok = [comment("/merge")]
    assert decide("gh pr merge 5 --merge", True, pr_json(ok, branch="main")) == "deny"
    assert decide("gh pr merge 5 --merge", True, pr_json(ok, branch="my-branch")) == "deny"
    assert decide("gh pr merge 5 --merge", True, pr_json(ok, state="MERGED")) == "deny"


def test_merge_fails_closed_when_the_pull_request_cannot_be_read() -> None:
    assert decide("gh pr merge 5 --merge", True, view="") == "deny"
    assert decide("gh pr merge 5 --merge", True, view="not json") == "deny"


def test_setting_the_loop_variable_inside_the_command_does_not_switch_loop_mode_on() -> None:
    view = pr_json([comment("/merge")])
    assert decide("REVIEWRADAR_LOOP=1 gh pr merge 5 --merge", False, view) == "ask"
