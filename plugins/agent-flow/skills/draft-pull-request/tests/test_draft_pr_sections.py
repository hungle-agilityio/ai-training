"""The pull request draft can hold the plan and the tests changed after the test author.

Run: uv run pytest ../plugins/agent-flow/skills/draft-pull-request/tests --no-cov -q
(from the app folder)
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
PLAN_TEXT = "1. Change the rule.\n2. Write the test first.\n3. Run the checks."
TESTS_TEXT = "- `tests/test_a.py::test_a`: AC1, the expected value was wrong."
LINK = "https://claude.ai/artifact/x"


def load() -> ModuleType:
    spec = util.spec_from_file_location("draft_pr", SKILL / "draft_pr.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DRAFT = load()

HEAD = "## What\n\nA rule changes.\n\n"
WHY = "## Why\n\nManagers need it.\n\n"
TESTED = (
    "## How tested\n\nVerdict: **PASS**\n\n| Axis | Result | Evidence |\n|---|---|---|\n"
    "| Lint | PASS | All checks passed! |\n\n"
)
TAIL = (
    f"## Evidence\n\nReport (private link): {LINK}\n\nNothing visible to users.\n\n"
    "## One concern\n\n- [ ] This pull request does one thing only\n\nCloses #12\n"
)


def make_report(folder: Path) -> Path:
    folder.mkdir(parents=True)
    report: dict[str, Any] = {
        "verdict": "PASS",
        "share": {"url": LINK, "date": "2026-11-12"},
        "axes": [{"name": "Lint", "status": "PASS", "evidence": "All checks passed!"}],
    }
    (folder / "report.json").write_text(json.dumps(report))
    return folder


def body_of(tmp_path: Path, **extra: Any) -> str:
    result = DRAFT.build_draft(
        "[TASK] A rule",
        "A rule changes.",
        "Managers need it.",
        12,
        make_report(tmp_path / "report"),
        None,
        True,
        tmp_path / "out",
        **extra,
    )
    assert result["complete"]
    return (tmp_path / "out" / "pr-body.md").read_text()


def test_without_the_two_files_the_body_is_the_one_main_builds(tmp_path: Path) -> None:
    assert body_of(tmp_path) == HEAD + WHY + TESTED + TAIL


def test_the_plan_sits_between_what_and_why_and_holds_the_files_text(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(f"\n{PLAN_TEXT}\n\n")

    body = body_of(tmp_path, plan=plan)

    assert body == HEAD + f"## Plan\n\n{PLAN_TEXT}\n\n" + WHY + TESTED + TAIL
    assert body.index("## What") < body.index("## Plan") < body.index("## Why")


def test_the_tests_changed_section_sits_right_after_how_tested(tmp_path: Path) -> None:
    changed = tmp_path / "tests-changed.md"
    changed.write_text(TESTS_TEXT + "\n")

    body = body_of(tmp_path, tests_changed=changed)

    section = f"## Tests changed after the test author\n\n{TESTS_TEXT}\n\n"
    assert body == HEAD + WHY + TESTED + section + TAIL
    assert body.index("## How tested") < body.index("## Tests changed") < body.index("## Evidence")


def test_both_files_give_both_sections_in_their_places(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(PLAN_TEXT)
    changed = tmp_path / "tests-changed.md"
    changed.write_text("None.")

    body = body_of(tmp_path, plan=plan, tests_changed=changed)

    expected = (
        HEAD
        + f"## Plan\n\n{PLAN_TEXT}\n\n"
        + WHY
        + TESTED
        + "## Tests changed after the test author\n\nNone.\n\n"
        + TAIL
    )
    assert body == expected


def test_the_command_line_takes_plan_and_tests_changed(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(PLAN_TEXT)
    changed = tmp_path / "tests-changed.md"
    changed.write_text("None.")
    make_report(tmp_path / "report")
    out = tmp_path / "out"

    code = DRAFT.main(
        [
            "--title", "[TASK] A rule",
            "--what", "A rule changes.",
            "--why", "Managers need it.",
            "--issue", "12",
            "--report", str(tmp_path / "report"),
            "--no-visual",
            "--plan", str(plan),
            "--tests-changed", str(changed),
            "--out", str(out),
        ]
    )  # fmt: skip

    body = (out / "pr-body.md").read_text()
    assert code == 0
    assert f"## Plan\n\n{PLAN_TEXT}\n\n" in body
    assert "## Tests changed after the test author\n\nNone.\n\n" in body
