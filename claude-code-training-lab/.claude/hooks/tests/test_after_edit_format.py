"""Tests of the after-edit-format hook. Run: uv run pytest .claude/hooks/tests --no-cov -q"""

import sys
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


@pytest.mark.skipif(not RUFF.exists(), reason="ruff is not installed next to this Python")
def test_real_ruff_sorts_imports_and_lays_out(project: Path) -> None:
    target = project / "a.py"
    target.write_text(
        "import sys\nimport os\ndef f():\n    return os.sep, sys.argv\ndef g():\n    pass\n"
    )
    assert FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, [str(RUFF)]) is None
    assert target.read_text() == (
        "import os\nimport sys\n\n\ndef f():\n    return os.sep, sys.argv\n\n\ndef g():\n    pass\n"
    )


@pytest.mark.skipif(not RUFF.exists(), reason="ruff is not installed next to this Python")
def test_real_ruff_keeps_a_broken_file(project: Path) -> None:
    target = project / "a.py"
    broken = "def f(\n    return 1\n"
    target.write_text(broken)
    message = FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, [str(RUFF)])
    assert message is not None
    assert "no output" not in message
    assert target.read_text() == broken


@pytest.mark.skipif(not RUFF.exists(), reason="ruff is not installed next to this Python")
def test_real_ruff_skips_migrations(project: Path) -> None:
    target = project / "reviews" / "migrations" / "0001_x.py"
    target.parent.mkdir(parents=True)
    messy = "import sys\nimport os\nx=(os,sys)\n"
    target.write_text(messy)
    assert FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, [str(RUFF)]) is None
    assert target.read_text() == messy


@pytest.mark.skipif(not RUFF.exists(), reason="ruff is not installed next to this Python")
def test_real_ruff_keeps_an_import_not_used_yet(project: Path) -> None:
    target = project / "a.py"
    target.write_text("import sys\nimport json\n\n\ndef f():\n    return 1\n")
    assert FORMAT.evaluate(payload(str(target)), project, FORMAT.real_run, [str(RUFF)]) is None
    assert target.read_text() == "import json\nimport sys\n\n\ndef f():\n    return 1\n"
