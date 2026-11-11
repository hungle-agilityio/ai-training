"""The plugin texts name a project's folders by their flow-config key, never by a fixed path.

Spec: specs/project-layout/spec.md (AC9 to AC11).
Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
FIXED_PATHS = (".claude/knowledge/decisions", "docs/app/templates", "specs/<feature>")
TEXTS = sorted(
    path
    for folder in ("agents", "commands", "skills")
    for path in (PLUGIN / folder).rglob("*.md")
    if path.is_file()
)
README = PLUGIN / "README.md"


@pytest.mark.parametrize("path", TEXTS, ids=lambda p: str(p.relative_to(PLUGIN)))
def test_no_text_names_a_fixed_layout_path(path: Path) -> None:
    text = path.read_text()
    assert [fixed for fixed in FIXED_PATHS if fixed in text] == []


def test_readme_names_each_default_once_in_its_layout_table() -> None:
    text = README.read_text()
    assert all(text.count(fixed) <= 1 for fixed in FIXED_PATHS)
    assert "| `decisions_dir` |" in text
    assert "| `templates_dir` |" in text


def test_spec_rule_names_the_spec_pr_folders_by_key() -> None:
    assert "a spec pull request changes only the folders of `paths.spec_pr_dirs`" in (
        README.read_text()
    )


def test_plan_is_saved_only_when_plans_dir_is_set() -> None:
    plan = (PLUGIN / "commands" / "plan.md").read_text()
    planner = (PLUGIN / "agents" / "planner.md").read_text()
    for text in (plan, planner):
        assert "`<plans_dir>/<issue number>-<short-description>.md`" in text
    assert "When it is empty, save nothing." in plan


def test_texts_name_the_decisions_and_templates_keys() -> None:
    assert "`paths.decisions_dir`" in (PLUGIN / "commands" / "learn.md").read_text()
    assert "`paths.templates_dir`" in (PLUGIN / "skills" / "write-issue" / "SKILL.md").read_text()
