"""Skills run their scripts from the installed plugin, as one plain command (#230).

Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILLS = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
SCRIPT_SKILLS = ("build-verify-report", "draft-pull-request", "create-issue", "share-report")
REPOSITORY_PATHS = ("../plugins/agent-flow/skills", "plugins/agent-flow/skills/")
INSTALLED_RULE = "base directory"
PLAIN_RULE = "no pipe"


def skill_text(name: str) -> str:
    return (PLUGIN / "skills" / name / "SKILL.md").read_text()


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_no_skill_runs_a_script_from_the_repository_copy(path: Path) -> None:
    text = path.read_text()

    assert [found for found in REPOSITORY_PATHS if found in text] == []


@pytest.mark.parametrize("name", SCRIPT_SKILLS)
def test_a_script_skill_says_to_run_from_the_installed_plugin(name: str) -> None:
    text = skill_text(name)

    assert INSTALLED_RULE in text
    assert PLAIN_RULE in text


def test_work_queue_gives_the_report_script_from_its_own_folder() -> None:
    text = skill_text("work-queue")

    assert "<this skill's folder>/../build-verify-report/build_report.py" in text
    assert INSTALLED_RULE in text
    assert PLAIN_RULE in text
