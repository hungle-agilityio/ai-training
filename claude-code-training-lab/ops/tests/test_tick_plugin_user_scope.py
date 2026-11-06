"""The tick also updates the plugin's user-scope install, which the build worktrees use (#246)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from ops import agent_tick
from ops.tests.test_agent_tick import NOW, FakeHost

MARKETPLACE_CMD = ["claude", "plugin", "marketplace", "update", "ai-training"]
UPDATE_CMD = ["claude", "plugin", "update", "agent-flow@ai-training"]
USER_UPDATE_CMD = [*UPDATE_CMD, "--scope", "user"]


@dataclass
class ScopeHost(FakeHost):
    """A fake host that answers the project and the user-scope update separately."""

    project_answer: tuple[int, str] = (0, "")
    user_answer: tuple[int, str] = (0, "")
    marketplace_answer: tuple[int, str] = (0, "")
    limits: list[tuple[list[str], int]] = field(default_factory=list)

    def run_limited(self, args: Sequence[str], seconds: int) -> tuple[int, str]:
        args = list(args)
        self.calls.append(args)
        self.limits.append((args, seconds))
        if args == MARKETPLACE_CMD:
            return self.marketplace_answer
        return self.user_answer if "--scope" in args else self.project_answer


def update(host: ScopeHost, tmp_path: Path) -> list[str]:
    tick = agent_tick.Tick(host, tmp_path, agent_tick.Settings(concurrency=1, ntfy_topic="t"))
    agent_tick.update_plugin(tick)
    return tick.log


def plugin_calls(host: ScopeHost) -> list[list[str]]:
    return [c for c in host.calls if c[:2] == ["claude", "plugin"]]


def test_the_user_scope_is_updated_third_with_a_60_second_limit(tmp_path: Path) -> None:
    host = ScopeHost(clock=NOW)
    update(host, tmp_path)
    assert plugin_calls(host) == [MARKETPLACE_CMD, UPDATE_CMD, USER_UPDATE_CMD]
    assert [seconds for _, seconds in host.limits] == [60, 60, 60]


def test_the_tick_never_enables_the_plugin(tmp_path: Path) -> None:
    host = ScopeHost(clock=NOW)
    update(host, tmp_path)
    assert not any("enable" in c or "install" in c for c in plugin_calls(host))


def test_a_failed_user_update_is_its_own_kind_and_sent_once_per_hour(tmp_path: Path) -> None:
    host = ScopeHost(clock=NOW, user_answer=(1, "network down"))
    log = update(host, tmp_path)
    assert any("plugin-update-user" in line and "network down" in line for line in log)
    host.clock = NOW + 600
    update(host, tmp_path)
    assert len(host.sent) == 1
    assert "plugin-update-user" in host.sent[0]


def test_no_user_update_after_the_project_update_failed(tmp_path: Path) -> None:
    host = ScopeHost(clock=NOW, project_answer=(1, "network down"))
    update(host, tmp_path)
    assert plugin_calls(host) == [MARKETPLACE_CMD, UPDATE_CMD]


def test_the_same_version_in_both_scopes_is_logged_once(tmp_path: Path) -> None:
    answer = (0, '✔ Plugin "agent-flow" updated from 1.0.1 to 1.0.2.')
    host = ScopeHost(clock=NOW, project_answer=answer, user_answer=answer)
    log = update(host, tmp_path)
    assert [line for line in log if "agent-flow@ai-training" in line] == [
        "plugin agent-flow@ai-training: version 1.0.2"
    ]


def test_different_versions_log_the_build_version_and_the_main_checkout(tmp_path: Path) -> None:
    host = ScopeHost(
        clock=NOW,
        project_answer=(0, "agent-flow is already at the latest (1.0.2)"),
        user_answer=(0, "agent-flow is already at the latest (1.0.0)"),
    )
    log = update(host, tmp_path)
    assert "plugin agent-flow@ai-training: version 1.0.0 (main checkout 1.0.2)" in log
