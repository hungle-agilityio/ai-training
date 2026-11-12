"""The pull request draft can hold a Code review section right after How tested.

Spec: specs/test-harden/spec.md, issue #498 (AC3).
Run: uv run pytest ../plugins/agent-flow/skills/draft-pull-request/tests --no-cov -q
(from the app folder)
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
REVIEW_TEXT = "Level: standard\nRounds: 1\n\nNo findings."
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


# M8: with the option


def test_the_code_review_sits_right_after_how_tested_and_holds_the_files_text(
    tmp_path: Path,
) -> None:
    review = tmp_path / "code-review.md"
    review.write_text(f"\n{REVIEW_TEXT}\n\n")

    body = body_of(tmp_path, code_review=review)

    assert body == HEAD + WHY + TESTED + f"## Code review\n\n{REVIEW_TEXT}\n\n" + TAIL
    assert body.index("## How tested") < body.index("## Code review") < body.index("## Evidence")


def test_the_code_review_comes_before_the_tests_changed_section(tmp_path: Path) -> None:
    review = tmp_path / "code-review.md"
    review.write_text(REVIEW_TEXT)
    changed = tmp_path / "tests-changed.md"
    changed.write_text(TESTS_TEXT)

    body = body_of(tmp_path, code_review=review, tests_changed=changed)

    expected = (
        HEAD
        + WHY
        + TESTED
        + f"## Code review\n\n{REVIEW_TEXT}\n\n"
        + f"## Tests changed after the test author\n\n{TESTS_TEXT}\n\n"
        + TAIL
    )
    assert body == expected
    assert body.index("## Code review") < body.index("## Tests changed")


def test_the_command_line_takes_code_review(tmp_path: Path) -> None:
    review = tmp_path / "code-review.md"
    review.write_text(REVIEW_TEXT)
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
            "--code-review", str(review),
            "--out", str(out),
        ]
    )  # fmt: skip

    body = (out / "pr-body.md").read_text()
    assert code == 0
    assert f"## Code review\n\n{REVIEW_TEXT}\n\n" in body


# M9: without the option


def test_without_the_option_the_body_is_the_one_main_builds_and_has_no_code_review(
    tmp_path: Path,
) -> None:
    body = body_of(tmp_path)

    assert body == HEAD + WHY + TESTED + TAIL
    assert "## Code review" not in body


def test_the_code_review_option_defaults_to_none() -> None:
    import inspect

    parameter = inspect.signature(DRAFT.build_draft).parameters["code_review"]

    assert parameter.default is None
