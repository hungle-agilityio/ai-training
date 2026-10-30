"""Tests of --debug-off and of the spec's own options, without a browser.

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
    spec = util.spec_from_file_location("browser_check_debug", SKILL / "browser_check.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()


class FakeProcess:
    pass


def started(monkeypatch: pytest.MonkeyPatch, debug: bool) -> tuple[list[Any], list[Any]]:
    runs: list[Any] = []
    servers: list[Any] = []
    monkeypatch.setattr(CHECK.subprocess, "run", lambda args, **kw: runs.append((args, kw)))
    monkeypatch.setattr(
        CHECK.subprocess, "Popen", lambda args, **kw: servers.append((args, kw)) or FakeProcess()
    )
    CHECK.start_app(Path("."), Path("db.sqlite3"), 8123, debug=debug)
    return runs, servers


def test_the_app_starts_in_debug_mode_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    runs, servers = started(monkeypatch, debug=True)
    args, kwargs = servers[0]
    assert kwargs["env"]["DJANGO_DEBUG"] == "1"
    assert "--insecure" not in args
    assert all(kw["env"]["DJANGO_DEBUG"] == "1" for _, kw in runs)


def test_debug_off_starts_the_app_like_production(monkeypatch: pytest.MonkeyPatch) -> None:
    runs, servers = started(monkeypatch, debug=False)
    args, kwargs = servers[0]
    assert kwargs["env"]["DJANGO_DEBUG"] == "0"
    assert "--insecure" in args
    assert all(kw["env"]["DJANGO_DEBUG"] == "0" for _, kw in runs)


def capture_run(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        raise RuntimeError("stop here")

    monkeypatch.setattr(CHECK, "run", fake_run)
    return seen


def test_the_flag_reaches_the_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path), "--debug-off"])
    assert seen["debug"] is False


def test_without_the_flag_debug_stays_on(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path)])
    assert seen["debug"] is True


def test_a_spec_can_set_debug_and_viewport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spec = tmp_path / "spec.json"
    steps = [{"name": "not-found", "goto": "/missing/"}]
    spec.write_text(json.dumps({"debug": False, "viewport": "390x844", "steps": steps}))
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path / "out"), "--spec", str(spec)])
    assert seen["debug"] is False
    assert seen["viewport"] == {"width": 390, "height": 844}


def test_the_command_line_wins_over_the_spec(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"viewport": "390x844", "steps": [{"name": "a", "goto": "/"}]}))
    seen = capture_run(monkeypatch)
    CHECK.main(["--out", str(tmp_path / "out"), "--spec", str(spec), "--viewport", "800x600"])
    assert seen["viewport"] == {"width": 800, "height": 600}


def test_a_spec_with_a_wrong_debug_value_stops_with_one_line(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"debug": "no", "steps": [{"name": "a", "goto": "/"}]}))
    code = CHECK.main(["--out", str(tmp_path / "out"), "--spec", str(spec)])
    out = capsys.readouterr().out.strip()
    assert code != 0
    assert len(out.splitlines()) == 1
    assert "debug" in out


def test_the_debug_mode_is_in_the_summary() -> None:
    assert CHECK.summarize([], None, debug=False)["debug"] is False
    assert CHECK.summarize([], None)["debug"] is True


def record(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "http_status": 404,
        "network_failures": ["404 http://127.0.0.1:1/missing/"],
        "console_errors": [
            "Failed to load resource: the server responded with a status of 404 (Not Found)"
        ],
        "problems": [],
    }
    return {**base, **over}


def test_an_expected_status_is_not_a_failure() -> None:
    step = {"name": "nf", "goto": "/missing/", "status": 404}
    result = CHECK.apply_expected_status(record(), step, "http://127.0.0.1:1")
    assert result["network_failures"] == []
    assert result["console_errors"] == []
    assert result["problems"] == []


def test_another_status_than_expected_is_a_problem() -> None:
    step = {"name": "nf", "goto": "/missing/", "status": 404}
    result = CHECK.apply_expected_status(
        record(http_status=500, network_failures=["500 http://127.0.0.1:1/missing/"]),
        step,
        "http://127.0.0.1:1",
    )
    assert result["problems"] == ["expected status 404, got 500"]
    assert result["network_failures"] == ["500 http://127.0.0.1:1/missing/"]


def test_without_an_expected_status_a_404_stays_a_failure() -> None:
    step = {"name": "nf", "goto": "/missing/"}
    result = CHECK.apply_expected_status(record(), step, "http://127.0.0.1:1")
    assert result["network_failures"] == ["404 http://127.0.0.1:1/missing/"]
    assert len(result["console_errors"]) == 1


def test_other_failures_on_the_page_still_count() -> None:
    step = {"name": "nf", "goto": "/missing/", "status": 404}
    failures = ["404 http://127.0.0.1:1/missing/", "404 http://127.0.0.1:1/static/app.css"]
    errors = [
        "Failed to load resource: the server responded with a status of 404 (Not Found)",
        "Failed to load resource: the server responded with a status of 404 (Not Found)",
    ]
    result = CHECK.apply_expected_status(
        record(network_failures=failures, console_errors=errors), step, "http://127.0.0.1:1"
    )
    assert result["network_failures"] == ["404 http://127.0.0.1:1/static/app.css"]
    assert len(result["console_errors"]) == 1
