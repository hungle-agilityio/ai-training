"""Tests of the after-edit-format hook. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import os
import sys
from collections.abc import Mapping
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parents[1]
RUFF = Path(sys.executable).parent / "ruff"


def load(name: str) -> ModuleType:
    spec = util.spec_from_file_location(name.replace("-", "_"), HOOKS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FORMAT = load("after-edit-format")


class FakeRun:
    """Records the commands and answers each with the given exit code and output."""

    def __init__(self, code: int = 0, output: str = "") -> None:
        self.calls: list[list[str]] = []
        self.code = code
        self.output = output

    def __call__(self, args: list[str], cwd: Path) -> tuple[int, str]:
        self.calls.append(args)
        return self.code, self.output


def require_ruff(path: Path, env: Mapping[str, str]) -> list[str]:
    """Without ruff the real-ruff tests fail on CI, so a green run always ran them."""
    if not path.exists():
        if env.get("CI"):
            pytest.fail(f"ruff is missing at {path}; run uv sync")
        pytest.skip(f"ruff is not installed at {path}")
    return [str(path)]


@pytest.fixture
def ruff() -> list[str]:
    return require_ruff(RUFF, os.environ)


def payload(file_path: str, tool: str = "Edit") -> dict[str, object]:
    return {"tool_name": tool, "tool_input": {"file_path": file_path}}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project with the ruff settings of ReviewRadar that matter here."""
    (tmp_path / "ruff.toml").write_text(
        'line-length = 100\nextend-exclude = ["*/migrations/*"]\n'
        '[lint]\nselect = ["E", "F", "I", "UP", "B"]\n'
    )
    return tmp_path


def test_python_file_gets_fix_then_format(project: Path) -> None:
    run = FakeRun()
    target = project / "reviews" / "forms.py"
    assert FORMAT.evaluate(payload(str(target)), project, run, ["ruff"]) is None
    assert run.calls == [
        [
            "ruff",
            "check",
            "--fix",
            "--extend-unfixable",
            "F401",
            "--exit-zero",
            "--force-exclude",
            str(target),
        ],
        ["ruff", "format", "--force-exclude", str(target)],
    ]


def test_write_is_formatted_like_edit(project: Path) -> None:
    run = FakeRun()
    FORMAT.evaluate(payload(str(project / "a.py"), tool="Write"), project, run, ["ruff"])
    assert len(run.calls) == 2


@pytest.mark.parametrize("name", ["notes.md", "page.html", "data.json", "script.pyc"])
def test_other_files_are_left_alone(project: Path, name: str) -> None:
    run = FakeRun()
    assert FORMAT.evaluate(payload(str(project / name)), project, run, ["ruff"]) is None
    assert run.calls == []


def test_file_outside_the_project_is_left_alone(
    project: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    run = FakeRun()
    outside = tmp_path_factory.mktemp("other") / "x.py"
    assert FORMAT.evaluate(payload(str(outside)), project, run, ["ruff"]) is None
    assert run.calls == []


@pytest.mark.parametrize("bad", [{}, {"tool_input": None}, {"tool_input": {}}, "text", None])
def test_payload_without_a_file_is_ignored(project: Path, bad: object) -> None:
    run = FakeRun()
    assert FORMAT.evaluate(bad, project, run, ["ruff"]) is None
    assert run.calls == []


def test_ruff_failure_is_one_line_for_claude(project: Path) -> None:
    run = FakeRun(code=2, output="error: Failed to parse a.py:1:5: Expected ':'\nmore\n")
    message = FORMAT.evaluate(payload(str(project / "a.py")), project, run, ["ruff"])
    assert message is not None
    assert "\n" not in message
    assert "a.py was not formatted" in message
    assert "Failed to parse" in message


def test_missing_ruff_is_reported_not_raised(project: Path) -> None:
    message = FORMAT.evaluate(
        payload(str(project / "a.py")), project, FORMAT.real_run, [str(project / "no-ruff")]
    )
    assert message is not None and "not formatted" in message


def test_real_ruff_sorts_imports_and_lays_out(project: Path, ruff: list[str]) -> None:
    target = project / "a.py"
    target.write_text(
        "import sys\nimport os\ndef f():\n    return os.sep, sys.argv\ndef g():\n    pass\n"
    )
    assert FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, ruff) is None
    assert target.read_text() == (
        "import os\nimport sys\n\n\ndef f():\n    return os.sep, sys.argv\n\n\ndef g():\n    pass\n"
    )


def test_real_ruff_keeps_a_broken_file(project: Path, ruff: list[str]) -> None:
    target = project / "a.py"
    broken = "def f(\n    return 1\n"
    target.write_text(broken)
    message = FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, ruff)
    assert message is not None
    assert "no output" not in message
    assert target.read_text() == broken


def test_real_ruff_skips_migrations(project: Path, ruff: list[str]) -> None:
    target = project / "reviews" / "migrations" / "0001_x.py"
    target.parent.mkdir(parents=True)
    messy = "import sys\nimport os\nx=(os,sys)\n"
    target.write_text(messy)
    assert FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, ruff) is None
    assert target.read_text() == messy


def test_real_ruff_keeps_an_import_not_used_yet(project: Path, ruff: list[str]) -> None:
    target = project / "a.py"
    target.write_text("import sys\nimport json\n\n\ndef f():\n    return 1\n")
    assert FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, ruff) is None
    assert target.read_text() == "import json\nimport sys\n\n\ndef f():\n    return 1\n"


def test_missing_ruff_fails_on_ci(tmp_path: Path) -> None:
    with pytest.raises(pytest.fail.Exception):
        require_ruff(tmp_path / "no-ruff", {"CI": "true"})


def test_missing_ruff_skips_outside_ci(tmp_path: Path) -> None:
    with pytest.raises(pytest.skip.Exception):
        require_ruff(tmp_path / "no-ruff", {})


def test_ruff_of_the_project_venv_comes_first(tmp_path: Path) -> None:
    local = tmp_path / ".venv" / "bin" / "ruff"
    local.parent.mkdir(parents=True)
    local.write_text("")
    assert FORMAT.ruff_command(tmp_path) == [str(local)]


def test_without_a_venv_ruff_runs_through_uv(tmp_path: Path) -> None:
    assert FORMAT.ruff_command(tmp_path) == ["uv", "run", "--quiet", "ruff"]


def test_slow_ruff_times_out_as_one_line(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(FORMAT, "TIMEOUT_SECONDS", 0.2)
    slow = [sys.executable, "-c", "import time; time.sleep(5)", "--"]
    code, output = FORMAT.real_run(slow, project)
    assert code == 124 and "timed out" in output
    message = FORMAT.evaluate(payload(str(project / "a.py")), project, FORMAT.real_run, slow)
    assert message is not None and "\n" not in message and "timed out" in message
