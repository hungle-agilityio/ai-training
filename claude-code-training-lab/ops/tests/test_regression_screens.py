"""Browser regression of the main screens: its spec, its CI steps, skipped by bootstrap."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap

ROOT = Path(__file__).resolve().parents[3]
APP = Path(__file__).resolve().parents[2]
SPEC = APP / "ops" / "regression_screens.json"
WORKFLOW = ROOT / ".github" / "workflows" / "checks.yml"
REPO = "acme/shop"
INSTALL = "Install the browser"
REGRESSION = "Browser regression of the main screens"
Run = Callable[..., int]

EXPECTED_STEPS: list[dict[str, object]] = [
    {
        "name": "dashboard",
        "goto": "/dashboard/",
        "expect": ["Reputation dashboard", "Riverside"],
        "capture": "#kpi-open-cases",
    },
    {
        "name": "location",
        "goto": "/dashboard/",
        "actions": [{"click": "a[aria-label^='Details for']"}],
        "expect": ["Weekly trend", "Rating breakdown", "Latest reviews"],
    },
    {"name": "reviews", "goto": "/reviews/", "expect": ["Reviews", "Follow-up"]},
    {
        "name": "reply",
        "goto": "/reviews/?rating=bad",
        "actions": [{"click": "a[href$='/reply/']"}],
        "expect": ["Reply to a review", "Follow-up", "Template"],
    },
    {"name": "replies", "goto": "/replies/", "expect": ["Reply drafts"]},
    {
        "name": "settings",
        "goto": "/settings/",
        "expect": ["Settings", "Locations", "Location goals", "Reply templates"],
    },
    {"name": "reports", "goto": "/reports/", "expect": ["Monthly report"]},
    {"name": "compare", "goto": "/compare/", "expect": ["Compare locations"]},
    {"name": "topics", "goto": "/topics/", "expect": ["Topics"]},
]


def _steps(text: str) -> list[tuple[str, str]]:
    """Return (name, block text) of each workflow step, in order."""
    parts = re.split(r"^ {6}- name: ", text, flags=re.MULTILINE)[1:]
    return [(p.splitlines()[0].strip(), p) for p in parts]


def _run_line(block: str) -> str:
    match = re.search(r"^ {8}run: (.+)$", block, flags=re.MULTILINE)
    assert match is not None
    return match.group(1).strip()


# M17 (AC1)


def test_spec_file_holds_the_nine_steps_in_order() -> None:
    data = json.loads(SPEC.read_text())

    assert list(data) == ["steps"]
    assert data["steps"] == EXPECTED_STEPS
    assert [s["name"] for s in data["steps"]] == [s["name"] for s in EXPECTED_STEPS]


def test_spec_file_is_two_space_indented_with_a_final_newline() -> None:
    text = SPEC.read_text()

    assert text.endswith("\n") and not text.endswith("\n\n")
    assert text == json.dumps(json.loads(text), indent=2) + "\n"


def test_only_the_first_step_captures_an_element() -> None:
    steps = json.loads(SPEC.read_text())["steps"]

    assert steps[0]["capture"] == "#kpi-open-cases"
    assert all("capture" not in s for s in steps[1:])


# M18 (AC2)


def test_checks_install_the_browser_right_after_the_app_tests() -> None:
    steps = _steps(WORKFLOW.read_text())
    names = [n for n, _ in steps]

    index = names.index("App tests with coverage")
    assert names[index + 1] == INSTALL
    assert _run_line(steps[index + 1][1]) == "uv run playwright install --with-deps chromium"


def test_checks_run_the_browser_regression_after_the_install_step() -> None:
    steps = _steps(WORKFLOW.read_text())
    names = [n for n, _ in steps]

    index = names.index(INSTALL)
    assert names[index + 1] == REGRESSION
    assert _run_line(steps[index + 1][1]) == (
        "uv run python .claude/skills/check-in-browser/browser_check.py"
        " --spec ops/regression_screens.json"
    )


def test_the_new_steps_set_no_working_directory() -> None:
    steps = dict(_steps(WORKFLOW.read_text()))

    assert "working-directory" not in steps[INSTALL]
    assert "working-directory" not in steps[REGRESSION]


def test_the_job_timeout_stays_ten_minutes() -> None:
    assert "timeout-minutes: 10" in WORKFLOW.read_text()


# M18b (AC3)


@pytest.fixture(autouse=True)
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    return fake


@pytest.fixture(autouse=True)
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
def run(target: Path) -> Run:
    def call(*extra: str, app_dir: str = ".") -> int:
        return bootstrap.main(
            [
                "--target", str(target),
                "--repo", REPO,
                "--owner", "acme-owner",
                "--app-dir", app_dir,
                "--name", "Shop",
                "--slug", "shop",
                "--ntfy-topic", "shop-test",
                "--no-labels",
                *extra,
            ]
        )  # fmt: skip

    return call


def _assert_no_regression(target: Path) -> None:
    workflow = (target / ".github" / "workflows" / "checks.yml").read_text()
    names = [n for n, _ in _steps(workflow)]

    assert INSTALL not in names
    assert REGRESSION not in names
    assert "playwright" not in workflow
    assert "regression_screens" not in workflow
    assert "browser_check.py" not in workflow
    assert "App tests with coverage" in names or "Install uv" in names
    assert not list(target.rglob("regression_screens.json"))


def test_bootstrap_default_layout_drops_the_browser_steps_and_the_spec(
    run: Run, target: Path
) -> None:
    assert run() == 0

    _assert_no_regression(target)


def test_bootstrap_python_stack_drops_the_browser_steps_and_the_spec(
    run: Run, target: Path
) -> None:
    assert run("--stack", "python") == 0

    _assert_no_regression(target)


def test_bootstrap_keeps_the_other_steps_of_the_checks(run: Run, target: Path) -> None:
    assert run() == 0

    workflow = (target / ".github" / "workflows" / "checks.yml").read_text()
    for step in ("Install uv", "Lint", "Types", "App tests with coverage"):
        assert f"- name: {step}" in workflow
