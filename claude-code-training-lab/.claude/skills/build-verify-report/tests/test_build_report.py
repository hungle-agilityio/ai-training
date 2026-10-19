"""Tests of the verify report builder.

Run: uv run pytest .claude/skills/build-verify-report/tests --no-cov -q
"""

import json
from collections.abc import Callable
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SKILL = Path(__file__).resolve().parents[1]
Runner = Callable[[list[str], Path], tuple[int, str]]


def load() -> ModuleType:
    spec = util.spec_from_file_location("build_report", SKILL / "build_report.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load()

GREEN: dict[str, tuple[int, str]] = {
    "ruff": (0, "All checks passed!\n"),
    "mypy": (0, "Success: no issues found in 28 source files\n"),
    "pytest -q": (0, "TOTAL   1020   3   99%\n142 passed in 1.2s\n"),
    "coverage": (0, "Name Stmts\nTOTAL 204 0 100%\n"),
    "skills": (0, "176 passed in 2.2s\n"),
    "diff": (0, ""),
    "git": (0, "feat/x\n"),
}


def scripted(overrides: dict[str, tuple[int, str]] | None = None) -> Runner:
    table = {**GREEN, **(overrides or {})}

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        text = " ".join(args)
        if "ruff" in text:
            return table["ruff"]
        if "mypy" in text:
            return table["mypy"]
        if "coverage report" in text:
            return table["coverage"]
        if ".claude/hooks/tests" in text:
            return table["skills"]
        if "pytest" in text:
            return table["pytest -q"]
        if args[:2] == ["git", "diff"]:
            return table["diff"]
        return table["git"]

    return run


def test_parsers_read_real_tool_output() -> None:
    assert BUILD.parse_pytest("1 failed, 139 passed in 1s") == {"passed": 139, "failed": 1}
    assert BUILD.parse_pytest("139 passed in 1.2s") == {"passed": 139, "failed": 0}
    assert BUILD.parse_total_coverage("TOTAL   1020   3   99%") == 99
    assert BUILD.parse_total_coverage("nothing here") is None
    assert BUILD.parse_mypy_files("Success: no issues found in 28 source files") == 28


def test_green_checks_give_pass_axes_with_the_real_numbers() -> None:
    axes = {a["name"]: a for a in BUILD.run_checks(Path("."), scripted())}

    assert axes["Lint"]["status"] == "PASS"
    assert "28 source files" in axes["Types"]["evidence"]
    assert "142 passed" in axes["Tests"]["evidence"] and "99%" in axes["Tests"]["evidence"]
    assert axes["Coverage"]["status"] == "PASS"
    assert axes["Skill and hook tests"]["status"] == "PASS"


def test_a_failing_check_gives_fail_and_the_reason() -> None:
    axes = {
        a["name"]: a
        for a in BUILD.run_checks(
            Path("."),
            scripted({"pytest -q": (1, "1 failed, 141 passed in 1s\nFAILED t.py::test_x\n")}),
        )
    }

    assert axes["Tests"]["status"] == "FAIL"
    assert "1 failed" in axes["Tests"]["evidence"]


def test_verdict() -> None:
    assert BUILD.verdict([{"status": "PASS"}, {"status": "PASS"}]) == "PASS"
    assert BUILD.verdict([{"status": "PASS"}, {"status": "FAIL"}]) == "FAIL"
    assert BUILD.verdict([{"status": "PASS"}, {"status": "NOT CONFIGURED"}]) == "INCOMPLETE"
    assert BUILD.verdict([{"status": "FAIL"}, {"status": "NOT CONFIGURED"}]) == "FAIL"


def test_issue_axis_is_not_configured_without_criteria_and_follows_them_with() -> None:
    assert BUILD.issue_axis(None)["status"] == "NOT CONFIGURED"
    ok = BUILD.issue_axis({"criteria": [{"text": "a", "status": "PASS", "evidence": "x"}]})
    bad = BUILD.issue_axis(
        {"criteria": [{"text": "a", "status": "PASS"}, {"text": "b", "status": "FAIL"}]}
    )

    assert ok["status"] == "PASS" and bad["status"] == "FAIL"


def test_query_count_axis_counts_the_tests_that_assert_it(tmp_path: Path) -> None:
    tests = tmp_path / "reviews" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_a.py").write_text("def test_a(django_assert_max_num_queries):\n    pass\n")
    (tests / "test_b.py").write_text("def test_b(django_assert_num_queries):\n    pass\n")

    assert BUILD.query_axis(tmp_path)["status"] == "PASS"
    assert "2" in BUILD.query_axis(tmp_path)["evidence"]
    (tests / "test_a.py").unlink()
    (tests / "test_b.py").unlink()
    assert BUILD.query_axis(tmp_path)["status"] == "NOT CONFIGURED"


def test_security_axis_fails_on_a_secret_like_string_without_printing_it() -> None:
    clean = BUILD.security_axis("+x = 1\n")
    leaked = BUILD.security_axis('+token = "ghp_' + "a" * 36 + '"\n')

    assert clean["status"] == "PASS"
    assert leaked["status"] == "FAIL" and "ghp_" not in leaked["evidence"]


def test_browser_axis_reads_the_result_of_the_browser_check(tmp_path: Path) -> None:
    (tmp_path / "01-a.png").write_bytes(b"png")
    (tmp_path / "result.json").write_text(
        json.dumps(
            {
                "status": "clean",
                "steps": [{"name": "a", "screenshot": "01-a.png"}],
                "console_errors": 0,
                "network_failures": 0,
                "problems": 0,
            }
        )
    )

    axis = BUILD.browser_axis(tmp_path, 0, "")

    assert axis["status"] == "PASS" and "1 screenshot" in axis["evidence"]
    assert (
        BUILD.browser_axis(tmp_path, 2, "NOT CONFIGURED: no browser")["status"] == "NOT CONFIGURED"
    )
    assert BUILD.browser_axis(None, None, "")["status"] == "NOT CONFIGURED"


def test_html_is_escaped_and_holds_the_verdict_axes_and_images(tmp_path: Path) -> None:
    (tmp_path / "01-a.png").write_bytes(b"png")
    report = {
        "title": "Issue <b>x</b>",
        "verdict": "PASS",
        "branch": "feat/x",
        "commit": "abc1234",
        "date": "2026-10-19",
        "axes": [{"name": "Lint", "status": "PASS", "evidence": "All <ok>"}],
        "screenshots": [str(tmp_path / "01-a.png")],
        "review": "",
        "check_yourself": ["Open /reviews/"],
    }

    html = BUILD.render_html(report)

    assert "<b>x</b>" not in html and "&lt;b&gt;x&lt;/b&gt;" in html
    assert "PASS" in html and "Lint" in html and "Open /reviews/" in html
    assert "data:image/png;base64," in html


@pytest.mark.parametrize("fail", [False, True])
def test_build_writes_the_report_files_and_the_verdict(tmp_path: Path, fail: bool) -> None:
    root = tmp_path / "project"
    (root / "reviews" / "tests").mkdir(parents=True)
    (root / "reviews" / "tests" / "test_q.py").write_text(
        "def test_q(django_assert_num_queries):\n    pass\n"
    )
    out = tmp_path / "out"
    run = scripted({"ruff": (1, "x.py:1:1 F401 unused import\n")} if fail else None)

    report = BUILD.build(
        root, out, run, title="Issue", criteria=None, review=None, browser=False, open_report=False
    )

    assert (out / "report.html").is_file() and (out / "report.json").is_file()
    assert report["verdict"] == ("FAIL" if fail else "INCOMPLETE")
    assert json.loads((out / "report.json").read_text())["verdict"] == report["verdict"]


def test_the_report_opens_by_itself_unless_told_not_to(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opened: list[str] = []
    monkeypatch.setattr(BUILD.webbrowser, "open", lambda url: opened.append(url))
    root = tmp_path / "project"
    root.mkdir()

    BUILD.build(root, tmp_path / "a", scripted(), "I", None, None, False, open_report=True)
    BUILD.build(root, tmp_path / "b", scripted(), "I", None, None, False, open_report=False)

    assert len(opened) == 1 and opened[0].endswith("a/report.html")
