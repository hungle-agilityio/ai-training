"""Tests of the loop-mode hooks. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import subprocess
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parents[1]
LOOP = {"REVIEWRADAR_LOOP": "1"}


def load(name: str) -> ModuleType:
    spec = util.spec_from_file_location(name.replace("-", "_"), HOOKS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDIT = load("before-edit-check")
FINISH = load("before-finish-check")


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture
def lab(tmp_path: Path) -> Path:
    """A git root with a lab folder; one test file is committed on main."""
    git(tmp_path, "init", "-q", "-b", "main")
    lab_dir = tmp_path / "lab"
    (lab_dir / "reviews" / "tests" / "unit").mkdir(parents=True)
    (lab_dir / "reviews" / "tests" / "unit" / "test_old.py").write_text("x = 1\n")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "ci.yml").write_text("a: b\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "feat/1-x")
    return lab_dir


def check(lab: Path, rel: str, env: dict[str, str]) -> list[str]:
    return EDIT.evaluate(str(lab / rel), lab, env, EDIT.real_run)  # type: ignore[no-any-return]


@pytest.mark.parametrize(
    "rel",
    [
        "../.github/ci.yml",
        ".claude/settings.json",
        ".claude/hooks/before-edit-check.py",
        ".mcp.json",
    ],
)
def test_loop_cannot_edit_its_own_rules(lab: Path, rel: str) -> None:
    assert check(lab, rel, LOOP)


def test_loop_may_write_knowledge_and_decisions(lab: Path) -> None:
    assert not check(lab, ".claude/knowledge/decisions/ADR-009-x.md", LOOP)


def test_loop_cannot_edit_a_test_already_on_main(lab: Path) -> None:
    assert check(lab, "reviews/tests/unit/test_old.py", LOOP)


def test_loop_may_add_a_new_test(lab: Path) -> None:
    assert not check(lab, "reviews/tests/unit/test_new.py", LOOP)


def test_allow_test_edit_lifts_only_the_test_rule(lab: Path) -> None:
    env = {**LOOP, "ALLOW_TEST_EDIT": "1"}
    assert not check(lab, "reviews/tests/unit/test_old.py", env)
    assert check(lab, ".mcp.json", env)


def test_interactive_session_is_never_blocked(lab: Path) -> None:
    assert not check(lab, ".claude/settings.json", {})
    assert not check(lab, "reviews/tests/unit/test_old.py", {})


def test_source_files_are_free(lab: Path) -> None:
    assert not check(lab, "reviews/services.py", LOOP)


def runner(codes: dict[str, int]) -> object:
    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        return codes.get(args[2], 0), f"{args[2]} output"

    return run


def test_finish_passes_when_all_checks_pass(tmp_path: Path) -> None:
    assert FINISH.evaluate({}, tmp_path, LOOP, runner({})) == []


def test_finish_reports_each_failing_check(tmp_path: Path) -> None:
    found = FINISH.evaluate({}, tmp_path, LOOP, runner({"ruff": 1, "pytest": 1}))
    assert len(found) == 2
    assert "ruff" in found[0] and "pytest" in found[1]


def test_finish_allows_the_second_stop(tmp_path: Path) -> None:
    payload = {"stop_hook_active": True}
    assert FINISH.evaluate(payload, tmp_path, LOOP, runner({"ruff": 1})) == []


def test_finish_does_nothing_outside_loop_mode(tmp_path: Path) -> None:
    assert FINISH.evaluate({}, tmp_path, {}, runner({"ruff": 1})) == []
