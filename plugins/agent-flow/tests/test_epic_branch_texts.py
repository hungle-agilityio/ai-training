"""Builds can start from an epic branch and open their pull request into it (#262, ADR-021).

Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
WORK_QUEUE = (PLUGIN / "skills" / "work-queue" / "SKILL.md").read_text()
CREATE_PR = (PLUGIN / "skills" / "create-pull-request" / "SKILL.md").read_text()
EPIC_PROMPT = (
    "Stacked on epic branch epic/<N>-<slug>: branch from origin/epic/<N>-<slug> and open the "
    "pull request into epic/<N>-<slug>."
)
EPIC_LINE = "Stacked on #<P1>, #<P2> through epic/<N>-<slug> (merge those first)."
EPIC_REDO = "/redo merge origin/epic/<N>-<slug> into this branch and fix the conflict"


def test_work_queue_names_the_epic_prompt_and_where_to_branch() -> None:
    assert EPIC_PROMPT in WORK_QUEUE
    assert "origin/epic/<N>-<slug>" in WORK_QUEUE
    assert "gh pr create --base epic/<N>-<slug>" in WORK_QUEUE


def test_work_queue_handles_the_epic_conflict_request_without_a_rebase() -> None:
    assert EPIC_REDO in WORK_QUEUE
    section = WORK_QUEUE[WORK_QUEUE.index(EPIC_REDO) - 400 : WORK_QUEUE.index(EPIC_REDO) + 400]
    assert "never a rebase" in section


def test_pull_requests_carry_the_epic_stacked_line() -> None:
    assert EPIC_LINE in WORK_QUEUE
    assert EPIC_LINE in CREATE_PR
    assert "ADR-021" in CREATE_PR


def test_the_plugin_version_is_at_least_1_0_3() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    version = tuple(int(part) for part in manifest["version"].split("."))
    assert version >= (1, 0, 3)
