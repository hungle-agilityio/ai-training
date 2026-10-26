"""Hardening tests of before-edit-check. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import json
import subprocess
import sys
from importlib import util
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-edit-check.py"
LOOP = {"REVIEWRADAR_LOOP": "1"}


def load():  # type: ignore[no-untyped-def]
    spec = util.spec_from_file_location("edit_check", HOOK)
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
        "reviews/tests/unit/test_old.py",
        ".claude/knowledge/BUSINESS_RULES.md",
        ".claude/rules/git.md",
        "pyproject.toml",
    ):
        (lab_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (lab_dir / rel).write_text("x\n")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "ci.yml").write_text("a: b\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "feat/1-x")
    return lab_dir


def check(lab: Path, rel: str, env: dict[str, str] = LOOP) -> list[str]:
    result: list[str] = EDIT.evaluate(str(lab / rel), lab, env, EDIT.real_run)
    return result


@pytest.mark.parametrize(
    "rel",
    [
        ".CLAUDE/settings.json",
        ".Claude/rules/git.md",
        "../.GITHUB/ci.yml",
        ".MCP.json",
        "reviews/TESTS/unit/test_old.py",
        "Reviews/Tests/unit/TEST_OLD.py",
    ],
)
def test_letter_case_does_not_bypass_the_rules(lab: Path, rel: str) -> None:
    assert check(lab, rel)


def test_user_level_claude_folder_is_protected(lab: Path) -> None:
    assert check(lab, "../../home/someone/.claude/settings.json")


def test_existing_knowledge_file_is_protected_but_a_new_one_is_not(lab: Path) -> None:
    assert check(lab, ".claude/knowledge/BUSINESS_RULES.md")
    assert not check(lab, ".claude/knowledge/decisions/ADR-009-new.md")


@pytest.mark.parametrize("rel", ["pyproject.toml", "uv.lock", "conftest.py", "reviews/conftest.py"])
def test_gate_files_are_protected(lab: Path, rel: str) -> None:
    assert check(lab, rel)


def test_allow_test_edit_does_not_lift_the_gate_files(lab: Path) -> None:
    assert check(lab, "pyproject.toml", {**LOOP, "ALLOW_TEST_EDIT": "1"})


def test_test_edit_is_refused_when_main_cannot_be_read(tmp_path: Path) -> None:
    not_a_repo = tmp_path / "plain"
    (not_a_repo / "reviews" / "tests").mkdir(parents=True)
    assert check(not_a_repo, "reviews/tests/test_x.py")


def run_hook(payload: str, env_extra: dict[str, str]) -> int:
    import os

    done = subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env={**os.environ, **env_extra},
        check=False,
    )
    return done.returncode


def test_unreadable_call_is_blocked_in_loop_mode_only() -> None:
    assert run_hook("not json", LOOP) == 2
    assert run_hook("not json", {"REVIEWRADAR_LOOP": "0"}) == 0


def test_edit_call_without_a_path_is_blocked_in_loop_mode() -> None:
    payload = json.dumps({"tool_name": "Edit", "tool_input": {}})
    assert run_hook(payload, LOOP) == 2


@pytest.mark.parametrize(
    "rel",
    ["ruff.toml", ".ruff.toml", "mypy.ini", ".mypy.ini", "setup.cfg", "pytest.ini", "tox.ini"]
    + [".coveragerc"],
)
def test_tool_config_files_are_protected(lab: Path, rel: str) -> None:
    assert check(lab, rel)


def test_a_file_is_judged_in_its_own_checkout_not_the_sessions(lab: Path, tmp_path: Path) -> None:
    other = tmp_path / "elsewhere"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    result: list[str] = EDIT.evaluate(
        str(lab / "reviews/tests/unit/test_old.py"), other, LOOP, EDIT.real_run
    )
    assert result
