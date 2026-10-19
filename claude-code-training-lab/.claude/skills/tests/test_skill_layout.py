"""Every skill follows the layout in .claude/skills/README.md.

Run: uv run pytest .claude/skills/tests --no-cov -q
"""

import re
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[1]
FOLDERS = sorted(p for p in SKILLS.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
NAME = re.compile(r"^[a-z]+(-[a-z]+){1,2}$")
FORBIDDEN = {"github", "gitlab", "git", "claude", "helper", "utils", "misc"}


def frontmatter(folder: Path) -> dict[str, str]:
    text = (folder / "SKILL.md").read_text()
    block = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert block is not None, f"{folder.name}: SKILL.md has no frontmatter"
    return dict(line.split(": ", 1) for line in block.group(1).splitlines() if ": " in line)


def test_the_skills_are_found() -> None:
    assert len(FOLDERS) >= 13


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda p: p.name)
def test_name_is_the_folder_and_follows_the_naming_rule(folder: Path) -> None:
    meta = frontmatter(folder)

    assert meta["name"] == folder.name
    assert NAME.match(folder.name)
    assert not FORBIDDEN & set(folder.name.split("-"))


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda p: p.name)
def test_description_says_what_and_when(folder: Path) -> None:
    description = frontmatter(folder)["description"]

    assert len(description) > 40
    assert "use " in description.lower()


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda p: p.name)
def test_a_skill_with_a_program_has_tests(folder: Path) -> None:
    programs = [p for p in folder.glob("*.py")]

    if programs:
        assert list((folder / "tests").glob("test_*.py")), f"{folder.name}: no tests"


@pytest.mark.parametrize("folder", FOLDERS, ids=lambda p: p.name)
def test_every_skill_is_in_the_readme_table(folder: Path) -> None:
    assert f"`{folder.name}`" in (SKILLS / "README.md").read_text()
