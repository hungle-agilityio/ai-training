"""Uptime probe of the live site: its state, its two messages, its place in the loop line."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ops import flow_config, live_check, uptime

OPS = Path(__file__).resolve().parents[1]
ZONE = ZoneInfo("Asia/Ho_Chi_Minh")
UP = uptime.Reply(200, "ok")
DOWN = uptime.Reply(503, "")
LOOP_LINE = (
    "caffeinate -i bash -c 'while true; do date; uv run python $REL/agent_tick.py; "
    "uv run python $REL/uptime.py || true; sleep 300; done'"
)
LIVE_TABLE = (
    '\n[live]\nurl = "https://shop.example"\nusername = "demo"\nwait_minutes = 15\n'
    "load_warn_seconds = 3\npersistent_database = false\n"
)
Probe = Callable[[uptime.Reply, str], int]


def at(clock: str) -> datetime:
    hour, minute = clock.split(":")
    return datetime(2026, 11, 12, int(hour), int(minute), tzinfo=ZONE)


def flow_file(tmp_path: Path, *, live: bool, zone: str | None = None) -> Path:
    """The repository's flow config, with or without a [live] table."""
    text = (OPS / "flow.toml").read_text(encoding="utf-8")
    head = text.split("\n[live]")[0].rstrip("\n") + "\n"
    if zone is not None:
        current = flow_config.load(OPS / "flow.toml").release_timezone
        head = head.replace(f'"{current}"', f'"{zone}"')
    path = tmp_path / "flow.toml"
    path.write_text(head + (LIVE_TABLE if live else ""), encoding="utf-8")
    return path


class Site:
    """A fake site, a fake clock and a fake phone around `uptime.main`."""

    def __init__(self, tmp_path: Path, *, live: bool = True, zone: str | None = None) -> None:
        self.home = tmp_path / "state"
        self.config_path = flow_file(tmp_path, live=live, zone=zone)
        self.sent: list[tuple[str, str]] = []
        self.requests: list[tuple[str, float]] = []

    @property
    def state_file(self) -> Path:
        return self.home / "uptime.json"

    def state(self) -> dict[str, object]:
        data: dict[str, object] = json.loads(self.state_file.read_text())
        return data

    def probe(self, reply: uptime.Reply, clock: str) -> int:
        def fetch(url: str, timeout: float) -> uptime.Reply:
            self.requests.append((url, timeout))
            return reply

        return uptime.main(
            [],
            fetch=fetch,
            now=lambda: at(clock),
            send=lambda message, priority: self.sent.append((message, priority)),
            environ={"FLOW_HOME": str(self.home)},
            config_path=self.config_path,
        )


@pytest.fixture
def site(tmp_path: Path) -> Site:
    return Site(tmp_path)


# M24 (AC1)


def test_a_good_answer_keeps_zero_failures_and_sends_nothing(site: Site) -> None:
    code = site.probe(UP, "08:55")

    assert code == 0
    assert site.state() == {"failures": 0, "down_since": None, "alerted": False}
    assert site.sent == []
    assert site.requests == [("https://shop.example/healthz/", 60.0)]


def test_a_200_answer_with_another_body_is_a_failure(site: Site) -> None:
    site.probe(uptime.Reply(200, "maintenance"), "09:00")
    site.probe(uptime.Reply(200, "maintenance"), "09:05")

    assert site.sent == [("ReviewRadar site is down since 09:00 (Vietnam time): HTTP 200", "high")]


def test_an_unreadable_state_file_counts_as_no_failure(site: Site) -> None:
    site.home.mkdir(parents=True)
    site.state_file.write_text("not json")

    site.probe(DOWN, "09:00")

    assert site.state()["failures"] == 1
    assert site.sent == []


# M25 (AC1)


def test_without_a_live_table_nothing_is_asked_or_written(tmp_path: Path) -> None:
    site = Site(tmp_path, live=False)

    code = site.probe(DOWN, "09:00")

    assert code == 0
    assert site.requests == []
    assert not site.state_file.exists()
    assert site.sent == []


# M26 (AC2)


def test_two_failures_in_a_row_send_one_down_message(site: Site) -> None:
    site.probe(UP, "08:55")
    site.probe(DOWN, "09:00")
    assert site.sent == []

    site.probe(DOWN, "09:05")

    assert site.sent == [("ReviewRadar site is down since 09:00 (Vietnam time): HTTP 503", "high")]
    state = site.state()
    assert state["failures"] == 2
    assert state["alerted"] is True
    assert datetime.fromisoformat(str(state["down_since"])) == at("09:00")


def test_a_third_failure_sends_nothing_more(site: Site) -> None:
    for clock in ("09:00", "09:05", "09:10"):
        site.probe(DOWN, clock)

    assert len(site.sent) == 1
    assert site.state()["failures"] == 3


def test_the_down_message_gives_the_reason_of_the_latest_failure(site: Site) -> None:
    site.probe(DOWN, "09:00")
    site.probe(uptime.Reply(None, "", uptime.TIMED_OUT), "09:05")

    assert site.sent == [
        ("ReviewRadar site is down since 09:00 (Vietnam time): timeout after 60s", "high")
    ]


# M27 (AC2)


