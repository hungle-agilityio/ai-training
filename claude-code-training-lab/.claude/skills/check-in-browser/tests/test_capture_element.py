"""Tests of the close-up screenshot of one element per step ("capture"), without a browser.

Run: uv run pytest .claude/skills/check-in-browser/tests --no-cov -q
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:1"
FAKE_EMAIL = "jane.doe@example.com"


def load() -> ModuleType:
    spec = util.spec_from_file_location("browser_check_capture", SKILL / "browser_check.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()


class FakeLocator:
    def __init__(self, count: int, visible: bool) -> None:
        self._count, self._visible = count, visible

    @property
    def first(self) -> "FakeLocator":
        return self

    def count(self) -> int:
        return self._count

    def is_visible(self) -> bool:
        return self._count > 0 and self._visible

    def screenshot(self, path: str, **_: Any) -> None:
        Path(path).write_bytes(b"element")


class FakePage:
    """Just enough of a Playwright page to run one step without a browser."""

    url = BASE + "/dashboard/"

    def __init__(self, body: str = "Dashboard", count: int = 1, visible: bool = True) -> None:
        self.body, self.count, self.visible = body, count, visible
        self.located: list[str] = []

    def on(self, event: str, handler: Any) -> None:
        return None

    def goto(self, url: str, **_: Any) -> None:
        return None

    def screenshot(self, path: str, full_page: bool) -> None:
        Path(path).write_bytes(b"page")

    def locator(self, selector: str) -> FakeLocator:
        self.located.append(selector)
        return FakeLocator(self.count, self.visible)

    def title(self) -> str:
        return "Dashboard"

    def inner_text(self, selector: str) -> str:
        return self.body


def step(**extra: Any) -> dict[str, Any]:
    return {"name": "dash", "goto": "/dashboard/", **extra}


def test_a_capture_step_saves_the_page_and_the_element(tmp_path: Path) -> None:
    page = FakePage()
    record, ok = CHECK.run_step(page, BASE, step(capture="h1"), tmp_path, 1)

    assert ok and record["problems"] == []
    assert page.located == ["h1"]
    assert record["screenshot"] == "01-dash.png"
    assert record["element_screenshot"] == "01-dash-element.png"
    assert (tmp_path / "01-dash.png").read_bytes() == b"page"
    assert (tmp_path / "01-dash-element.png").read_bytes() == b"element"


def test_a_selector_that_matches_nothing_fails_the_step(tmp_path: Path) -> None:
    record, _ = CHECK.run_step(
        FakePage(count=0), BASE, step(capture="#does-not-exist"), tmp_path, 1
    )

    assert record["problems"] == ["capture: no visible element for #does-not-exist"]
    assert record["element_screenshot"] == ""
    assert not (tmp_path / "01-dash-element.png").exists()
    assert (tmp_path / "01-dash.png").exists()


def test_a_hidden_element_fails_the_step(tmp_path: Path) -> None:
    record, _ = CHECK.run_step(FakePage(visible=False), BASE, step(capture=".hidden"), tmp_path, 1)

    assert record["problems"] == ["capture: no visible element for .hidden"]
    assert not (tmp_path / "01-dash-element.png").exists()


def test_a_failed_capture_makes_the_run_not_clean() -> None:
    record = {
        "name": "dash",
        "console_errors": [],
        "page_errors": [],
        "network_failures": [],
        "problems": ["capture: no visible element for #x"],
        "masking_findings": [],
    }

    assert CHECK.summarize([record], None)["status"] == "not clean"


def test_a_failed_capture_exits_with_one(monkeypatch: Any, tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"steps": [step(capture="#x")]}))
    record = {
        "name": "dash",
        "url": "/dashboard/",
        "screenshot": "01-dash.png",
        "element_screenshot": "",
        "console_errors": [],
        "page_errors": [],
        "network_failures": [],
        "problems": ["capture: no visible element for #x"],
        "masking_findings": [],
    }
    monkeypatch.setattr(CHECK, "run", lambda *a, **kw: CHECK.summarize([record], None))

    assert CHECK.main(["--out", str(tmp_path / "out"), "--spec", str(spec)]) == 1


def test_personal_data_deletes_both_screenshots_of_the_step(tmp_path: Path) -> None:
    page = FakePage(body=f"Review: contact {FAKE_EMAIL}")
    record, _ = CHECK.run_step(page, BASE, step(capture="h1"), tmp_path, 1)

    assert record["masking_findings"] == ["email"]
    assert record["screenshot"] == "" and record["element_screenshot"] == ""
    assert not (tmp_path / "01-dash.png").exists()
    assert not (tmp_path / "01-dash-element.png").exists()


def test_a_step_without_capture_takes_no_close_up(tmp_path: Path) -> None:
    page = FakePage()
    record, ok = CHECK.run_step(page, BASE, step(), tmp_path, 1)

    assert ok and page.located == []
    assert "element_screenshot" not in record
    assert sorted(path.name for path in tmp_path.iterdir()) == ["01-dash.png"]
