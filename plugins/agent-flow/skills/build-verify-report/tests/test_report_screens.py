"""Tests of the screens in the verify report: none without UI, only the named ones with UI.

Run: uv run pytest .claude/skills/build-verify-report/tests --no-cov -q
"""

import json
from collections.abc import Callable
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]
Runner = Callable[[list[str], Path], tuple[int, str]]
NO_SCREENS = 'no screens given: pass --spec from the issue\'s "Screens to capture"'


def load() -> ModuleType:
    spec = util.spec_from_file_location("build_report_screens", SKILL / "build_report.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load()


def green(commands: list[list[str]], browser: Callable[[list[str]], tuple[int, str]]) -> Runner:
    """Every check green; the browser check is answered by the given function."""

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        commands.append(args)
        text = " ".join(args)
        if "browser_check.py" in text:
            return browser(args)
        if "ruff" in text:
            return 0, "All checks passed!\n"
        if "mypy" in text:
            return 0, "Success: no issues found in 28 source files\n"
        if "coverage report" in text:
            return 0, "TOTAL 204 0 100%\n"
        if "pytest" in text:
            return 0, "TOTAL   1020   3   99%\n142 passed in 1.2s\n"
        if args[:2] == ["git", "diff"]:
            return 0, ""
        return 0, "task/x\n"

    return run


def no_browser(args: list[str]) -> tuple[int, str]:
    raise AssertionError("the browser check must not run")


def browser_writing(steps: list[dict[str, Any]], status: str = "clean") -> Any:
    """A fake browser check that writes result.json and the screenshots its steps name."""

    def browser(args: list[str]) -> tuple[int, str]:
        folder = Path(args[args.index("--out") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        for step in steps:
            for key in ("screenshot", "element_screenshot"):
                if step.get(key):
                    (folder / step[key]).write_bytes(b"png")
        result = {
            "status": status,
            "steps": steps,
            "console_errors": 0,
            "network_failures": 0,
            "problems": sum(len(s.get("problems", [])) for s in steps),
            "masking": {"status": "clean", "findings": []},
        }
        (folder / "result.json").write_text(json.dumps(result))
        return (0 if status == "clean" else 1), "result: " + status

    return browser


def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "reviews" / "tests").mkdir(parents=True)
    (root / "reviews" / "tests" / "test_q.py").write_text(
        "def test_q(django_assert_num_queries):\n    pass\n"
    )
    return root


CRITERIA = {"criteria": [{"text": "a", "status": "PASS", "evidence": "x"}]}


def browser_axis(report: dict[str, Any]) -> dict[str, str]:
    axes: list[dict[str, str]] = report["axes"]
    return next(a for a in axes if a["name"] == "Browser")


def test_no_ui_runs_no_browser_and_is_not_applicable(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    run = green(commands, no_browser)

    report = BUILD.build(
        project(tmp_path), tmp_path / "out", run, "T", CRITERIA, None, False, False, no_ui=True
    )

    assert browser_axis(report) == {
        "name": "Browser",
        "status": "NOT APPLICABLE",
        "evidence": "the task changes no screen",
    }
    assert report["verdict"] == "PASS"
    assert report["screenshots"] == []
    assert "<h2>Screenshots</h2>" not in (tmp_path / "out" / "report.html").read_text()


def test_not_applicable_does_not_make_the_verdict_incomplete() -> None:
    assert BUILD.verdict([{"status": "PASS"}, {"status": "NOT APPLICABLE"}]) == "PASS"
    assert BUILD.verdict([{"status": "FAIL"}, {"status": "NOT APPLICABLE"}]) == "FAIL"


def test_no_ui_masking_is_clean_when_the_report_text_is_clean(tmp_path: Path) -> None:
    run = green([], no_browser)

    report = BUILD.build(
        project(tmp_path), tmp_path / "out", run, "T", CRITERIA, None, False, False, no_ui=True
    )

    saved = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["masking"]["status"] == "clean" == saved["masking"]["status"]


def test_no_ui_masking_finds_personal_data_in_the_report_text(tmp_path: Path) -> None:
    run = green([], no_browser)
    review = "Status: PASS\nasked jane.doe@example.com"

    report = BUILD.build(
        project(tmp_path), tmp_path / "out", run, "T", CRITERIA, review, False, False, no_ui=True
    )

    assert report["masking"]["status"] == "findings"
    assert report["masking"]["findings"] == [{"step": "report text", "kinds": ["email"]}]


def test_the_share_gate_allows_a_clean_no_ui_report(tmp_path: Path) -> None:
    run = green([], no_browser)
    out = tmp_path / "out"
    BUILD.build(project(tmp_path), out, run, "T", CRITERIA, None, False, False, no_ui=True)
    spec = util.spec_from_file_location(
        "share_gate_screens", SKILL.parent / "share-report" / "share_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    allowed, reason = gate.decide(out)
    assert allowed, reason


def test_browser_without_spec_fails_and_runs_no_default_pages(tmp_path: Path) -> None:
    run = green([], no_browser)

    report = BUILD.build(project(tmp_path), tmp_path / "out", run, "T", CRITERIA, None, True, False)

    assert browser_axis(report) == {"name": "Browser", "status": "FAIL", "evidence": NO_SCREENS}
    assert report["verdict"] == "FAIL"
    assert report["screenshots"] == []


def test_each_step_shows_its_page_next_to_its_close_up(tmp_path: Path) -> None:
    steps = [
        {
            "name": "dashboard",
            "screenshot": "01-dashboard.png",
            "element_screenshot": "01-dashboard-element.png",
            "problems": [],
        },
        {"name": "reviews", "screenshot": "02-reviews.png", "problems": []},
    ]
    spec = tmp_path / "spec.json"
    spec.write_text("{}")
    run = green([], browser_writing(steps))

    report = BUILD.build(
        project(tmp_path), tmp_path / "out", run, "T", CRITERIA, None, True, False, spec=spec
    )

    assert browser_axis(report)["status"] == "PASS"
    assert [Path(p).name for p in report["screenshots"]] == ["01-dashboard.png", "02-reviews.png"]
    close_ups = {Path(k).name: Path(v).name for k, v in report["close_ups"].items()}
    assert close_ups == {"01-dashboard.png": "01-dashboard-element.png"}
    page = (tmp_path / "out" / "report.html").read_text()
    pair = page.index('<div class="pair">')
    assert page.index("<figcaption>01-dashboard</figcaption>") > pair
    assert page.index("<figcaption>01-dashboard (close-up)</figcaption>") > pair
    assert page.count('<div class="pair">') == 1
    assert "<figcaption>02-reviews</figcaption>" in page


def test_a_failed_capture_fails_the_browser_axis_and_names_the_step(tmp_path: Path) -> None:
    steps = [
        {
            "name": "dashboard",
            "screenshot": "01-dashboard.png",
            "element_screenshot": "",
            "problems": ["capture: no visible element for #gone"],
        }
    ]
    spec = tmp_path / "spec.json"
    spec.write_text("{}")
    run = green([], browser_writing(steps, status="not clean"))

    report = BUILD.build(
        project(tmp_path), tmp_path / "out", run, "T", CRITERIA, None, True, False, spec=spec
    )

    axis = browser_axis(report)
    assert axis["status"] == "FAIL"
    assert "capture failed in step dashboard" in axis["evidence"]
    assert report["verdict"] == "FAIL"


def test_browser_and_no_ui_together_are_refused(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        BUILD.main(["--title", "T", "--browser", "--no-ui", "--no-open"])

    assert stop.value.code == 2
    assert "usage:" in capsys.readouterr().err
