"""Tests of the sign-in before the steps and of the one-run secrets, without a browser.

Run: uv run pytest .claude/skills/check-in-browser/tests --no-cov -q
"""

import json
import os
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]


def load() -> ModuleType:
    spec = util.spec_from_file_location("browser_check_sign_in", SKILL / "browser_check.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()
BASE = "http://127.0.0.1:1"


class FakeProcess:
    pass


def started(monkeypatch: pytest.MonkeyPatch, debug: bool) -> tuple[list[Any], list[Any]]:
    runs: list[Any] = []
    servers: list[Any] = []
    monkeypatch.setattr(CHECK.subprocess, "run", lambda args, **kw: runs.append((args, kw)))
    monkeypatch.setattr(
        CHECK.subprocess, "Popen", lambda args, **kw: servers.append((args, kw)) or FakeProcess()
    )
    CHECK.start_app(Path("."), Path("db.sqlite3"), 8123, debug=debug, password="one-run")
    return runs, servers


def test_the_seed_gets_the_one_run_demo_password(monkeypatch: pytest.MonkeyPatch) -> None:
    runs, servers = started(monkeypatch, debug=True)
    assert all(kw["env"]["REVIEWRADAR_DEMO_PASSWORD"] == "one-run" for _, kw in runs)
    assert servers[0][1]["env"]["REVIEWRADAR_DEMO_PASSWORD"] == "one-run"


def test_debug_off_gets_a_one_run_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    runs, servers = started(monkeypatch, debug=False)
    keys = {kw["env"]["DJANGO_SECRET_KEY"] for _, kw in [*runs, *servers]}
    assert len(keys) == 1
    key = keys.pop()
    assert len(key) >= 32 and key != "dev-only-insecure-key"


def test_debug_on_sets_no_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    runs, _ = started(monkeypatch, debug=True)
    assert all("DJANGO_SECRET_KEY" not in kw["env"] for _, kw in runs)


def test_the_secrets_never_reach_the_calling_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.delenv("REVIEWRADAR_DEMO_PASSWORD", raising=False)
    started(monkeypatch, debug=False)
    assert "DJANGO_SECRET_KEY" not in os.environ
    assert "REVIEWRADAR_DEMO_PASSWORD" not in os.environ


def test_each_run_gets_a_new_secret() -> None:
    assert CHECK.one_run_secret() != CHECK.one_run_secret()


class FakePage:
    def __init__(self, url_after: str) -> None:
        self.url = BASE
        self.url_after = url_after
        self.filled: dict[str, str] = {}
        self.clicked: list[str] = []

    def goto(self, url: str, **_: Any) -> None:
        self.url = url

    def fill(self, selector: str, value: str, **_: Any) -> None:
        self.filled[selector] = value

    def expect_navigation(self, **_: Any) -> Any:
        page = self

        class Navigation:
            def __enter__(self) -> None:
                return None

            def __exit__(self, *exc: object) -> None:
                page.url = BASE + page.url_after

        return Navigation()

    def click(self, selector: str, **_: Any) -> None:
        self.clicked.append(selector)


def test_sign_in_fills_the_real_form_as_demo() -> None:
    page = FakePage("/dashboard/")
    CHECK.sign_in(page, BASE, "one-run")
    assert page.filled == {"#id_username": "demo", "#id_password": "one-run"}
    assert page.clicked == ["button[type=submit]"]


def test_still_on_the_sign_in_page_is_a_failed_sign_in() -> None:
    page = FakePage("/login/")
    with pytest.raises(CHECK.SignInError, match="could not sign in as demo"):
        CHECK.sign_in(page, BASE, "wrong")


def test_a_failed_sign_in_never_shows_the_password() -> None:
    page = FakePage("/login/")
    with pytest.raises(CHECK.SignInError) as error:
        CHECK.sign_in(page, BASE, "secret-value-123")
    assert "secret-value-123" not in str(error.value)


def capture_run(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        raise RuntimeError("stop here")

    monkeypatch.setattr(CHECK, "run", fake_run)
    return seen


def test_steps_run_signed_in_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path)])
    assert seen["signed_in"] is True


def test_the_flag_runs_signed_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path), "--signed-out"])
    assert seen["signed_in"] is False


def test_a_spec_can_run_signed_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"sign_in": False, "steps": [{"name": "a", "goto": "/login/"}]}))
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path / "out"), "--spec", str(spec)])
    assert seen["signed_in"] is False


def test_a_spec_with_a_wrong_sign_in_value_stops_with_one_line(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"sign_in": "no", "steps": [{"name": "a", "goto": "/"}]}))
    code = CHECK.main(["--out", str(tmp_path / "out"), "--spec", str(spec)])
    out = capsys.readouterr().out.strip()
    assert code == 2
    assert len(out.splitlines()) == 1 and "sign_in" in out


def test_a_failed_sign_in_stops_with_not_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    def failing_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise CHECK.SignInError("could not sign in as demo")

    monkeypatch.setattr(CHECK, "run", failing_run)
    code = CHECK.main(["--out", str(tmp_path)])
    assert code == 2
    assert capsys.readouterr().out.strip() == "NOT RUN: could not sign in as demo"


def test_the_summary_says_whether_steps_were_signed_in() -> None:
    assert CHECK.summarize([], None)["signed_in"] is True
    assert CHECK.summarize([], None, signed_in=False)["signed_in"] is False


class Message:
    def __init__(self, url: str) -> None:
        self.location = {"url": url, "lineNumber": 0, "columnNumber": 0}


def test_the_console_echo_of_a_missing_favicon_is_not_an_error() -> None:
    assert CHECK.is_favicon_message(Message("http://127.0.0.1:1/favicon.ico")) is True


def test_a_console_error_from_another_resource_stays_an_error() -> None:
    assert CHECK.is_favicon_message(Message("http://127.0.0.1:1/static/app.css")) is False
    assert CHECK.is_favicon_message(object()) is False


def test_no_default_step_clicks_any_submit_button() -> None:
    clicks = [
        action["click"]
        for step in CHECK.DEFAULT_STEPS
        for action in step.get("actions", [])
        if "click" in action
    ]
    assert clicks and all(selector == "button.button-apply" for selector in clicks)
