"""Tests of "Design vs build" in the verify report (matrix rows M6 to M11 of issue 503).

Assumed contract: tests patch `BUILD.capture_designs` on the loaded build_report module;
`build()` takes `design: Path | None = None`; `main()` takes `--design PATH`.

Run: uv run pytest ../plugins/agent-flow/skills/build-verify-report/tests --no-cov -q
"""

import json
import sys
from collections.abc import Callable, Iterator
from importlib import import_module, util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]
SKILLS = SKILL.parent
Runner = Callable[[list[str], Path], tuple[int, str]]
PROTOTYPE = (
    '<html><body><script>const SCENARIOS = [["one", "G", "L"]];'
    "document.body.textContent = location.hash;</script></body></html>"
)


def load_module(name: str, file: str) -> ModuleType:
    spec = util.spec_from_file_location(name, SKILL / file)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load_module("build_report_design", "build_report.py")


def green(browser: Callable[[list[str]], tuple[int, str]]) -> Runner:
    """Every check green; the browser check is answered by the given function."""

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
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


def browser_writing(steps: list[dict[str, Any]]) -> Callable[[list[str]], tuple[int, str]]:
    """A fake browser check that writes result.json and the screenshots its steps name."""

    def browser(args: list[str]) -> tuple[int, str]:
        folder = Path(args[args.index("--out") + 1])
        folder.mkdir(parents=True, exist_ok=True)
        for step in steps:
            if step.get("screenshot"):
                (folder / step["screenshot"]).write_bytes(b"png")
        result = {
            "status": "clean",
            "steps": steps,
            "console_errors": 0,
            "network_failures": 0,
            "problems": 0,
            "masking": {"status": "clean", "findings": []},
        }
        (folder / "result.json").write_text(json.dumps(result))
        return 0, "result: clean"

    return browser


def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / "reviews" / "tests").mkdir(parents=True, exist_ok=True)
    (root / "reviews" / "tests" / "test_q.py").write_text(
        "def test_q(django_assert_num_queries):\n    pass\n"
    )
    return root


CRITERIA = {"criteria": [{"text": "a", "status": "PASS", "evidence": "x"}]}
RESULT_STEPS = [{"name": "dashboard", "screenshot": "01-dashboard.png", "problems": []}]


def write_spec(tmp_path: Path, steps: list[dict[str, Any]], viewport: str | None = None) -> Path:
    data: dict[str, Any] = {"steps": steps}
    if viewport:
        data["viewport"] = viewport
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(data))
    return spec


def write_prototype(tmp_path: Path) -> Path:
    prototype = tmp_path / "prototype.html"
    prototype.write_text(PROTOTYPE)
    return prototype


def run_build(tmp_path: Path, spec: Path, design: Path | None, out: str = "out") -> dict[str, Any]:
    run = green(browser_writing(RESULT_STEPS))
    report: dict[str, Any] = BUILD.build(
        project(tmp_path),
        tmp_path / out,
        run,
        "T",
        CRITERIA,
        None,
        True,
        False,
        spec=spec,
        design=design,
    )
    return report


def png_width(path: Path) -> int:
    return int.from_bytes(path.read_bytes()[16:20], "big")


@pytest.fixture
def chromium() -> None:
    """Skip when Chromium cannot launch (CI installs none)."""
    try:
        sync_api = import_module("playwright.sync_api")
        with sync_api.sync_playwright() as playwright:
            playwright.chromium.launch().close()
    except Exception as error:
        pytest.skip(f"browser test skipped: Chromium not available ({error})")


