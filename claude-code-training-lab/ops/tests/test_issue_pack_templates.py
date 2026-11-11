"""The spec templates and the write-issue skill carry the issue pack.

Spec: specs/issue-pack/spec.md (AC1 to AC6 and AC8; rows M1 to M6 and M9 of its test matrix).
Run: pytest ops/tests/test_issue_pack_templates.py
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap

APP = Path(__file__).resolve().parents[2]
TEMPLATES = APP / "docs" / "app" / "templates" / "spec"
SPEC = TEMPLATES / "spec.md"
MATRIX = TEMPLATES / "test-matrix.md"
TASKS = TEMPLATES / "tasks.md"
SPECS_README = APP / "specs" / "README.md"
SKILL = APP.parent / "plugins" / "agent-flow" / "skills" / "write-issue" / "SKILL.md"

REPO = "acme/garden"
STORY = "As a <user>, I want <ability>, so that <goal>."
GIVEN_WHEN_THEN = (
    "**ACn.** Given <the starting data, with real names and numbers>, "
    "when <the action>, then <the exact result>."
)
MATRIX_HEADER = "| Row | AC | Case | Check | Level | Test file | Task |"
CASES = ("normal", "empty", "edge", "error", "permission", "narrow screen")
LEVELS = ("unit", "integration", "browser", "manual")
PROJECT_WORDS = re.compile(r"reviewradar|ai-training|claude-code-training-lab|hungle", re.I)
Run = Callable[..., int]


def section(text: str, heading: str) -> str:
    """The body of one `## ` section, up to the next `## ` heading."""
    body = text.split(f"\n{heading}\n", 1)[1]
    return re.split(r"\n## ", body, maxsplit=1)[0]


def headings(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("## ")]


def one_of(values: tuple[str, ...]) -> str:
    return "is one of " + ", ".join(f'"{value}"' for value in values)


# AC1 (M1): the user story


def test_spec_template_has_the_user_story_right_after_the_summary() -> None:
    text = SPEC.read_text()
    names = headings(text)
    assert names[names.index("## Summary") + 1] == "## User story"
    story = section(text, "## User story")
    assert STORY in story
    comment = re.search(r"<!--(.*?)-->", story, re.S)
    assert comment is not None
    words = " ".join(comment.group(1).split())
    assert "One line per kind of user" in words
    assert "names the person who gains (the owner, QA, the loop)" in words


# AC2 (M2): the two AC forms


def test_spec_template_states_both_ac_forms_and_keeps_the_test_rule() -> None:
    criteria = section(SPEC.read_text(), "## Acceptance criteria")
    assert "what a person sees or does" in criteria
    assert f"`{GIVEN_WHEN_THEN}`" in criteria
    assert "a function, a query, a file or a setting keeps the plain form" in criteria
    assert 'Write the test rule as "every test on `main` passes unchanged".' in criteria


def test_spec_template_example_shows_one_ac_of_each_form() -> None:
    criteria = section(SPEC.read_text(), "## Acceptance criteria")
    examples = [line for line in criteria.splitlines() if line.startswith("- **AC")]
    given = [
        line for line in examples if re.match(r"- \*\*AC\d+\.\*\* Given .+, when .+, then ", line)
    ]
    assert len(examples) == 2
    assert len(given) == 1


# AC3 (M3): the test matrix template


def test_matrix_template_starts_with_the_title_and_the_copy_comment() -> None:
    lines = [line for line in MATRIX.read_text().splitlines() if line.strip()]
    assert lines[0] == "# Test matrix: <feature>"
    assert lines[1].startswith("<!-- Copy to specs/<feature>/test-matrix.md.")


def test_matrix_template_has_the_table_with_numbered_example_rows() -> None:
    lines = MATRIX.read_text().splitlines()
    start = lines.index(MATRIX_HEADER)
    assert lines[start + 1].replace("-", "").replace("|", "").strip() == ""
    assert lines[start + 2].startswith("| M1 |")
    assert lines[start + 3].startswith("| M2 |")
    rows = [line for line in lines if re.match(r"\| M\d+ \|", line)]
    assert all(line.count("|") == MATRIX_HEADER.count("|") for line in rows)


def test_matrix_template_writes_out_the_allowed_values() -> None:
    text = MATRIX.read_text()
    assert one_of(CASES) in text
    assert one_of(LEVELS) in text
    assert "the Given/When/Then of a user-visible AC or the plain check of a technical AC" in text


def test_matrix_template_example_rows_use_only_allowed_values() -> None:
    rows = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in MATRIX.read_text().splitlines()
        if re.match(r"\| M\d+ \|", line)
    ]
    assert rows
    assert all(row[2] in CASES and row[4] in LEVELS for row in rows)


@pytest.mark.parametrize(
    "rule",
    [
        "Every AC has at least one row.",
        'Every user-visible AC has a "normal" row and an "empty" row, '
        'or a row whose "Check" says `n/a: <why>`.',
        "A row's test file is the new test file named in its task.",
        'A check no test can make has "Level" "manual" and gives the person\'s steps.',
        "The matrix is written at step 3 from the ACs, before any build, "
        "and is part of the spec pull request.",
    ],
)
def test_matrix_template_lists_each_rule_as_a_bullet(rule: str) -> None:
    bullets = [line[2:] for line in MATRIX.read_text().splitlines() if line.startswith("- ")]
    assert rule in bullets


def test_matrix_template_names_no_project() -> None:
    assert PROJECT_WORDS.findall(MATRIX.read_text()) == []


# AC4 (M4): each task names its matrix rows


def test_every_task_entry_names_its_matrix_rows_right_after_its_acs() -> None:
    lines = TASKS.read_text().splitlines()
    tasks = [i for i, line in enumerate(lines) if re.match(r"## T\d+:", line)]
    after_acs = {}
    for start in tasks:
        acs = next(i for i in range(start, len(lines)) if lines[i].startswith("- **ACs:**"))
        after_acs[lines[start].split(":")[0]] = lines[acs + 1]
    assert after_acs == {
        "## T1": "- **Matrix rows:** M1, M2",
        "## T2": "- **Matrix rows:** M3",
    }


# AC5 (M5): the specs README


def test_specs_readme_lists_the_test_matrix_and_the_user_story() -> None:
    bullets = [line for line in SPECS_README.read_text().splitlines() if line.startswith("- `")]
    matrix = [line for line in bullets if line.startswith("- `test-matrix.md`:")]
    spec = [line for line in bullets if line.startswith("- `spec.md`:")]
    assert len(matrix) == 1 and len(spec) == 1
    assert (
        "the tests planned per AC: case, level, test file and task, written before any build"
        in matrix[0]
    )
    assert "user story" in spec[0]


# AC6 (M6): write-issue, section 7


def handover() -> str:
    return section(
        SKILL.read_text(), "## 7. Handing an issue to the loop (new request from the user)"
    )


def test_skill_puts_the_user_story_at_the_end_of_the_summary() -> None:
    text = handover()
    assert "user story" in text
    assert "Summary ends with" in text
    assert "fast lane" in text


def test_skill_states_the_two_done_when_forms() -> None:
    text = handover()
    assert "Given <the starting data, with real names and numbers>, when <the action>" in text
    assert "plain form" in text


def test_skill_names_the_test_matrix_rows_section_and_its_source() -> None:
    text = handover()
    assert "`## Test matrix rows`" in text
    assert "`test-matrix.md`" in text
    assert "`paths.specs_dir`" in text


def test_skill_has_the_zero_questions_test_before_agent_ready() -> None:
    text = handover()
    assert "**Zero-questions test" in text
    step = text.split("**Zero-questions test", 1)[1]
    assert "before `agent:ready`" in step
    assert "no conversation context" in step
    assert "only the issue body and read access to the repository" in step
    assert "is not a question" in step
    assert "0 questions" in step
    assert "`Zero-questions test: 0 questions after <n> rounds (<k> in round 1).`" in step


# AC8 (M9): bootstrap copies the new template


@pytest.fixture
def target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    path = tmp_path / "garden"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{REPO}.git"], cwd=path, check=True
    )
    return path


@pytest.fixture
def run(target: Path) -> Run:
    def call(*extra: str) -> int:
        argv = [
            "--target", str(target), "--repo", REPO, "--owner", "acme-owner",
            "--name", "Garden", "--slug", "garden", "--ntfy-topic", "garden-test", "--no-labels",
        ]  # fmt: skip
        return bootstrap.main([*argv, *extra])

    return call


def test_bootstrap_copies_the_matrix_template(run: Run, target: Path) -> None:
    assert run("--app-dir", ".") == 0
    assert (target / "docs" / "app" / "templates" / "spec" / "test-matrix.md").is_file()


def test_bootstrap_layout_copy_names_the_new_specs_folder(run: Run, target: Path) -> None:
    assert run("--stack", "python") == 0
    template = target / "docs" / "templates" / "spec" / "test-matrix.md"
    assert template.is_file()
    assert "docs/specs/<feature>/test-matrix.md" in template.read_text()
