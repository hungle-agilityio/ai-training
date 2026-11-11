"""The spec templates make room for the decisions a build takes.

Spec: specs/build-trust/spec.md (AC18 to AC21; rows M18 to M20 of its test matrix).
Run: pytest ops/tests/test_build_trust_templates.py
"""

from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2]
TEMPLATES = APP / "docs" / "app" / "templates" / "spec"
SPEC = TEMPLATES / "spec.md"
TASKS = TEMPLATES / "tasks.md"
SPECS_README = APP / "specs" / "README.md"

BUILD_DECISIONS = "## Decisions during build"
LINK_LINE = "See [decisions/](decisions/): one file per task, written by its build."
COMMENT_LINE = (
    "Each task of a full-lane spec lists its decisions file "
    "specs/<feature>/decisions/T<k>.md (NEW): its build writes there every decision it takes, "
    'or "No decision beyond the issue." (ADR-027).'
)
RISK_LINE = "- **Risk:** low | medium | high (high: the build stops for plan approval)"
README_BULLET = (
    "- `decisions/`: one file per task, T<k>.md, written by its build in its own pull request: "
    "the decisions taken while building (ADR-027)."
)
FILES = "- **Files likely touched:**"


def task_entries() -> dict[str, list[str]]:
    """The lines of each `## T<k>:` entry of the tasks template, by task name."""
    entries: dict[str, list[str]] = {}
    name = ""
    for line in TASKS.read_text().splitlines():
        found = re.match(r"## (T\d+):", line)
        if found:
            name = found.group(1)
            entries[name] = []
        elif line.startswith("## "):
            name = ""
        elif name:
            entries[name].append(line)
    return entries


def one_line(lines: list[str], start: str) -> str:
    found = [line for line in lines if line.startswith(start)]
    assert len(found) == 1
    return found[0]


# AC1 (M18): the spec template links the decisions files


def test_spec_template_has_decisions_during_build_between_decisions_and_design() -> None:
    names = [line for line in SPEC.read_text().splitlines() if line.startswith("## ")]
    at = names.index(BUILD_DECISIONS)
    assert names[at - 1 : at + 2] == ["## Decisions", BUILD_DECISIONS, "## Design"]
    assert names.count(BUILD_DECISIONS) == 1


def test_spec_template_section_holds_only_the_link_line() -> None:
    body = SPEC.read_text().split(f"\n{BUILD_DECISIONS}\n", 1)[1].split("\n## ", 1)[0]
    assert body == f"\n{LINK_LINE}\n"


def test_spec_template_decisions_table_ends_right_before_the_new_section() -> None:
    lines = SPEC.read_text().splitlines()
    at = lines.index(BUILD_DECISIONS)
    assert lines[at - 1] == ""
    assert lines[at - 2] == "| <question settled in grill-me> | <option> | <option> | <reason> |"


def test_spec_template_keeps_its_other_sections_in_order() -> None:
    names = [line for line in SPEC.read_text().splitlines() if line.startswith("## ")]
    assert names == [
        "## Summary",
        "## User story",
        "## Acceptance criteria",
        "## Edge cases",
        "## Decisions",
        BUILD_DECISIONS,
        "## Design",
        "## Open questions",
    ]


# AC2 (M19): the tasks template lists the decisions file and names the plan stop


def test_tasks_template_has_two_task_entries() -> None:
    assert list(task_entries()) == ["T1", "T2"]


def test_each_task_lists_its_decisions_file_last_as_new() -> None:
    files = {name: one_line(lines, FILES) for name, lines in task_entries().items()}
    assert files == {
        "T1": f"{FILES} `reviews/services.py`, `reviews/tests/unit/test_<name>.py`, "
        "`specs/<feature>/decisions/T1.md` (NEW)",
        "T2": f"{FILES} <paths>, `specs/<feature>/decisions/T2.md` (NEW)",
    }


def test_tasks_template_top_comment_explains_the_decisions_file() -> None:
    text = TASKS.read_text()
    top = text.split("<!--", 1)[1].split("-->", 1)[0]
    assert [line.strip() for line in top.splitlines()].count(COMMENT_LINE) == 1
    assert text.count(COMMENT_LINE) == 1


def test_each_task_risk_line_names_the_plan_stop() -> None:
    risks = {name: one_line(lines, "- **Risk:**") for name, lines in task_entries().items()}
    assert risks == {"T1": RISK_LINE, "T2": RISK_LINE}


def test_matrix_rows_stay_right_after_the_acs() -> None:
    for lines in task_entries().values():
        acs = next(i for i, line in enumerate(lines) if line.startswith("- **ACs:**"))
        assert lines[acs + 1].startswith("- **Matrix rows:**")


def test_each_task_keeps_its_fields_in_order() -> None:
    for lines in task_entries().values():
        fields = [line.split(":**")[0] for line in lines if line.startswith("- **")]
        assert fields == [
            "- **ACs",
            "- **Matrix rows",
            "- **Files likely touched",
            "- **Depends on",
            "- **Risk",
            "- **needs-ui",
            "- **Screens to capture",
            "- **Label",
        ]


# AC3 (M20): the specs README names the decisions folder


def test_specs_readme_has_the_decisions_bullet_right_after_tasks() -> None:
    bullets = [line for line in SPECS_README.read_text().splitlines() if line.startswith("- `")]
    tasks = [i for i, line in enumerate(bullets) if line.startswith("- `tasks.md`:")]
    assert len(tasks) == 1
    assert bullets[tasks[0] + 1] == README_BULLET
    assert bullets.count(README_BULLET) == 1


def test_specs_readme_keeps_its_bullets_in_one_list() -> None:
    lines = SPECS_README.read_text().splitlines()
    starts = [line.split(":")[0] for line in lines if line.startswith("- `")]
    assert starts == [
        "- `intent.md`",
        "- `spec.md`",
        "- `test-matrix.md`",
        "- `tasks.md`",
        "- `decisions/`",
    ]
    at = lines.index(README_BULLET)
    assert lines[at - 1].startswith("- `tasks.md`:") and lines[at + 1] == ""