@pytest.fixture
def no_playwright(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replace Playwright by a fake whose start raises; the list records the starts."""
    starts: list[str] = []

    def sync_playwright() -> Any:
        starts.append("started")
        raise RuntimeError("boom\nsecond line")

    fake = ModuleType("playwright.sync_api")
    fake.sync_playwright = sync_playwright  # type: ignore[attr-defined]
    parent = ModuleType("playwright")
    parent.sync_api = fake  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", parent)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", fake)
    return starts


@pytest.fixture
def capture_module() -> Iterator[ModuleType]:
    yield load_module("design_capture_under_test", "design_capture.py")


# M6: the design next to the build, at the viewport's width (needs Chromium)


def test_capture_designs_saves_a_full_page_picture_at_the_viewport_width(
    tmp_path: Path, chromium: None, capture_module: ModuleType
) -> None:
    """M6 (AC2)."""
    steps = [{"name": "home", "design": "one"}, {"name": "plain"}]

    pairs = capture_module.capture_designs(
        write_prototype(tmp_path), steps, {"width": 390, "height": 844}, tmp_path / "shots"
    )

    assert pairs == [
        {"step": "home", "state": "one", "design_screenshot": "design-01-home.png", "note": ""}
    ]
    assert png_width(tmp_path / "shots" / "design-01-home.png") == 390


def test_report_shows_design_and_build_side_by_side_at_the_same_width(
    tmp_path: Path, chromium: None
) -> None:
    """M6 (AC2, AC3, AC4): the whole path with a real prototype page."""
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "one"}], "390x844")

    report = run_build(tmp_path, spec, write_prototype(tmp_path))

    page = (tmp_path / "out" / "report.html").read_text()
    assert "<h2>Design vs build</h2>" in page
    assert "<figcaption>Design: one</figcaption>" in page
    assert "<figcaption>Build: dashboard</figcaption>" in page
    design_image = Path(report["design_pairs"][0]["design_screenshot"])
    assert design_image.is_absolute()
    assert png_width(design_image) == 390


# M6/M8: the report page and report.json from the list capture_designs returns (no browser)


def fake_capture(
    entries: list[dict[str, Any]],
) -> Callable[[Path, list[dict[str, Any]], dict[str, int], Path], list[dict[str, Any]]]:
    def capture(
        prototype: Path, steps: list[dict[str, Any]], viewport: dict[str, int], out_dir: Path
    ) -> list[dict[str, Any]]:
        out_dir.mkdir(parents=True, exist_ok=True)
        for entry in entries:
            if entry["design_screenshot"]:
                (out_dir / entry["design_screenshot"]).write_bytes(b"png")
        return [dict(e) for e in entries]

    return capture


FOUND = {
    "step": "dashboard",
    "state": "dashboard",
    "design_screenshot": "design-01-dashboard.png",
    "note": "",
}


def test_pair_holds_design_left_and_build_right_after_the_screenshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M6 (AC3, AC4)."""
    monkeypatch.setattr(BUILD, "capture_designs", fake_capture([FOUND]))
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "dashboard"}])

    report = run_build(tmp_path, spec, write_prototype(tmp_path))

    pair = report["design_pairs"][0]
    browser = tmp_path / "out" / "browser"
    assert pair["build_screenshot"] == str(browser / "01-dashboard.png")
    assert pair["design_screenshot"] == str(browser / "design-01-dashboard.png")
    saved = json.loads((tmp_path / "out" / "report.json").read_text())
    assert saved["design_pairs"] == report["design_pairs"]
    for name in ("report.html", "report-share.html"):
        page = (tmp_path / "out" / name).read_text()
        heading = page.index("<h2>Design vs build</h2>")
        assert page.index("<h2>Screenshots</h2>") < heading
        section = page[heading:]
        assert section.index('<div class="shots">') < section.index('<div class="pair">')
        assert section.count('<div class="pair">') == 1
        assert section.index("Design: dashboard") < section.index("Build: dashboard")
        assert "LIGHTBOX" in page or "lightbox" in page


