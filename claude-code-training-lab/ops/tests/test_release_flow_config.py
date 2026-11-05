"""ops/release.py takes its project values from the flow config (AC1, AC2).

Run: uv run pytest -q --no-cov ops/tests/test_release.py ops/tests/test_release_flow_config.py
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from ops import flow_config, release
from ops.tests.test_release import CLOSING_NOW, merge_pr, repo, run  # noqa: F401

SECOND = """
[project]
repo = "acme/shop"
owner = "acme-owner"
app_dir = "."
display_name = "Shop"
slug = "shop"

[loop]
state_dir = "{state}"
tmux_session = "shop-loop"
launchd_label = "com.shop.loop"
setup_command = ["uv", "sync", "--frozen"]
alone_words = ["migrations/"]

[checks]
commands = [["uv", "run", "pytest", "-q"]]
ci_workflow = "CI"
protected_test_dirs = ["tests"]

[release]
timezone = "Europe/Berlin"
deploy_line = ""
"""


@pytest.fixture
def second(tmp_path: Path) -> Iterator[None]:
    path = tmp_path / "shop.toml"
    path.write_text(SECOND.format(state=tmp_path / "shop-state"))
    release.configure(flow_config.load(path))
    yield
    release.configure(flow_config.load())


def test_release_has_no_project_literal() -> None:
    text = Path(release.__file__).read_text()
    assert "Asia/Ho_Chi_Minh" not in text
    assert "Render" not in text
    assert '"Checks"' not in text


def test_today_config_keeps_vietnam_zone_workflow_and_deploy_line() -> None:
    assert str(release.ZONE) == "Asia/Ho_Chi_Minh"
    assert release.CI_WORKFLOW == "Checks"
    assert release.DEPLOY_LINE == "Render deploys branch deploy after Checks pass."


def test_second_config_uses_its_zone_workflow_and_prints_no_deploy_line(
    repo: tuple[Path, Path],  # noqa: F811
    second: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "Add the filter")
    seen: list[list[str]] = []
    real_run = subprocess.run

    def spy(args: list[str], *rest: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "gh":
            seen.append(args)
            return subprocess.CompletedProcess(
                args, 0, '[{"status":"completed","conclusion":"success"}]', ""
            )
        return real_run(args, *rest, **kwargs)  # type: ignore[call-overload, no-any-return]

    monkeypatch.setattr(subprocess, "run", spy)
    assert release.main([], cwd=clone, now=CLOSING_NOW) == 0
    out = capsys.readouterr().out
    assert seen and seen[0][seen[0].index("--workflow") + 1] == "CI"
    assert "v2026.10.30" in out  # 18:30 UTC is 19:30 in Berlin, still the 30th
    assert "Render" not in out
    assert out.strip().splitlines()[-1].startswith("  #7")


def test_second_config_refusal_names_its_workflow(
    repo: tuple[Path, Path],  # noqa: F811
    second: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    assert run(clone, monkeypatch, checks=None) == 1
    assert "no CI run found" in capsys.readouterr().err