def test_a_good_answer_after_the_alert_sends_one_back_message_and_resets(site: Site) -> None:
    site.probe(DOWN, "09:00")
    site.probe(DOWN, "09:05")

    site.probe(UP, "09:20")

    assert site.sent[1:] == [("ReviewRadar site is back after 20 minutes", "low")]
    assert site.state() == {"failures": 0, "down_since": None, "alerted": False}

    site.probe(UP, "09:25")
    assert len(site.sent) == 2


def test_one_failure_then_a_good_answer_sends_nothing(site: Site) -> None:
    site.probe(DOWN, "09:00")
    site.probe(UP, "09:05")

    assert site.sent == []
    assert site.state() == {"failures": 0, "down_since": None, "alerted": False}


def test_no_connection_is_named_in_the_down_message(site: Site) -> None:
    lost = uptime.Reply(None, "", uptime.NO_CONNECTION)
    site.probe(lost, "09:00")
    site.probe(lost, "09:05")

    assert site.sent == [
        ("ReviewRadar site is down since 09:00 (Vietnam time): no connection", "high")
    ]


def test_minutes_are_rounded_down_and_at_least_one(tmp_path: Path) -> None:
    config = flow_config.load(flow_file(tmp_path, live=True))
    since = at("09:00")

    late = since + timedelta(minutes=19, seconds=40)
    soon = since + timedelta(seconds=20)

    assert uptime.back_message(config, since, late) == "ReviewRadar site is back after 19 minutes"
    assert uptime.back_message(config, since, soon) == "ReviewRadar site is back after 1 minutes"


def test_another_zone_is_named_in_the_brackets(tmp_path: Path) -> None:
    site = Site(tmp_path, zone="Europe/Paris")
    site.probe(DOWN, "09:00")
    site.probe(DOWN, "09:05")

    assert site.sent == [("ReviewRadar site is down since 03:00 (Europe/Paris): HTTP 503", "high")]


# AC1, AC3: a message that cannot be sent, and no topic at all


def test_a_message_that_cannot_be_sent_still_exits_0_and_keeps_the_state(site: Site) -> None:
    def broken(message: str, priority: str) -> None:
        raise OSError("no network")

    site.probe(DOWN, "09:00")
    code = uptime.main(
        [],
        fetch=lambda url, timeout: DOWN,
        now=lambda: at("09:05"),
        send=broken,
        environ={"FLOW_HOME": str(site.home)},
        config_path=site.config_path,
    )

    assert code == 0
    assert site.state()["alerted"] is True


def test_with_neither_topic_nor_webhook_nothing_is_sent_and_the_state_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    site = Site(tmp_path)
    monkeypatch.setattr(live_check, "REPO_ENV", tmp_path / "no-agent.env")
    environ = {"FLOW_HOME": str(site.home)}
    for clock in ("09:00", "09:05"):
        code = uptime.main(
            [],
            fetch=lambda url, timeout: DOWN,
            now=lambda clock=clock: at(clock),  # type: ignore[misc]
            environ=environ,
            config_path=site.config_path,
        )
        assert code == 0

    assert site.state()["alerted"] is True


def test_messages_go_to_ntfy_and_slack_through_the_tick_senders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ops import agent_tick

    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        agent_tick.RealHost,
        "notify_priority",
        lambda self, topic, message, priority: calls.append(("ntfy", topic, message, priority)),
    )

    def slack(self: object, url: str, message: str) -> bool:
        calls.append(("slack", url, message))
        return True

    monkeypatch.setattr(agent_tick.RealHost, "slack", slack)
    monkeypatch.setattr(live_check, "REPO_ENV", tmp_path / "no-agent.env")
    site = Site(tmp_path)
    site.home.mkdir(parents=True)
    (site.home / "agent.env").write_text(
        "AGENT_CONCURRENCY=9\nNTFY_TOPIC=shop-topic\nSLACK_WEBHOOK_URL=https://hooks.example/x\n"
    )
    environ = {"FLOW_HOME": str(site.home)}
    for clock in ("09:00", "09:05"):
        uptime.main(
            [],
            fetch=lambda url, timeout: DOWN,
            now=lambda clock=clock: at(clock),  # type: ignore[misc]
            environ=environ,
            config_path=site.config_path,
        )

    text = "ReviewRadar site is down since 09:00 (Vietnam time): HTTP 503"
    assert calls == [
        ("ntfy", "shop-topic", text, "high"),
        ("slack", "https://hooks.example/x", text),
    ]


# M28 (AC4)


def test_start_loop_runs_the_probe_after_the_tick_exactly_once() -> None:
    script = (OPS / "start-loop.sh").read_text()

    assert script.count(LOOP_LINE) == 1


def test_the_script_names_no_other_project() -> None:
    text = (OPS / "uptime.py").read_text()

    assert "REVIEWRADAR_" not in text
    assert "onrender" not in text


# AC5


def test_readme_lists_both_messages_and_has_the_uptime_section() -> None:
    readme = (OPS / "README.md").read_text()

    assert "| `ReviewRadar site is down since <HH:MM> (Vietnam time): <reason>` | yes |" in readme
    assert "| `ReviewRadar site is back after <m> minutes` | no |" in readme
    assert "\n## Uptime\n" in readme
    assert "uptime.json" in readme.split("\n## Uptime\n")[1].split("\n## ")[0]
