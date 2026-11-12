"""The plugin's skills, commands and sub-agents name no project: they point to the project's files.

Run: uv run pytest ../plugins/agent-flow/tests --no-cov -q (from the app folder)
"""

from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
FOLDERS = ("skills", "commands", "agents")
PROJECT_WORDS = ("ReviewRadar", "Django", "reviews/", "rounded_average", "claude-code-training-lab")
FILES = sorted(
    path
    for folder in FOLDERS
    for path in (PLUGIN / folder).rglob("*")
    if path.is_file() and "__pycache__" not in path.parts
)


def test_the_plugin_holds_the_flow() -> None:
    assert len(list((PLUGIN / "skills").glob("*/SKILL.md"))) == 10
    assert len(list((PLUGIN / "commands").glob("*.md"))) == 8
    assert len(list((PLUGIN / "agents").glob("*.md"))) == 6


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(PLUGIN)))
def test_no_file_names_a_project(path: Path) -> None:
    text = path.read_text(errors="replace")

    assert [word for word in PROJECT_WORDS if word in text] == []
