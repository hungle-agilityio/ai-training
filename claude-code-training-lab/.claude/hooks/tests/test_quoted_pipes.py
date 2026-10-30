"""Tests that the GitHub guard splits commands only on operators outside quotes (#98)."""

from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-github-command-check.py"
ALLOWED = "hungle-agilityio/ai-training"


def load() -> ModuleType:
    spec = util.spec_from_file_location("guard_quoted_pipes", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load()


def decide(command: str, loop: bool = True) -> str:
    def run(args: list[str]) -> tuple[int, str]:
        return (0, "task/93-x") if args[:3] == ["git", "branch", "--show-current"] else (1, "")

    if GUARD.check_command(command, ALLOWED, loop):
        return "deny"
    decision, _ = GUARD.check_publish(command, loop, run, ALLOWED)
    return str(decision)


@pytest.mark.parametrize(
    "command",
    [
        "gh api repos/hungle-agilityio/ai-training/pulls/97/comments --jq '.[] | {id, body}'",
        'gh api repos/hungle-agilityio/ai-training/pulls/97/comments --jq ".[] | .id"',
        "gh api repos/hungle-agilityio/ai-training/issues/97/comments --jq '.[] | .body'",
        'gh issue comment 5 --body "a | b; c && d"',
        "gh run view 40994137438 --log-failed | tail -50",
    ],
)
def test_operators_inside_quotes_do_not_split_the_command(command: str) -> None:
    assert decide(command) == "allow"


@pytest.mark.parametrize(
    "command",
    [
        "gh issue list | gh repo delete x/y",
        'echo "a" ; git push --force',
        "gh issue list && git push origin --delete claude/x",
        "echo 'a | b' | gh api repos/other/repo/issues",
        "gh api repos/hungle-agilityio/ai-training/pulls/1/merge -X PUT --jq '.[] | .a'",
        'gh pr view 1 --json body --jq ".body" | gh pr merge 1 --merge',
    ],
)
def test_operators_outside_quotes_still_split_and_refuse(command: str) -> None:
    assert decide(command) == "deny"


def test_split_keeps_quoted_text_whole() -> None:
    parts = GUARD.split_segments("gh api x --jq '.[] | .a' && echo \"b; c\" | tail")
    assert parts == ["gh api x --jq '.[] | .a' ", ' echo "b; c" ', " tail"]


def test_an_unclosed_quote_still_splits_on_every_operator() -> None:
    assert GUARD.split_segments("gh issue comment 1 --body \"it's | x") == [
        "gh issue comment 1 --body \"it's ",
        " x",
    ]
