"""#344: a cancelled CI run is neither green nor red. Run: pytest ops/tests"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import issue, started
from ops.tests.test_tick_guards import GREEN, RED, ChecksHost, files
from ops.tests.test_tick_merge import loop_pr

CANCELLED = {"conclusion": "cancelled", "headSha": "d" * 40, "url": "https://ci/3"}
SKIPPED = {"conclusion": "skipped", "headSha": "e" * 40, "url": "https://ci/4"}
ISSUE_RUN = "Use the work-queue skill for issue #1 only."
PR_RUN = "Use the work-queue skill for pull request #20 only."


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=3\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def ready_issue() -> dict[str, Any]:
    return issue(1, "agent:ready", body=files("a.py"))


def red_messages(host: ChecksHost) -> list[str]:
    return [m for m in host.sent if "main is red" in m]


# AC1: main


def test_main_reads_up_to_ten_completed_runs(home: Path) -> None:
    host = ChecksHost(main_runs=GREEN)
    agent_tick.tick_once(host, home)
    call = next(c for c in host.calls if c[:3] == ["gh", "run", "list"])
    assert call[call.index("--limit") + 1] == "10"
    assert call[call.index("--status") + 1] == "completed"


@pytest.mark.parametrize("ignored", [CANCELLED, SKIPPED])
def test_a_cancelled_run_before_a_green_one_is_green(home: Path, ignored: dict[str, str]) -> None:
    host = ChecksHost(main_runs=[ignored, *GREEN], issues=[ready_issue()])
    agent_tick.tick_once(host, home)
    assert started(host) == [ISSUE_RUN]
    assert red_messages(host) == []


def test_a_cancelled_run_before_a_failed_one_is_red(home: Path) -> None:
    host = ChecksHost(main_runs=[CANCELLED, *RED], issues=[ready_issue()])
    agent_tick.tick_once(host, home)
    assert host.spawned == []
    assert red_messages(host) == ["rr-test: main is red at b1c2d3e: https://ci/2"]


def test_a_green_run_after_an_old_failure_is_green(home: Path) -> None:
    host = ChecksHost(main_runs=[*GREEN, *RED], issues=[ready_issue()])
    agent_tick.tick_once(host, home)
    assert started(host) == [ISSUE_RUN]


def test_only_cancelled_or_skipped_runs_count_as_green(home: Path) -> None:
    host = ChecksHost(main_runs=[CANCELLED, SKIPPED, CANCELLED], issues=[ready_issue()])
    agent_tick.tick_once(host, home)
    assert started(host) == [ISSUE_RUN]
    assert red_messages(host) == []


def test_no_runs_still_counts_as_green_with_the_unreadable_log_line(home: Path) -> None:
    host = ChecksHost(main_runs=[], issues=[ready_issue()])
    log = agent_tick.tick_once(host, home)
    assert started(host) == [ISSUE_RUN]
    assert "main checks could not be read" in "\n".join(log)


# AC2: pull requests


def test_a_cancelled_check_with_ready_for_review_does_not_need_a_run(home: Path) -> None:
    checks = [{"status": "COMPLETED", "conclusion": "CANCELLED"}]
    host = ChecksHost(prs=[loop_pr(checks=checks)])
    agent_tick.tick_once(host, home)
    assert PR_RUN not in started(host)


@pytest.mark.parametrize(
    "conclusion", ["FAILURE", "ERROR", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE"]
)
def test_a_real_failure_with_ready_for_review_still_needs_a_run(
    home: Path, conclusion: str
) -> None:
    checks = [{"status": "COMPLETED", "conclusion": conclusion}]
    host = ChecksHost(prs=[loop_pr(checks=checks)])
    agent_tick.tick_once(host, home)
    assert started(host) == [PR_RUN]


# AC3: a real failure behaves as before


def test_a_real_failure_keeps_the_message_the_log_line_and_the_record(home: Path) -> None:
    host = ChecksHost(main_runs=[*RED], issues=[ready_issue()])
    log = agent_tick.tick_once(host, home)
    agent_tick.tick_once(host, home)
    assert red_messages(host) == ["rr-test: main is red at b1c2d3e: https://ci/2"]
    assert "main is red at b1c2d3e; no new issue starts" in "\n".join(log)
    assert (home / "last-red").read_text() == "b1c2d3e"
