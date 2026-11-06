"""before-edit-check lets a build edit only the existing tests its issue names (FLOW_TEST_EDITS)."""

import subprocess
from importlib import util
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-edit-check.py"
LOOP = {"REVIEWRADAR_LOOP": "1"}


def load():  # type: ignore[no-untyped-def]
    spec = util.spec_from_file_location("edit_check_test_edits", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDIT = load()


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture
def lab(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    lab_dir = tmp_path / "lab"
    for rel in (
        "reviews/tests/integration/test_seed_demo_replies.py",
        "reviews/tests/unit/test_old.py",
        ".claude/rules/git.md",
        "pyproject.toml",
    ):
        (lab_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (lab_dir / rel).write_text("x\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "task/290-x")
    return lab_dir


def check(lab: Path, rel: str, listed: str = "") -> list[str]:
    env = {**LOOP, "FLOW_TEST_EDITS": listed} if listed else LOOP
    result: list[str] = EDIT.evaluate(str(lab / rel), lab, env, EDIT.real_run)
    return result


LISTED = "reviews/tests/integration/test_seed_demo_replies.py\n"


def test_a_listed_existing_test_may_be_edited(lab: Path) -> None:
    assert check(lab, "reviews/tests/integration/test_seed_demo_replies.py", LISTED) == []


def test_the_listed_path_ignores_letter_case(lab: Path) -> None:
    listed = "Reviews/Tests/Integration/TEST_SEED_DEMO_REPLIES.py"
    assert check(lab, "reviews/tests/integration/test_seed_demo_replies.py", listed) == []


def test_an_unlisted_existing_test_is_still_refused(lab: Path) -> None:
    problems = check(lab, "reviews/tests/unit/test_old.py", LISTED)
    assert problems == ["test_old.py is a test that is already on main; fix the code, not the test"]


def test_without_the_variable_an_existing_test_is_refused(lab: Path) -> None:
    problems = check(lab, "reviews/tests/integration/test_seed_demo_replies.py")
    assert problems and "already on main" in problems[0]


@pytest.mark.parametrize("rel", [".claude/rules/git.md", "pyproject.toml"])
def test_listing_a_rule_or_gate_file_does_not_open_it(lab: Path, rel: str) -> None:
    assert check(lab, rel, f"{rel}\n") != []


def test_outside_loop_mode_nothing_changes(lab: Path) -> None:
    path = lab / "reviews/tests/unit/test_old.py"
    assert EDIT.evaluate(str(path), lab, {}, EDIT.real_run) == []
