"""#407: a build fixes technical stops itself; the epic pull request lists those fixes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ops import epic_pull_request
from ops.tests.test_epic_pull_request import (
    EPIC,
    NEW_PR,
    home,
    host_for,
    the_epic_pr,
    tick,
    two_merged,
)

__all__ = ["home"]  # the fixture comes from the epic pull request tests

PLUGIN = Path(__file__).resolve().parents[3] / "plugins" / "agent-flow"
URL = "https://github.com/o/r/issues/5#issuecomment-77"


def self_fix(url: str = URL, created: str = "2026-11-10T04:00:00Z") -> dict[str, Any]:
    body = "<!-- work-queue -->\n<!-- self-fix -->\n## Decisions\n\n| a | b | c |\n"
    return {"author": {"login": "x"}, "body": body, "createdAt": created, "url": url}


def plain(url: str = "https://github.com/o/r/issues/5#issuecomment-1") -> dict[str, Any]:
    return {
        "body": "<!-- work-queue -->\nRetry 1 of 3.",
        "createdAt": "2026-11-10T00:00:00Z",
        "url": url,
    }


# AC4: the epic pull request lists every self-decided fix


def test_the_epic_body_lists_each_self_fixed_task_with_its_link(home: Path) -> None:
    host = host_for(*two_merged(), issue_comments={5: [plain(), self_fix()], 6: [plain()]})
    tick(host, home)
    body = host.bodies[0]
    assert f"## Self-decided fixes\n\n- #5: {URL}\n" in body
    assert body.index("## Self-decided fixes") < body.index("Closes #5")


def test_no_self_fix_says_none(home: Path) -> None:
    host = host_for(*two_merged())
    tick(host, home)
    assert "## Self-decided fixes\n\nNone.\n" in host.bodies[0]


def test_a_task_with_two_self_fixes_lists_both(home: Path) -> None:
    second = "https://github.com/o/r/issues/5#issuecomment-99"
    host = host_for(*two_merged(), issue_comments={5: [self_fix(), self_fix(second)]})
    tick(host, home)
    assert f"- #5: {URL}\n- #5: {second}\n" in host.bodies[0]


def test_a_task_joining_later_refreshes_the_section(home: Path) -> None:
    host = host_for(
        *two_merged(), the_epic_pr(), issue_comments={6: [self_fix(URL.replace("5#", "6#"))]}
    )
    tick(host, home)
    body = host.edits[-1]
    assert (
        "## Self-decided fixes\n\n- #6: https://github.com/o/r/issues/6#issuecomment-77\n" in body
    )
    assert body.count("## Self-decided fixes") == 1


def test_only_a_comment_starting_with_both_markers_counts() -> None:
    late = {"body": "Hello\n<!-- work-queue -->\n<!-- self-fix -->", "url": "u"}
    assert epic_pull_request.self_fix_urls([plain(), late, self_fix()]) == [URL]


def test_the_section_helper_replaces_an_old_section() -> None:
    body = "x\n\n## Self-decided fixes\n\n- #1: old\n\nCloses #1\n"
    done = epic_pull_request.with_self_fixes(body, ["- #2: new"])
    assert done == "x\n\n## Self-decided fixes\n\n- #2: new\n\nCloses #1\n"


# AC1 to AC3: the work-queue self-fix step, the pull request section, the plugin version


def skill(name: str) -> str:
    return (PLUGIN / "skills" / name / "SKILL.md").read_text()


def test_work_queue_has_a_self_fix_branch_with_only_technical_cases() -> None:
    text = skill("work-queue")
    assert "<!-- self-fix -->" in text
    for words in (
        "## Existing tests that change",
        "old → new",
        "not guarded",
        "narrower technical reading",
        "recommended option",
        "never self-fixed again",
        "grows with the data",
    ):
        assert words in text


def test_work_queue_self_fix_ends_the_run_with_agent_ready_and_no_pull_request() -> None:
    step = re.search(r"\*\*Self-fix\.\*\*(.*?)(?=\n\d+\. \*\*|\n## )", skill("work-queue"), re.S)
    assert step is not None
    text = step.group(1)
    assert "agent:ready" in text and "agent:running" in text and "without a pull request" in text
    assert "## Decisions" in text


def test_create_pull_request_adds_the_self_fix_section_outside_an_epic() -> None:
    assert "## Self-decided fixes" in skill("create-pull-request")


def test_the_plugin_version_went_up_one_patch() -> None:
    version = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
    assert tuple(int(p) for p in version.split(".")) >= (1, 0, 16)


def test_the_epic_tests_still_use_the_same_numbers() -> None:
    assert (EPIC, NEW_PR) == (236, 30)
