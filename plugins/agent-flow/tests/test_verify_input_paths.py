"""The verify report's input files live in out/verify-input/, so no long path is needed (#334).

Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

from collections.abc import Callable
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
CRITERIA_FILE = "`out/verify-input/criteria.json`"
SPEC_FILE = "`out/verify-input/spec.json`"
Section = Callable[[], str]


def skill_text(name: str) -> str:
    return (PLUGIN / "skills" / name / "SKILL.md").read_text()


def between(text: str, start: str, end: str) -> str:
    first = text.index(start)
    return text[first : text.index(end, first)]


def verify_step() -> str:
    return between(skill_text("work-queue"), "`build-verify-report` writes one report", "2. `share")


def redo_round() -> str:
    return between(skill_text("work-queue"), "**Open change requests** (above)", "**Done:**")


def report_skill() -> str:
    return skill_text("build-verify-report")


SECTIONS = [verify_step, redo_round, report_skill]


@pytest.mark.parametrize("section", SECTIONS)
def test_the_criteria_and_screens_files_are_written_to_verify_input(section: Section) -> None:
    text = section()

    assert CRITERIA_FILE in text
    assert SPEC_FILE in text
    assert "Write tool" in text


@pytest.mark.parametrize("section", SECTIONS)
def test_the_report_runs_with_relative_paths_as_one_plain_command(section: Section) -> None:
    text = section()

    assert "relative paths" in text
    assert "one plain command" in text


@pytest.mark.parametrize("section", SECTIONS)
def test_the_scratchpad_is_gone_from_the_verify_step(section: Section) -> None:
    assert "scratchpad" not in section().lower()
