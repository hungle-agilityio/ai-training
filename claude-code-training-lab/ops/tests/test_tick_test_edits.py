"""The tick passes the existing tests an issue names to the build (FLOW_TEST_EDITS)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import agent_tick
from ops.tests.test_agent_tick import issue, pull
from ops.tests.test_build_artifact_tool import RESULT, WITH, Child, Fake
from ops.tests.test_tick_hardening import GitHost

PREFIX = agent_tick.LAB_PREFIX
BODY = (
    "## Summary\n\nx\n\n## Files likely touched\n\n"
    f"- `{PREFIX}reviews/management/commands/seed_demo_data.py`\n"
    f"- `{PREFIX}reviews/tests/integration/test_seed_demo_replies.py`\n\n"
    "## Existing tests that change\n\n"
    f"- `{PREFIX}reviews/tests/integration/test_seed_demo_replies.py::test_a`: 9.\n"
    f"- `{PREFIX}reviews/tests/integration/test_seed_demo_replies.py::test_b`: 9.\n"
    f"- `{PREFIX}reviews/tests/unit/test_other.py`\n\n"
    "## How to check it when built\n\n1. x\n"
)
LISTED = "reviews/tests/integration/test_seed_demo_replies.py\nreviews/tests/unit/test_other.py\n"


@pytest.fixture
def home(tmp_path: Path) -> Path:
    (tmp_path / "agent.env").write_text("AGENT_CONCURRENCY=2\nNTFY_TOPIC=rr-test\n")
    return tmp_path


def test_the_section_gives_each_file_once_without_prefix_or_test_name() -> None:
    assert agent_tick.test_edits_of(BODY) == (
        "reviews/tests/integration/test_seed_demo_replies.py",
        "reviews/tests/unit/test_other.py",
    )


def test_a_body_without_the_section_gives_nothing() -> None:
    assert agent_tick.test_edits_of("## Files likely touched\n\n- `reviews/x.py`\n") == ()


def test_an_issue_build_writes_the_test_edits_file(home: Path) -> None:
    host = GitHost(issues=[issue(290, "agent:ready", body=BODY)])
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "issue-290" / "test-edits").read_text() == LISTED


def test_an_issue_without_the_section_writes_no_file(home: Path) -> None:
    body = "## Files likely touched\n\n- `reviews/x.py`\n"
    host = GitHost(issues=[issue(291, "agent:ready", body=body)])
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "issue-291").is_dir()
    assert not (home / "runs" / "issue-291" / "test-edits").exists()


def test_a_pull_request_round_uses_its_issue(home: Path) -> None:
    host = GitHost(prs=[pull(300, closes=290)], issues=[issue(290, "agent:review", body=BODY)])
    agent_tick.tick_once(host, home)
    assert (home / "runs" / "pr-300" / "test-edits").read_text() == LISTED


def test_the_build_gets_the_variable_from_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = tmp_path / "runs" / "issue-290"
    run.mkdir(parents=True)
    (run / "test-edits").write_text(LISTED)
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_start(run, tmp_path, "p", 1, 10**12)
    assert fake.starts[0][1]["env"]["FLOW_TEST_EDITS"] == LISTED.strip()


def test_without_the_file_the_variable_is_not_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FLOW_TEST_EDITS", "reviews/tests/unit/test_leak.py")
    run = tmp_path / "runs" / "issue-291"
    run.mkdir(parents=True)
    fake = Fake(monkeypatch, [Child([WITH, RESULT])])
    agent_tick.run_start(run, tmp_path, "p", 1, 10**12)
    assert "FLOW_TEST_EDITS" not in fake.starts[0][1]["env"]
