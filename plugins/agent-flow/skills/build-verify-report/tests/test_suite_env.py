"""The report runs the plugin's tests without the loop variables (#243).

Run: uv run pytest ../plugins/agent-flow/skills/build-verify-report/tests --no-cov -q
"""

import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SKILL = Path(__file__).resolve().parents[1]
LOOP_VARS = ("FLOW_LOOP", "REVIEWRADAR_LOOP")


def load() -> ModuleType:
    spec = util.spec_from_file_location("build_report_suite_env", SKILL / "build_report.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load()


def recorded_calls(tmp_path: Path) -> list[list[str]]:
    calls: list[list[str]] = []

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        calls.append(args)
        return 0, "1 passed in 0.1s\n"

    BUILD.run_checks(tmp_path, run)
    return calls


def test_the_plugin_suites_run_without_the_loop_variables(tmp_path: Path) -> None:
    suite = [args for args in recorded_calls(tmp_path) if "--no-cov" in args]

    assert len(suite) == 1
    assert suite[0][:5] == ["env", "-u", "FLOW_LOOP", "-u", "REVIEWRADAR_LOOP"]
    assert suite[0][5:8] == ["uv", "run", "pytest"]


def test_the_other_checks_keep_the_build_environment(tmp_path: Path) -> None:
    others = [args for args in recorded_calls(tmp_path) if "--no-cov" not in args]

    assert others
    assert all(args[0] == "uv" for args in others)


@pytest.mark.parametrize("name", LOOP_VARS)
def test_a_loop_variable_does_not_reach_the_suite(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(name, "1")
    probe = f"import os; print(os.environ.get('{name}', 'unset'))"

    code, out = BUILD.real_run([*BUILD.WITHOUT_LOOP, sys.executable, "-c", probe], tmp_path)

    assert (code, out.strip()) == (0, "unset")
