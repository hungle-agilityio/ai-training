"""A loop build writes the verify report's criteria file from the work-queue skill alone (#321).

Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
CRITERIA_KEYS = ("text", "status", "evidence")
STATUS_WORDS = ("PASS", "FAIL", "NOT CONFIGURED")


def skill_text(name: str) -> str:
    return (PLUGIN / "skills" / name / "SKILL.md").read_text()


def verify_step(text: str) -> str:
    start = text.index("`build-verify-report` writes one report")
    end = text.index("2. `share-report`", start)
    return text[start:end]


def criteria_block(text: str) -> str:
    found = re.search(r'\{"criteria": \[.*?\]\}', text, re.DOTALL)
    assert found is not None
    return found.group(0)


def block_keys(block: str) -> set[str]:
    return set(re.findall(r'"(\w+)"\s*:', block))


def test_verify_step_gives_the_full_report_command() -> None:
    step = verify_step(skill_text("work-queue"))

    assert '--title "<issue title>"' in step
    assert "--criteria <criteria file>" in step
    assert "--no-ui" in step
    assert "--browser --spec <file>" in step


def test_verify_step_shows_the_criteria_file_format() -> None:
    step = verify_step(skill_text("work-queue"))
    block = criteria_block(step)

    assert block_keys(block) == {"criteria", *CRITERIA_KEYS, "check_yourself"}
    for word in STATUS_WORDS:
        assert f"`{word}`" in step
    assert '"Done when"' in step
    assert "How to check it when built" in step


def test_verify_step_never_runs_the_report_without_criteria() -> None:
    step = verify_step(skill_text("work-queue"))

    assert "never run `build_report.py` without `--criteria`" in step.lower()
    assert "no need to read another skill's files" in step


def test_criteria_format_matches_the_build_verify_report_skill() -> None:
    queue = criteria_block(verify_step(skill_text("work-queue")))
    report = criteria_block(skill_text("build-verify-report"))

    assert block_keys(queue) == block_keys(report)
    for word in STATUS_WORDS:
        assert f"`{word}`" in skill_text("build-verify-report")


def test_plugin_version_is_raised_for_the_criteria_format() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())

    assert manifest["version"] == "1.0.10"
