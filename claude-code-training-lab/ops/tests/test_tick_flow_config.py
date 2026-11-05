"""The tick and the loop scripts take the project values from the flow config (AC1 to AC7).

No network, no `claude`: the host and Popen are faked.
Run: uv run pytest ops/tests --no-cov
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from ops import agent_tick, flow_config
from ops.tests.test_agent_tick import FakeHost, issue
from ops.tests.test_build_artifact_tool import RESULT, WITH, Child, Fake

OPS = Path(agent_tick.__file__).parent
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
timezone = "UTC"
deploy_line = "Deploy runs after CI."
"""


@pytest.fixture
def second(tmp_path: Path) -> Iterator[flow_config.FlowConfig]:
    path = tmp_path / "shop.toml"
    path.write_text(SECOND.format(state=tmp_path / "shop-state"))
    config = flow_config.load(path)
    agent_tick.configure(config)
    yield config
    agent_tick.configure(flow_config.load())


# AC1


def test_the_tick_has_no_project_literal() -> None:
    text = (OPS / "agent_tick.py").read_text()
    pattern = r"hungle-agilityio|claude-code-training-lab|ReviewRadar|\.reviewradar|\"Checks\""
    assert re.findall(pattern, text) == []


# AC2


def test_app_dir_dot_means_worktree_root_and_empty_prefix(
    second: flow_config.FlowConfig, tmp_path: Path
) -> None:
    assert agent_tick.LAB_PREFIX == ""
    assert agent_tick.files_of("## Files likely touched\n\n- `app/x.py`\n") == {"app/x.py"}
    home = tmp_path / "home"
    home.mkdir()
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=t\n")
    host = FakeHost(issues=[issue(1, "agent:ready")], labeller={1: "acme-owner"})
    agent_tick.tick_once(host, home)
    worktree = home / "worktrees" / "issue-1"
    assert host.spawned[0][2:5] == ["run", str(home / "runs" / "issue-1"), str(worktree)]


# AC3


def test_state_folder_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, second: flow_config.FlowConfig
) -> None:
    monkeypatch.delenv("FLOW_HOME", raising=False)
    monkeypatch.delenv("REVIEWRADAR_HOME", raising=False)
    seen: list[Path] = []

    def record(host: object, home: Path) -> list[str]:
        seen.append(home)
        return []

    monkeypatch.setattr(agent_tick, "tick_once", record)
    monkeypatch.setattr(agent_tick, "RealHost", lambda: object())
    agent_tick.main([])
    monkeypatch.setenv("REVIEWRADAR_HOME", str(tmp_path / "old"))
    agent_tick.main([])
    monkeypatch.setenv("FLOW_HOME", str(tmp_path / "flow"))
    agent_tick.main([])
    assert seen == [tmp_path / "shop-state", tmp_path / "old", tmp_path / "flow"]


# AC4


def test_a_build_has_both_loop_variables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = tmp_path / "runs" / "issue-1"
    run.mkdir(parents=True)
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_start(run, tmp_path, "p", 1, 10**12)
    env = fake.starts[0][1]["env"]
    assert env["FLOW_LOOP"] == "1"
    assert env["REVIEWRADAR_LOOP"] == "1"


# AC5


@pytest.mark.parametrize("script", ["start-loop.sh", "install-launchd.sh"])
def test_scripts_read_the_config_not_literals(script: str) -> None:
    text = (OPS / script).read_text()
    assert "flow_value " in text
    assert "rr-loop" not in text.replace("`rr-loop`", "")
    assert "com.reviewradar" not in text
    assert '.reviewradar"' not in text


def test_scripts_ask_flow_config_for_the_second_project(tmp_path: Path) -> None:
    path = tmp_path / "shop.toml"
    path.write_text(SECOND.format(state=tmp_path / "s"))
    command = (
        f'source "{OPS / "flow-value.sh"}"; flow_value loop.tmux_session; flow_value loop.state_dir'
    )
    for path_env in ("/usr/bin:/bin", f"{Path(sys.executable).parent}:/usr/bin:/bin"):
        env = {"FLOW_CONFIG": str(path), "PATH": path_env, "HOME": str(tmp_path)}
        out = subprocess.run(
            ["/bin/bash", "-c", command], capture_output=True, text=True, env=env, check=True
        )
        assert out.stdout.split() == ["shop-loop", str(tmp_path / "s")]


def test_example_and_readme_name_the_state_folder_from_the_config() -> None:
    assert "state folder from `ops/flow.toml`" in (OPS / "README.md").read_text()
    assert "state folder from ops/flow.toml" in (OPS / "agent.env.example").read_text()


# AC7


def test_second_project_messages_calls_and_approvals(
    second: flow_config.FlowConfig, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=t\n")
    ready = issue(1, "agent:ready") | {"title": "Add a filter"}
    host = FakeHost(issues=[ready], labeller={1: "acme-owner"})
    cwds: list[Path | None] = []
    original = host.run

    def run(args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
        if list(args) == ["uv", "sync", "--frozen"]:
            cwds.append(cwd)
        return original(args, cwd)

    host.run = run  # type: ignore[method-assign]
    agent_tick.tick_once(host, home)
    assert "t: Shop started #1: Add a filter" in host.sent
    assert any(m.startswith("t: Shop ") for m in host.sent)
    assert not any("ReviewRadar" in m for m in host.sent)
    assert [
        "gh",
        "issue",
        "edit",
        "1",
        "--add-label",
        "agent:running",
        "--remove-label",
        "agent:ready",
        "--repo",
        "acme/shop",
    ] in host.calls
    assert cwds == [home / "worktrees" / "issue-1"]
    owner = {"author": {"login": "acme-owner"}, "body": "ok", "createdAt": "2026-10-21T00:00:00Z"}
    other = {"author": {"login": "hungle-agilityio"}, "body": "ok", "createdAt": owner["createdAt"]}
    assert agent_tick.remark_of("conversation", owner) is not None
    assert agent_tick.remark_of("conversation", other) is None
