"""The pull request list stays under GitHub's GraphQL node limit (after #164). Run: pytest ops"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, pull

HEAVY = ("commits", "comments", "statusCheckRollup")


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def lists(host: FakeHost) -> list[list[str]]:
    return host.gh_calls("pr", "list")


def option(call: list[str], name: str) -> str:
    return call[call.index(name) + 1]


def test_heavy_fields_are_read_only_for_open_pull_requests(home: Path) -> None:
    host = FakeHost()
    agent_tick.tick_once(host, home)
    for call in lists(host):
        fields = option(call, "--json")
        if any(name in fields for name in HEAVY):
            assert option(call, "--state") == "open"


def test_light_list_reads_one_hundred_and_heavy_list_forty(home: Path) -> None:
    host = FakeHost()
    agent_tick.tick_once(host, home)
    limits = {option(c, "--state"): option(c, "--limit") for c in lists(host)}
    assert limits == {"all": "100", "open": "40"}


def test_open_and_ended_pull_requests_are_both_seen_once(home: Path) -> None:
    prs = [pull(20, "pr:ready-for-review", closes=5),
           pull(21, state="MERGED", closes=6)]
    host = FakeHost(prs=prs)
    tick = agent_tick.Tick(host, home, agent_tick.read_settings(home / "agent.env"))
    found = agent_tick.loop_pull_requests(tick)
    assert sorted((pr["number"], pr["state"]) for pr in found) == [(20, "OPEN"), (21, "MERGED")]
