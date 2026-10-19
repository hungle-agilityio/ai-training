"""Tests of the browser check, without a browser.

Run: uv run pytest .claude/skills/check-in-browser/tests --no-cov -q
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]


def load() -> ModuleType:
    spec = util.spec_from_file_location("browser_check", SKILL / "browser_check.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()


def step(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "name": "s",
        "url": "/x",
        "screenshot": "01-s.png",
        "console_errors": [],
        "console_warnings": [],
        "page_errors": [],
        "network_failures": [],
        "problems": [],
    }
    return {**base, **over}


def test_judge_accepts_a_page_with_the_expected_text() -> None:
    assert CHECK.judge({"expect": ["Hello"], "absent": ["Bye"]}, "Hello world") == []


def test_judge_names_missing_and_forbidden_text() -> None:
    result = CHECK.judge({"expect": ["Hello"], "absent": ["Bye"]}, "Bye now")

    assert any("Hello" in line for line in result) and any("Bye" in line for line in result)


def test_summary_is_clean_only_when_nothing_is_wrong() -> None:
    assert CHECK.summarize([step()], None)["status"] == "clean"
    assert CHECK.summarize([step(console_errors=["boom"])], None)["status"] == "not clean"
    assert CHECK.summarize([step(page_errors=["boom"])], None)["status"] == "not clean"
    assert CHECK.summarize([step(network_failures=["404 /x"])], None)["status"] == "not clean"
    assert CHECK.summarize([step(problems=["text"])], None)["status"] == "not clean"
    assert CHECK.summarize([step()], "stopped")["status"] == "not clean"


def test_summary_counts_each_kind() -> None:
    summary = CHECK.summarize([step(console_errors=["a", "b"], network_failures=["x"])], None)

    assert summary["console_errors"] == 2 and summary["network_failures"] == 1


def test_default_steps_are_well_formed() -> None:
    names = [item["name"] for item in CHECK.DEFAULT_STEPS]

    assert len(names) == len(set(names)) >= 4
    assert all(item["goto"].startswith("/") for item in CHECK.DEFAULT_STEPS)


def test_load_steps_reads_a_list_or_an_object(tmp_path: Path) -> None:
    listed = tmp_path / "a.json"
    listed.write_text(json.dumps([{"name": "one", "goto": "/"}]))
    wrapped = tmp_path / "b.json"
    wrapped.write_text(json.dumps({"steps": [{"name": "two", "goto": "/"}]}))

    assert CHECK.load_steps(listed)[0]["name"] == "one"
    assert CHECK.load_steps(wrapped)[0]["name"] == "two"
    assert CHECK.load_steps(None) is CHECK.DEFAULT_STEPS


def test_load_steps_refuses_a_step_without_a_name(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"goto": "/"}]))

    with pytest.raises(ValueError):
        CHECK.load_steps(bad)


def test_project_root_is_the_folder_with_manage_py(tmp_path: Path) -> None:
    (tmp_path / "manage.py").write_text("")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    assert CHECK.project_root(nested) == tmp_path


class FakePage:
    """Just enough of a Playwright page to run one step without a browser."""

    url = "http://127.0.0.1:1/dashboard/"

    def __init__(self, fail_goto: bool = False, body: str = "Dashboard") -> None:
        self.fail_goto, self.body = fail_goto, body

    def on(self, event: str, handler: Any) -> None:
        return None

    def goto(self, url: str, **kwargs: Any) -> None:
        if self.fail_goto:
            raise RuntimeError("Timeout 15000ms exceeded.\nmore lines")

    def screenshot(self, path: str, full_page: bool) -> None:
        Path(path).write_bytes(b"png")

    def title(self) -> str:
        return "Dashboard"

    def inner_text(self, selector: str) -> str:
        return self.body


def test_run_step_records_a_good_step_and_takes_the_screenshot(tmp_path: Path) -> None:
    record, ok = CHECK.run_step(
        FakePage(),
        "http://127.0.0.1:1",
        {"name": "dash", "goto": "/dashboard/", "expect": ["Dashboard"]},
        tmp_path,
        1,
    )

    assert ok and record["problems"] == [] and (tmp_path / "01-dash.png").exists()
    assert record["url"] == "/dashboard/"


def test_run_step_reports_a_failed_action_and_still_takes_the_screenshot(tmp_path: Path) -> None:
    record, ok = CHECK.run_step(
        FakePage(fail_goto=True),
        "http://127.0.0.1:1",
        {"name": "dash", "goto": "/dashboard/"},
        tmp_path,
        2,
    )

    assert not ok
    assert any("action failed" in line for line in record["problems"])
    assert (tmp_path / "02-dash.png").exists()


def test_the_limit_of_failed_actions_is_three() -> None:
    assert CHECK.MAX_FAILED_ACTIONS == 3
