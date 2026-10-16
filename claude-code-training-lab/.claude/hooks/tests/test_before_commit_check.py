"""Tests of the commit hook. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import json
import subprocess
import sys
from collections.abc import Callable
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOK = Path(__file__).resolve().parents[1] / "before-commit-check.py"
Runner = Callable[[list[str], Path], tuple[int, str]]


def load() -> ModuleType:
    spec = util.spec_from_file_location("commit_check", HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "feat/x-demo")
    (tmp_path / "app.py").write_text("x = 1\n")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-q", "-m", "first")
    return tmp_path


def runner(ruff: int = 0, mypy: int = 0) -> Runner:
    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        if args[:3] == ["uv", "run", "ruff"]:
            return ruff, "ruff output" if ruff else ""
        if args[:3] == ["uv", "run", "mypy"]:
            return mypy, "mypy output" if mypy else ""
        return CHECK.real_run(args, cwd)  # type: ignore[no-any-return]

    return run


def problems(command: str, repo: Path, ruff: int = 0, mypy: int = 0) -> list[str]:
    result: list[str] = CHECK.evaluate(command, repo, runner(ruff, mypy))
    return result


def test_commands_that_are_not_add_or_commit_are_left_alone(repo: Path) -> None:
    for command in ("git status", "git diff", "uv run pytest -q", "echo git commit"):
        assert problems(command, repo) == []


@pytest.mark.parametrize(
    "path",
    [
        "db.sqlite3",
        "local.sqlite3",
        ".env",
        ".env.local",
        "keys/id_rsa",
        "cert.pem",
        "a/__pycache__/x.pyc",
        ".venv/bin/python",
        ".coverage",
        ".mypy_cache/x",
        ".claude/settings.local.json",
        "CLAUDE.local.md",
    ],
)
def test_staging_a_forbidden_file_is_refused(repo: Path, path: str) -> None:
    assert problems(f"git add {path}", repo) != []


@pytest.mark.parametrize("path", ["reviews/models.py", "env.example", "README.md", ".github/x.yml"])
def test_staging_normal_files_is_allowed(repo: Path, path: str) -> None:
    assert problems(f"git add {path}", repo) == []


def test_force_adding_is_refused(repo: Path) -> None:
    assert problems("git add -f app.py", repo) != []
    assert problems("git add --force app.py", repo) != []


def test_add_all_is_refused_when_a_forbidden_file_would_be_added(repo: Path) -> None:
    (repo / ".env").write_text("SECRET=1\n")

    assert any(".env" in line for line in problems("git add -A", repo))


def test_add_all_is_allowed_when_that_file_is_ignored(repo: Path) -> None:
    (repo / ".gitignore").write_text(".env\n")
    (repo / ".env").write_text("SECRET=1\n")

    assert problems("git add -A", repo) == []


def test_commit_with_a_staged_forbidden_file_is_refused(repo: Path) -> None:
    (repo / "db.sqlite3").write_text("data")
    git(repo, "add", "-f", "db.sqlite3")

    assert any("db.sqlite3" in line for line in problems('git commit -m "x"', repo))


def test_clean_commit_on_a_branch_is_allowed(repo: Path) -> None:
    (repo / "app.py").write_text("x = 2\n")
    git(repo, "add", "app.py")

    assert problems('git commit -m "Change x"', repo) == []


@pytest.mark.parametrize(
    "line",
    ["Co-Authored-By: Claude <x@y.z>", "co-authored-by: Someone", "Generated with Claude Code"],
)
def test_commit_message_with_an_attribution_line_is_refused(repo: Path, line: str) -> None:
    command = f'git commit -m "Change x" -m "{line}"'

    assert any("attribution" in item for item in problems(command, repo))


def test_attribution_in_a_message_file_is_refused(repo: Path) -> None:
    (repo / "msg.txt").write_text("Change x\n\nCo-Authored-By: Claude\n")

    assert any("attribution" in item for item in problems("git commit -F msg.txt", repo))


def test_attribution_in_a_heredoc_message_is_refused(repo: Path) -> None:
    command = "git commit -F - <<'EOF'\nChange x\n\nGenerated with Claude Code\nEOF"

    assert any("attribution" in item for item in problems(command, repo))


@pytest.mark.parametrize("branch", ["main", "master"])
def test_commit_on_main_is_refused(repo: Path, branch: str) -> None:
    git(repo, "checkout", "-q", "-b", branch)

    assert any("main" in item or "master" in item for item in problems('git commit -m "x"', repo))


def test_failing_lint_or_types_refuse_the_commit(repo: Path) -> None:
    assert any("ruff" in item for item in problems('git commit -m "x"', repo, ruff=1))
    assert any("mypy" in item for item in problems('git commit -m "x"', repo, mypy=1))


def test_a_secret_added_to_a_file_is_refused(repo: Path) -> None:
    (repo / "app.py").write_text('token = "ghp_' + "a" * 36 + '"\n')
    git(repo, "add", "app.py")

    assert any("secret" in item for item in problems('git commit -m "x"', repo))


def test_hook_exit_code_blocks_a_commit_on_main_with_a_message(repo: Path) -> None:
    git(repo, "checkout", "-q", "-b", "main")
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": 'git commit -m "x"'},
    }

    done = subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 2
    assert "before-commit-check" in done.stderr


def test_hook_exit_code_allows_other_tools_and_commands(repo: Path) -> None:
    for payload in (
        {"tool_name": "Read", "tool_input": {"file_path": "x"}},
        {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": "git status"}},
    ):
        done = subprocess.run(
            [sys.executable, "-I", str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == 0


def test_quick_checks_run_where_pyproject_is_even_when_git_root_is_higher(repo: Path) -> None:
    project = repo / "lab"
    (project / "sub").mkdir(parents=True)
    (project / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    seen: list[Path] = []

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        if args[:2] == ["uv", "run"]:
            seen.append(cwd)
            return 0, ""
        return CHECK.real_run(args, cwd)  # type: ignore[no-any-return]

    (project / "sub" / "a.py").write_text("x = 1\n")
    git(repo, "add", "lab/sub/a.py")
    CHECK.evaluate('git commit -m "x"', project / "sub", run)

    assert seen and all(folder == project for folder in seen)
