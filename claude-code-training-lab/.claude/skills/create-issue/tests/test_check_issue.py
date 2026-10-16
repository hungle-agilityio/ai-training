"""Tests of the issue checker. Run: uv run pytest .claude/skills/create-issue/tests --no-cov -q"""

import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[2]


def load() -> ModuleType:
    spec = util.spec_from_file_location("check_issue", SKILL / "check_issue.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()


def problems(text: str) -> list[str]:
    result: list[str] = CHECK.check_text(text)
    return result


BUG = """# [BUG] Dashboard shows 3 instead of 3.67

- **Reporter:** Maria, manager
- **Reported on:** 2026-10-16
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `wrong-data`, `severity: medium`, `reproduced`, `env: dev`

## Summary

The Riverside score must show 3.67.

## Steps to reproduce

1. Open the dashboard.
2. Look at Riverside.

## Expected result

3.67

## Actual result

3

## Environment

dev

## Attachments

None yet.
"""

FEATURE = """# [FEAT] Filter reviews by week

- **Reporter:** Maria, manager
- **Reported on:** 2026-10-16
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`

## Summary

Managers need to see one week at a time on the reviews page.

## Acceptance criteria

- When a week is chosen, the screen must show only reviews of that week.
- When there is nothing to show, the screen must say "No reviews found".

## What exists today

1. Open /reviews/.
2. There is no week filter.

## How to check it when built

1. Open /reviews/ and choose a week.

## Expected result

Only that week.

## Environment

dev

## Attachments

None yet.
"""

TASK = """# [TASK] Clean demo data

- **Requester:** Hung, developer
- **Reported on:** 2026-10-16
- **Type:** Task
- **Labels:** `task`, `docs`

## Summary

Nothing visible to users.

## Scope

- **Included:** the demo data
- **Not included:** real data

## Done when

- [ ] The demo data has 10 reviews.

## Steps to check the result

1. Run the demo data command.

## Expected result

10 reviews.

## Environment

dev

## Attachments

None.
"""


def epic(children: int = 3) -> str:
    items = "\n".join(f"- [ ] Child {i}" for i in range(children))
    return f"""# [EPIC] Move to GitHub

- **Owner:** Hung, developer
- **Reported on:** 2026-10-16
- **Type:** Epic
- **Labels:** `epic`, `hosting`

## Goal

The project lives on GitHub.

## Why

GitLab is dropped.

## Scope

- **Included:** the move
- **Not included:** new features

## Success criteria

- [ ] GitHub shows the full history.

## Child issues

{items}

## Dependencies and risks

| Item | Kind |
|---|---|
| Token | dependency |

## Open questions

| Question | Proposal |
|---|---|
| Licence? | none |

## Scope changes

| Date | Change | Reason |
|---|---|---|
| 2026-10-16 | created | start |

## Environment

dev

## Attachments

None.
"""


@pytest.mark.parametrize("text", [BUG, FEATURE, TASK, epic(), epic(10)])
def test_complete_issues_pass(text: str) -> None:
    assert problems(text) == []


def test_title_without_a_known_type_is_refused() -> None:
    assert problems(BUG.replace("# [BUG] ", "# ")) != []


def test_type_label_must_match_the_title() -> None:
    assert problems(BUG.replace("`bug`, ", "`task`, ")) != []


def test_missing_section_is_named() -> None:
    result = problems(BUG.replace("## Actual result\n\n3\n\n", ""))

    assert any("Actual result" in line for line in result)


def test_empty_section_is_refused() -> None:
    result = problems(BUG.replace("## Expected result\n\n3.67\n", "## Expected result\n\n"))

    assert any("Expected result" in line for line in result)


def test_left_over_template_placeholder_is_refused() -> None:
    result = problems(BUG.replace("3.67\n\n## Actual", "\\<exact value>\n\n## Actual"))

    assert any("placeholder" in line for line in result)


def test_issue_without_an_area_label_is_refused() -> None:
    result = problems(TASK.replace("`task`, `docs`", "`task`"))

    assert any("area" in line for line in result)


def test_bug_needs_kind_severity_and_reproduction_labels() -> None:
    result = problems(BUG.replace("`wrong-data`, `severity: medium`, `reproduced`, ", ""))
    text = " ".join(result)

    assert "kind" in text and "severity" in text and "reproduc" in text


def test_bug_needs_numbered_steps() -> None:
    result = problems(BUG.replace("1. Open the dashboard.\n2. Look at Riverside.", "Just open it."))

    assert any("steps" in line.lower() for line in result)


def test_feature_needs_acceptance_criteria_in_the_when_form_and_the_empty_case() -> None:
    no_when = problems(FEATURE.replace("- When a week is chosen", "- A week is chosen"))
    no_empty = problems(
        FEATURE.replace(
            'When there is nothing to show, the screen must say "No reviews found".',
            'When a week has no match, the screen must say "Sorry".',
        )
    )

    assert any("When" in line for line in no_when)
    assert any("empty" in line.lower() or "nothing" in line.lower() for line in no_empty)


def test_task_needs_a_done_when_checkbox() -> None:
    result = problems(
        TASK.replace("- [ ] The demo data has 10 reviews.", "The demo data has 10 reviews.")
    )

    assert any("Done when" in line for line in result)


@pytest.mark.parametrize("children", [2, 11])
def test_epic_needs_between_three_and_ten_children(children: int) -> None:
    assert any("children" in line for line in problems(epic(children)))


def test_real_epics_pass() -> None:
    for path in sorted((ROOT / "docs/learning/epics").glob("*.md")):
        if path.name == "README.md":
            continue
        assert problems(path.read_text()) == [], path.name


def test_the_templates_are_not_publishable_because_they_still_hold_placeholders() -> None:
    for name in ("bug", "feature", "task", "epic"):
        path = ROOT / f"docs/app/templates/{name}.md"
        assert problems(path.read_text()) != [], name


def test_command_line_exit_codes_and_message() -> None:
    script = str(SKILL / "check_issue.py")
    bad = SKILL / "tests" / "_bad.md"
    good = SKILL / "tests" / "_good.md"
    try:
        bad.write_text(BUG.replace("## Environment\n\ndev\n\n", ""))
        good.write_text(BUG)
        failed = subprocess.run(
            [sys.executable, "-I", script, str(bad)], capture_output=True, text=True, check=False
        )
        passed = subprocess.run(
            [sys.executable, "-I", script, str(good)], capture_output=True, text=True, check=False
        )
    finally:
        bad.unlink(missing_ok=True)
        good.unlink(missing_ok=True)

    assert failed.returncode == 1 and "Environment" in failed.stdout
    assert passed.returncode == 0
