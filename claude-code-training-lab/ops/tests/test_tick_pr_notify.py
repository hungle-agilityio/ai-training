"""The phone hears when the loop opens or updates a pull request. Run: uv run pytest ops/tests"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import FakeHost, comment, issue, pull

REPORT = "https://claude.ai/artifact/AbC123"


def loop_pr(number: int, *labels: str, closes: int, state: str = "OPEN",
            report: bool = True) -> dict[str, Any]:
    pr = pull(number, *labels, state=state, closes=closes)
    if report:
        pr["body"] += f"\nVerify report: {REPORT}"
    return pr


def ended(home: Path, key: str, outcome: str | None) -> None:
    run = home / "runs" / key
    run.mkdir(parents=True)
    (run / "pid").write_text("99")
    if outcome is not None:
        (run / "exit").write_text(outcome)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def pr_messages(host: FakeHost) -> list[str]:
    return [m for m in host.sent if "ReviewRadar PR #" in m]


@pytest.mark.parametrize("outcome", ["0", "1", "timeout", None])
def test_issue_build_with_an_open_pull_request_sends_opened(
    home: Path, outcome: str | None
) -> None:
    host = FakeHost(prs=[loop_pr(40, "pr:ready-for-review", closes=7)],
                    issues=[issue(7, "agent:review")])
    ended(home, "issue-7", outcome)
    agent_tick.tick_once(host, home)
    assert pr_messages(host) == [
        "rr-test: ReviewRadar PR #40 opened for #7 (pr:ready-for-review)\n"
        "https://github.com/hungle-agilityio/ai-training/pull/40\n"
        f"Report: {REPORT}"
    ]


def test_pull_request_build_that_ends_normally_sends_updated(home: Path) -> None:
    host = FakeHost(prs=[loop_pr(40, "pr:changes-requested", closes=7)])
    ended(home, "pr-40", "0")
    agent_tick.tick_once(host, home)
    assert pr_messages(host) == [
        "rr-test: ReviewRadar PR #40 updated for #7 (pr:changes-requested)\n"
        "https://github.com/hungle-agilityio/ai-training/pull/40\n"
        f"Report: {REPORT}"
    ]


def test_tidying_a_merged_pull_request_sends_no_pull_request_message(home: Path) -> None:
    host = FakeHost(prs=[loop_pr(40, closes=7, state="MERGED")])
    ended(home, "pr-40", "0")
    agent_tick.tick_once(host, home)
    assert pr_messages(host) == []


def test_issue_build_without_a_pull_request_keeps_only_the_failed_message(home: Path) -> None:
    host = FakeHost(issues=[issue(7, "agent:running")])
    ended(home, "issue-7", "1")
    agent_tick.tick_once(host, home)
    assert pr_messages(host) == []
    assert any("build for issue #7 failed" in m for m in host.sent)


def test_missing_report_link_and_status_label_are_named(home: Path) -> None:
    host = FakeHost(prs=[loop_pr(40, closes=7, report=False)], issues=[issue(7, "agent:review")])
    ended(home, "issue-7", "0")
    agent_tick.tick_once(host, home)
    message = pr_messages(host)[0]
    assert "(no status label yet)" in message
    assert message.endswith("Report: no link in the pull request")


def test_the_newest_open_pull_request_is_named(home: Path) -> None:
    host = FakeHost(prs=[loop_pr(40, closes=7, state="CLOSED"), loop_pr(41, closes=7),
                         loop_pr(43, "pr:ready-for-review", closes=7)],
                    issues=[issue(7, "agent:review")])
    ended(home, "issue-7", "0")
    agent_tick.tick_once(host, home)
    assert len(pr_messages(host)) == 1
    assert "PR #43 opened for #7" in pr_messages(host)[0]


def test_a_later_tick_does_not_send_it_again(home: Path) -> None:
    host = FakeHost(prs=[loop_pr(40, "pr:ready-for-review", closes=7)],
                    issues=[issue(7, "agent:review")])
    ended(home, "issue-7", "0")
    agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert len(pr_messages(host)) == 1


def test_no_topic_sends_nothing(tmp_path: Path) -> None:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=1\n")
    host = FakeHost(prs=[loop_pr(40, "pr:ready-for-review", closes=7)],
                    issues=[issue(7, "agent:review")])
    ended(tmp_path, "issue-7", "0")
    agent_tick.tick_once(host, tmp_path)
    assert host.sent == []


def test_no_new_gh_call_is_made_for_the_message(home: Path) -> None:
    host = FakeHost(prs=[loop_pr(40, "pr:changes-requested", closes=7)],
                    issue_comments={7: [comment("hi")]})
    ended(home, "pr-40", "0")
    agent_tick.tick_once(host, home)
    assert host.gh_calls("pr", "view") == []