def test_a_missing_build_screenshot_is_named_next_to_the_design_figure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M6 (AC4)."""
    steps = [{"name": "other", "screenshot": "01-other.png", "problems": []}]
    monkeypatch.setattr(BUILD, "capture_designs", fake_capture([FOUND]))
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "dashboard"}])

    BUILD.build(
        project(tmp_path),
        tmp_path / "out",
        green(browser_writing(steps)),
        "T",
        CRITERIA,
        None,
        True,
        False,
        spec=spec,
        design=write_prototype(tmp_path),
    )

    page = (tmp_path / "out" / "report.html").read_text()
    assert "Build screenshot missing: dashboard" in page
    assert "Design: dashboard" in page
    assert "Build: dashboard" not in page


# M7: no design step


def test_no_design_step_gives_empty_pairs_and_no_heading(tmp_path: Path) -> None:
    """M7."""
    spec = write_spec(tmp_path, [{"name": "dashboard"}])

    report = run_build(tmp_path, spec, None)

    assert report["design_pairs"] == []
    assert "Design vs build" not in (tmp_path / "out" / "report.html").read_text()
    assert "Design vs build" not in (tmp_path / "out" / "report-share.html").read_text()


def test_no_ui_run_writes_empty_design_pairs(tmp_path: Path) -> None:
    """M7 (AC3)."""
    report = BUILD.build(
        project(tmp_path),
        tmp_path / "out",
        green(lambda args: (_ for _ in ()).throw(AssertionError("no browser"))),
        "T",
        CRITERIA,
        None,
        False,
        False,
        no_ui=True,
    )

    assert report["design_pairs"] == []
    assert "Design vs build" not in (tmp_path / "out" / "report.html").read_text()


# M8: a state id the prototype does not have


def test_capture_designs_names_an_unknown_state_and_saves_no_picture(
    tmp_path: Path, chromium: None, capture_module: ModuleType
) -> None:
    """M8 (AC2)."""
    pairs = capture_module.capture_designs(
        write_prototype(tmp_path),
        [{"name": "home", "design": "no-such-state"}],
        {"width": 1280, "height": 800},
        tmp_path / "shots",
    )

    assert pairs == [
        {
            "step": "home",
            "state": "no-such-state",
            "design_screenshot": None,
            "note": "Design not found: no-such-state",
        }
    ]


def test_unknown_state_is_shown_and_does_not_change_the_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M8 (AC2, AC4, AC5)."""
    missing = {
        "step": "dashboard",
        "state": "no-such-state",
        "design_screenshot": None,
        "note": "Design not found: no-such-state",
    }
    monkeypatch.setattr(BUILD, "capture_designs", fake_capture([missing]))
    plain = run_build(tmp_path, write_spec(tmp_path, [{"name": "dashboard"}]), None, "plain")
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "no-such-state"}])

    report = run_build(tmp_path, spec, write_prototype(tmp_path), "with")

    assert report["design_pairs"][0]["design_screenshot"] is None
    assert report["design_pairs"][0]["note"] == "Design not found: no-such-state"
    page = (tmp_path / "with" / "report.html").read_text()
    assert "Design not found: no-such-state" in page
    assert "Build: dashboard" in page
    assert report["verdict"] == plain["verdict"]
    assert report["axes"] == plain["axes"]


# M9: no prototype file; a Playwright error


def test_no_prototype_file_gives_design_not_found_and_starts_no_playwright(
    tmp_path: Path, no_playwright: list[str], capture_module: ModuleType
) -> None:
    """M9 (AC2)."""
    steps = [{"name": "a", "design": "one"}, {"name": "b", "design": "two"}, {"name": "c"}]

    pairs = capture_module.capture_designs(
        tmp_path / "missing.html", steps, {"width": 1280, "height": 800}, tmp_path / "shots"
    )

    assert [p["note"] for p in pairs] == ["Design not found: one", "Design not found: two"]
    assert [p["design_screenshot"] for p in pairs] == [None, None]
    assert no_playwright == []


def test_no_prototype_file_leaves_the_report_verdict_unchanged(
    tmp_path: Path, no_playwright: list[str]
) -> None:
    """M9 (AC2, AC5): the verdict decides the exit code (PASS 0, FAIL 1, else 2)."""
    plain = run_build(tmp_path, write_spec(tmp_path, [{"name": "dashboard"}]), None, "plain")
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "one"}])

    report = run_build(tmp_path, spec, tmp_path / "missing.html", "with")

    assert report["design_pairs"][0]["note"].startswith("Design not found")
    assert report["verdict"] == plain["verdict"]
    assert report["axes"] == plain["axes"]
    assert no_playwright == []


def test_a_playwright_error_is_caught_and_noted_on_every_step(
    tmp_path: Path, no_playwright: list[str], capture_module: ModuleType
) -> None:
    """M9 (AC5)."""
    steps = [{"name": "a", "design": "one"}, {"name": "b", "design": "one"}]

    pairs = capture_module.capture_designs(
        write_prototype(tmp_path), steps, {"width": 1280, "height": 800}, tmp_path / "shots"
    )

    assert [p["note"] for p in pairs] == ["Design not captured: boom"] * 2
    assert [p["design_screenshot"] for p in pairs] == [None, None]


