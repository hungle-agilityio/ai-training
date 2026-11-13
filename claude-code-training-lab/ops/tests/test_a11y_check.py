"""Accessibility of the main screens: the contrast fix, the axe scan, its CI step, the bootstrap."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from ops import a11y_check, bootstrap

ROOT = Path(__file__).resolve().parents[3]
APP = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "checks.yml"
REPO = "acme/shop"
REGRESSION = "Browser regression of the main screens"
A11Y = "Accessibility of the main screens"
A11Y_RUN = "uv run python ops/a11y_check.py --spec ops/regression_screens.json"
MISMATCH = "axe.min.js does not match axe-core 4.10.3"
Run = Callable[..., int]
COLOURS = """el => {
  const style = getComputedStyle(el);
  return [style.color, style.backgroundColor, style.opacity];
}"""


def _steps(text: str) -> list[tuple[str, str]]:
    """Return (name, block text) of each workflow step, in order."""
    parts = re.split(r"^ {6}- name: ", text, flags=re.MULTILINE)[1:]
    return [(p.splitlines()[0].strip(), p) for p in parts]


@pytest.fixture(scope="module")
def site() -> Iterator[tuple[str, str]]:
    """The app on a throw-away demo database, started with the helpers the scan uses."""
    check = a11y_check.browser_check
    with tempfile.TemporaryDirectory(prefix="a11y-test-") as temp:
        port = check.free_port()
        base = f"http://127.0.0.1:{port}"
        password = check.one_run_secret()
        server = check.start_app(APP, Path(temp) / "demo.sqlite3", port, password=password)
        try:
            assert check.wait_until_ready(base + "/dashboard/")
            yield base, password
        finally:
            server.terminate()
            server.wait(timeout=10)


def _signed_in_page(playwright: Any, site: tuple[str, str], scheme: str) -> tuple[Any, Any]:
    check = a11y_check.browser_check
    base, password = site
    browser = playwright.chromium.launch()
    context = browser.new_context(color_scheme=scheme, viewport=check.VIEWPORT)
    page = context.new_page()
    check.sign_in(page, base, password)
    return browser, page


# M34 (AC1)


def test_light_goal_badge_is_darker_green_and_the_sidebar_note_is_full_strength(
    site: tuple[str, str],
) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser, page = _signed_in_page(playwright, site, "light")
        try:
            page.goto(site[0] + "/dashboard/", wait_until="load")
            badge = page.locator(".badge-positive", has_text="Met").first
            colour, background, _ = badge.evaluate(COLOURS)
            _, _, opacity = page.locator(".sidebar-note").first.evaluate(COLOURS)
        finally:
            browser.close()

    assert colour == "rgb(23, 117, 63)"
    assert background == "rgb(224, 245, 234)"
    assert opacity == "1"


# M36 (AC1)


def test_dark_goal_link_on_a_location_page_uses_the_brand_colour(
    site: tuple[str, str],
) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser, page = _signed_in_page(playwright, site, "dark")
        try:
            page.goto(site[0] + "/dashboard/", wait_until="load")
            with page.expect_navigation(wait_until="load"):
                page.click("a[aria-label^='Details for']")
            link = page.get_by_role("link", name=re.compile("^(Set a goal|Change goal)$")).first
            colour, _, _ = link.evaluate(COLOURS)
        finally:
            browser.close()

    assert colour == "rgb(123, 147, 255)"


# M37 (AC3)


def test_a_changed_axe_file_stops_with_exit_2_before_the_app_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    data = bytearray(a11y_check.AXE_PATH.read_bytes())
    data[0] ^= 1
    changed = tmp_path / "axe.min.js"
    changed.write_bytes(bytes(data))
    monkeypatch.setattr(a11y_check, "AXE_PATH", changed)
    started: list[object] = []
    monkeypatch.setattr(
        a11y_check.browser_check, "start_app", lambda *args, **kwargs: started.append(args)
    )
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"steps": [{"name": "dashboard", "goto": "/dashboard/"}]}))

    code = a11y_check.main(["--spec", str(spec)])

    assert code == 2
    assert capsys.readouterr().out.splitlines() == [MISMATCH]
    assert started == []


def test_the_vendored_axe_file_is_axe_core_4_10_3() -> None:
    assert a11y_check.axe_matches()


# M38 (AC4)


def _violation(rule: str, impact: str, nodes: int, target: str = ".badge") -> dict[str, Any]:
    return {"id": rule, "impact": impact, "nodes": [{"target": [target]} for _ in range(nodes)]}


def test_a_serious_finding_is_a_fail_line_with_count_and_first_selector() -> None:
    lines = a11y_check.report_lines(
        "dashboard", "light", [_violation("color-contrast", "serious", 2)]
    )

    assert lines == ["FAIL dashboard light: color-contrast x2 (.badge)"]
    assert a11y_check.result_line(lines) == ("result: 1 failures", 1)


def test_a_critical_finding_is_a_fail_line() -> None:
    lines = a11y_check.report_lines("login", "dark", [_violation("label", "critical", 1, "#id_q")])

    assert lines == ["FAIL login dark: label x1 (#id_q)"]


def test_moderate_and_minor_findings_are_notes_before_pass() -> None:
    lines = a11y_check.report_lines(
        "dashboard",
        "light",
        [_violation("region", "moderate", 3), _violation("empty-heading", "minor", 1)],
    )

    assert lines == [
        "NOTE dashboard light: region x3",
        "NOTE dashboard light: empty-heading x1",
        "PASS dashboard light",
    ]
    assert a11y_check.result_line(lines) == ("result: clean", 0)


def test_lines_keep_the_order_of_the_findings_and_fail_leaves_out_pass() -> None:
    lines = a11y_check.report_lines(
        "reviews",
        "dark",
        [_violation("region", "moderate", 1), _violation("color-contrast", "serious", 1, "a")],
    )

    assert lines == [
        "NOTE reviews dark: region x1",
        "FAIL reviews dark: color-contrast x1 (a)",
    ]


def test_no_finding_is_a_pass_line_and_a_clean_result() -> None:
    lines = a11y_check.report_lines("dashboard", "light", [])

    assert lines == ["PASS dashboard light"]
    assert a11y_check.result_line(lines) == ("result: clean", 0)


def test_the_result_counts_every_fail_line() -> None:
    lines = [
        "FAIL dashboard light: color-contrast x2 (.badge)",
        "PASS reviews light",
        "FAIL settings dark: could not open the page",
    ]

    assert a11y_check.result_line(lines) == ("result: 2 failures", 1)


# M39 (AC3)


def test_one_step_spec_in_the_light_scheme_is_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"steps": [{"name": "dashboard", "goto": "/dashboard/"}]}))

    code = a11y_check.main(["--spec", str(spec), "--scheme", "light"])

    lines = [line for line in capsys.readouterr().out.splitlines() if not line.startswith("NOTE ")]
    assert lines == ["PASS login light", "PASS dashboard light", "result: clean"]
    assert code == 0


# M40 (AC5)


def test_checks_scan_accessibility_right_after_the_browser_regression() -> None:
    steps = _steps(WORKFLOW.read_text())
    names = [name for name, _ in steps]

    assert names.count(A11Y) == 1
    assert names[names.index(REGRESSION) + 1] == A11Y
    block = dict(steps)[A11Y]
    match = re.search(r"^ {8}run: (.+)$", block, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1).strip() == A11Y_RUN
    assert "working-directory" not in block


# M41 (AC6)


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return fake


@pytest.fixture
def fake_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "gh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


@pytest.fixture
def target(tmp_path: Path) -> Path:
    path = tmp_path / "shop"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{REPO}.git"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


@pytest.fixture
def run(target: Path, home: Path, fake_gh: None) -> Run:
    def call(*extra: str) -> int:
        return bootstrap.main(
            [
                "--target", str(target),
                "--repo", REPO,
                "--owner", "acme-owner",
                "--app-dir", ".",
                "--name", "Shop",
                "--slug", "shop",
                "--ntfy-topic", "shop-test",
                "--no-labels",
                *extra,
            ]
        )  # fmt: skip

    return call


def _assert_no_accessibility_scan(target: Path) -> None:
    workflow = (target / ".github" / "workflows" / "checks.yml").read_text()

    assert A11Y not in [name for name, _ in _steps(workflow)]
    assert "a11y_check" not in workflow
    assert "Install uv" in workflow
    assert not [path for path in target.rglob("vendor") if ".git" not in path.parts]
    assert not list(target.rglob("axe.min.js"))
    assert not list(target.rglob("a11y_check.py"))


def test_bootstrap_default_layout_gets_no_accessibility_scan(run: Run, target: Path) -> None:
    assert run() == 0

    _assert_no_accessibility_scan(target)


def test_bootstrap_python_stack_gets_no_accessibility_scan(run: Run, target: Path) -> None:
    assert run("--stack", "python") == 0

    _assert_no_accessibility_scan(target)
