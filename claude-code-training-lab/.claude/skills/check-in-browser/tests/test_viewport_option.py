"""Tests of the --viewport option of the browser check, without a browser.

Run: uv run pytest .claude/skills/check-in-browser/tests --no-cov -q
"""

from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]


def load() -> ModuleType:
    spec = util.spec_from_file_location("browser_check_viewport", SKILL / "browser_check.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load()


def test_viewport_parses_width_and_height() -> None:
    assert CHECK.parse_viewport("390x844") == {"width": 390, "height": 844}


@pytest.mark.parametrize("value", ["390", "390x", "x844", "abcxdef", "199x800", "390x4001", "-1x5"])
def test_viewport_refuses_a_bad_value(value: str) -> None:
    with pytest.raises(ValueError):
        CHECK.parse_viewport(value)


def test_without_the_option_the_size_stays_1280_by_800(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        raise RuntimeError("stop here")

    monkeypatch.setattr(CHECK, "run", fake_run)
    CHECK.main(["--out", str(tmp_path)])
    assert seen["viewport"] == {"width": 1280, "height": 800}


def test_the_option_reaches_the_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> dict[str, Any]:
        seen.update(kwargs)
        raise RuntimeError("stop here")

    monkeypatch.setattr(CHECK, "run", fake_run)
    CHECK.main(["--out", str(tmp_path), "--viewport", "390x844"])
    assert seen["viewport"] == {"width": 390, "height": 844}


def test_a_bad_option_stops_with_a_one_line_message(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    code = CHECK.main(["--out", str(tmp_path), "--viewport", "wide"])
    out = capsys.readouterr().out.strip()
    assert code != 0
    assert len(out.splitlines()) == 1
    assert "viewport" in out


def test_the_size_used_is_in_the_summary() -> None:
    summary = CHECK.summarize([], None, viewport={"width": 390, "height": 844})
    assert summary["viewport"] == {"width": 390, "height": 844}
