"""The tick brings the agent-flow plugin up to date first (spec flow-plugin AC21 to AC23)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from ops import agent_tick, flow_config
from ops.tests.test_agent_tick import NOW, FakeHost

MARKETPLACE_CMD = ["claude", "plugin", "marketplace", "update", "ai-training"]
UPDATE_CMD = ["claude", "plugin", "update", "agent-flow@ai-training"]
USER_UPDATE_CMD = [*UPDATE_CMD, "--scope", "user"]


@dataclass
class PluginHost(FakeHost):
    """A fake host whose `claude plugin` commands answer from `plugin_answers`."""

    plugin_answers: dict[str, tuple[int, str]] = field(default_factory=dict)
    limits: list[tuple[list[str], int]] = field(default_factory=list)

    def run_limited(self, args: Sequence[str], seconds: int) -> tuple[int, str]:
        args = list(args)
        self.calls.append(args)
        self.limits.append((args, seconds))
        return self.plugin_answers.get(args[2], (0, ""))


def tick(host: PluginHost, tmp_path: Path) -> list[str]:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return agent_tick.tick_once(host, tmp_path)


def plugin_calls(host: PluginHost) -> list[list[str]]:
    return [c for c in host.calls if c[:2] == ["claude", "plugin"]]


def test_plugin_commands_run_first_with_a_60_second_limit(tmp_path: Path) -> None:
    host = PluginHost(clock=NOW)
    tick(host, tmp_path)
    assert plugin_calls(host) == [MARKETPLACE_CMD, UPDATE_CMD, USER_UPDATE_CMD]
    assert [seconds for _, seconds in host.limits] == [60, 60, 60]
    first_other = next(i for i, c in enumerate(host.calls) if c[0] != "claude")
    assert host.calls.index(MARKETPLACE_CMD) < first_other


def test_the_installed_version_is_logged_once_per_tick(tmp_path: Path) -> None:
    host = PluginHost(
        plugin_answers={
            "update": (0, '✔ Plugin "agent-flow" updated from 1.0.0 to 1.0.1 for scope user.')
        }
    )
    log = tick(host, tmp_path)
    lines = [line for line in log if "agent-flow@ai-training" in line]
    assert lines == ["plugin agent-flow@ai-training: version 1.0.1"]


def test_an_unchanged_plugin_logs_the_version_it_reports(tmp_path: Path) -> None:
    host = PluginHost(plugin_answers={"update": (0, "agent-flow is already at the latest (1.2.3)")})
    log = tick(host, tmp_path)
    assert "plugin agent-flow@ai-training: version 1.2.3" in log


@pytest.mark.parametrize(
    ("failing", "kind", "commands"),
    [("marketplace", "marketplace-update", 3), ("update", "plugin-update", 2)],
)
def test_a_failed_command_is_logged_notified_and_the_tick_goes_on(
    tmp_path: Path, failing: str, kind: str, commands: int
) -> None:
    host = PluginHost(plugin_answers={failing: (1, "network down")})
    log = tick(host, tmp_path)
    assert any(kind in line and "network down" in line for line in log)
    assert len(plugin_calls(host)) == commands
    assert any(c[0] == "gh" for c in host.calls)  # the tick went on past the update


def test_a_timeout_is_a_failure_with_its_own_text(tmp_path: Path) -> None:
    host = PluginHost(plugin_answers={"marketplace": (124, "timed out after 60 seconds")})
    log = tick(host, tmp_path)
    assert any("marketplace-update" in line and "timed out" in line for line in log)


def test_one_message_per_failure_kind_per_hour(tmp_path: Path) -> None:
    host = PluginHost(plugin_answers={"marketplace": (1, "down"), "update": (1, "down")})
    settings = agent_tick.Settings(concurrency=1, ntfy_topic="t")
    for offset in (0, 600, 1200):
        host.clock = NOW + offset
        agent_tick.update_plugin(agent_tick.Tick(host, tmp_path, settings))
    assert len(host.sent) == 2  # one per kind, not one per tick
    assert any("marketplace-update" in m for m in host.sent)
    assert any("plugin-update" in m for m in host.sent)

    host.clock = NOW + 3601
    agent_tick.update_plugin(agent_tick.Tick(host, tmp_path, settings))
    assert len(host.sent) == 4


def test_a_success_sends_nothing(tmp_path: Path) -> None:
    host = PluginHost()
    agent_tick.update_plugin(agent_tick.Tick(host, tmp_path, agent_tick.Settings(1, "t")))
    assert host.sent == []


def test_the_build_is_told_the_full_skill_name() -> None:
    assert "agent-flow:work-queue" in agent_tick.HINT


@pytest.mark.parametrize("key", ["id", "marketplace"])
def test_a_missing_plugin_key_stops_the_tick_with_its_name(tmp_path: Path, key: str) -> None:
    text = (
        (Path(flow_config.DEFAULT_PATH))
        .read_text()
        .replace(
            f'{key} = "agent-flow@ai-training"' if key == "id" else 'marketplace = "ai-training"',
            "",
        )
    )
    path = tmp_path / "flow.toml"
    path.write_text(text)
    with pytest.raises(flow_config.FlowConfigError, match=f"missing plugin.{key}"):
        flow_config.load(path)


def test_a_file_without_a_plugin_table_stops_the_tick_with_the_key(tmp_path: Path) -> None:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\n")
    text = Path(flow_config.DEFAULT_PATH).read_text().split("[plugin]")[0]
    path = tmp_path / "flow.toml"
    path.write_text(text)
    agent_tick.configure(flow_config.load(path))
    try:
        with pytest.raises(flow_config.FlowConfigError, match="missing plugin.id"):
            agent_tick.tick_once(PluginHost(), tmp_path)
    finally:
        agent_tick.configure(flow_config.load())


def test_the_committed_file_names_the_plugin_and_the_marketplace() -> None:
    config = flow_config.load()
    assert config.plugin_id == "agent-flow@ai-training"
    assert config.plugin_marketplace == "ai-training"
