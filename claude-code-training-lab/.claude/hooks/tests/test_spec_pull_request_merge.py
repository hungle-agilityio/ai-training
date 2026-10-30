"""Tests that a spec pull request (branch task/spec-<name>) can be merged after approval."""

import json
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-github-command-check.py"
SHA = "a1b2c3d4e5f6a7b8c9d0a1b2c3d4e5f6a7b8c9d0"
MERGE = f"gh pr merge 77 --merge --match-head-commit {SHA}"


def load() -> ModuleType:
    spec = util.spec_from_file_location("guard_spec_merge", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load()


def decide(branch: str, loop: bool) -> str:
    view = json.dumps(
        {
            "state": "OPEN",
            "headRefName": branch,
            "headRefOid": SHA,
            "baseRefName": "main",
            "isCrossRepository": False,
        }
    )

    def run(args: list[str]) -> tuple[int, str]:
        return (0, view) if args[:3] == ["gh", "pr", "view"] else (1, "")

    decision, _ = GUARD.check_publish(MERGE, loop, run, "hungle-agilityio/ai-training")
    return str(decision)


@pytest.mark.parametrize("branch", ["task/spec-loop-ux", "task/spec-tick-hardening-ac4"])
def test_a_spec_branch_merge_asks_outside_the_loop(branch: str) -> None:
    assert decide(branch, loop=False) == "ask"


def test_an_issue_branch_merge_still_asks() -> None:
    assert decide("feat/61-page-not-found", loop=False) == "ask"


@pytest.mark.parametrize(
    "branch", ["spec/loop-ux", "claude/project-thread-x", "task/x", "task/spec-"]
)
def test_other_branches_are_still_refused(branch: str) -> None:
    assert decide(branch, loop=False) == "deny"


def test_the_loop_never_merges_a_spec_branch() -> None:
    assert decide("task/spec-loop-ux", loop=True) == "deny"