# M10: --design and the spec's viewport reach capture_designs


class Recorder:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self, prototype: Path, steps: list[dict[str, Any]], viewport: dict[str, int], out_dir: Path
    ) -> list[dict[str, Any]]:
        self.calls.append(
            {"prototype": prototype, "steps": steps, "viewport": viewport, "out_dir": out_dir}
        )
        return []


def test_design_path_and_spec_viewport_reach_capture_designs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M10 (AC3, AC6)."""
    recorder = Recorder()
    monkeypatch.setattr(BUILD, "capture_designs", recorder)
    prototype = write_prototype(tmp_path)
    steps = [{"name": "dashboard", "design": "one"}]

    run_build(tmp_path, write_spec(tmp_path, steps, "390x844"), prototype)

    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["prototype"] == prototype
    assert call["viewport"] == {"width": 390, "height": 844}
    assert call["steps"] == steps
    assert call["out_dir"] == tmp_path / "out" / "browser"


def test_viewport_defaults_to_1280_by_800(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M10 (AC3)."""
    recorder = Recorder()
    monkeypatch.setattr(BUILD, "capture_designs", recorder)
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "one"}])

    run_build(tmp_path, spec, write_prototype(tmp_path))

    assert recorder.calls[0]["viewport"] == {"width": 1280, "height": 800}


def test_prototype_defaults_to_design_app_prototype_under_the_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M10 (AC6)."""
    recorder = Recorder()
    monkeypatch.setattr(BUILD, "capture_designs", recorder)
    spec = write_spec(tmp_path, [{"name": "dashboard", "design": "one"}])

    run_build(tmp_path, spec, None)

    assert recorder.calls[0]["prototype"] == (
        tmp_path / "project" / "design" / "app" / "prototype.html"
    )


def test_main_accepts_design_and_passes_it_to_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M10 (AC6)."""
    seen: dict[str, Any] = {}

    def fake_build(*args: Any, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        return {"axes": [], "verdict": "PASS"}

    monkeypatch.setattr(BUILD, "build", fake_build)
    prototype = write_prototype(tmp_path)

    code = BUILD.main(["--title", "T", "--no-ui", "--no-open", "--design", str(prototype)])

    assert code == 0
    assert seen["design"] == prototype


# M11: the skill texts

NEW_WORK_QUEUE = (
    'A `Design` link and each step\'s `"design"` state of the app prototype are the UI to '
    "build; the verify report shows each design next to the built screen (Design vs build). "
    "A difference is reported in the pull request, never fixed by changing the prototype."
)
NEW_WRITE_ISSUE = (
    "(the prototype state the build must match; every step whose page has a state names it)"
)


def test_work_queue_skill_holds_the_design_vs_build_sentence() -> None:
    """M11 (AC7)."""
    assert NEW_WORK_QUEUE in (SKILLS / "work-queue" / "SKILL.md").read_text()


def test_write_issue_skill_lists_the_design_key_of_a_screen_step() -> None:
    """M11 (AC7)."""
    text = (SKILLS / "write-issue" / "SKILL.md").read_text()
    assert '`"design"` ' + NEW_WRITE_ISSUE in text


def test_build_verify_report_skill_documents_design_and_the_section() -> None:
    """M11 (AC7)."""
    text = (SKILL / "SKILL.md").read_text()
    assert "--design" in text
    assert "Design vs build" in text


def test_no_skill_file_says_capture_before_after_compares_with_the_design() -> None:
    """M11 (AC7)."""
    offenders = [
        str(path.relative_to(SKILLS))
        for path in SKILLS.rglob("*")
        if path.is_file()
        and path.suffix in {".md", ".py", ".toml", ".json", ".txt"}
        and "compares the real screens with it" in path.read_text(errors="ignore")
        and "capture-before-after" in path.read_text(errors="ignore")
        and path != Path(__file__).resolve()
    ]
    assert offenders == []
